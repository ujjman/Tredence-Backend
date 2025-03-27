from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

from cad_executor import CadQueryRunner
from llm_handler import CADCopilot, CADResponse
from fastapi.middleware.cors import CORSMiddleware
from databricks_uploader import upload_to_databricks


import time
import csv
from datetime import datetime

app = FastAPI()


# Make sure to add this BEFORE any route definitions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # This is important for file downloads:
    expose_headers=["Content-Disposition"]
)

runner = CadQueryRunner()
copilot = CADCopilot()

class DesignRequest(BaseModel):
    prompt: str
    parameters: dict = None

@app.post("/generate")
async def generate_design(request: DesignRequest):
    start_time = time.time()
    try:
        cad_response = copilot.generate_code(request.prompt)
        model_paths = runner.generate_model(cad_response.code)
        duration = round((time.time() - start_time) * 1000)  # in ms

        step_file = model_paths['step_path']
        stl_file = model_paths['stl_path']
        upload_to_databricks(step_file, f"dbfs:/cad_files/{os.path.basename(step_file)}")
        upload_to_databricks(stl_file, f"dbfs:/cad_files/{os.path.basename(stl_file)}")

        # Log to CSV
        log_data = {
            "Timestamp": datetime.utcnow().isoformat(),
            "UserID": "anonymous",  # replace with actual ID if available
            "Prompt": request.prompt,
            "GPT_Response": cad_response.code[:1000],  # truncate if needed
            "Success": True,
            "Error_Type": "",
            "Response_Time_ms": duration,
            "Retry_Count": 0  # implement retries later if needed
        }

    except Exception as e:
        duration = round((time.time() - start_time) * 1000)
        log_data = {
            "Timestamp": datetime.utcnow().isoformat(),
            "UserID": "anonymous",
            "Prompt": request.prompt,
            "GPT_Response": "",
            "Success": False,
            "Error_Type": str(e),
            "Response_Time_ms": duration,
            "Retry_Count": 0
        }

    finally:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, "prompt_logs.csv")

        with open(log_file_path, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=log_data.keys())
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(log_data)

    if not log_data["Success"]:
        raise HTTPException(500, detail=log_data["Error_Type"])

    return {
        **cad_response.dict(),
        "model_url": f"/download-model/{os.path.basename(model_paths['step_path'])}",
        "view_url": f"/download-model/{os.path.basename(model_paths['stl_path'])}"
    }


def replace_parameters_in_code(parameters: dict) -> str:
    """
    Stub: Replace with actual code generation logic.
    This example assumes box parameters: width, height, depth
    """
    try:
        width = parameters.get("width", {}).get("value", 1)
        height = parameters.get("height", {}).get("value", 1)
        depth = parameters.get("depth", {}).get("value", 1)
        code = f"""
import cadquery as cq
result = cq.Workplane("XY").box({width}, {height}, {depth})
"""
        return code.strip()
    except Exception as e:
        raise ValueError(f"Invalid parameters format: {e}")


@app.get("/download-model/{filename}")
async def download_model(filename: str):
    model_path = f"model_cache/{filename}"
    print(f"Attempting to serve file: {model_path}")
    print(f"File exists: {os.path.exists(model_path)}")
    
    if not os.path.exists(model_path):
        raise HTTPException(404, "Model file not found")
    
    return FileResponse(model_path, media_type="application/octet-stream", filename=filename)