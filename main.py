from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

from cad_executor import CadQueryRunner
from llm_handler import CADCopilot, CADResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


# Make sure to add this BEFORE any route definitions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
    try:
        # Generate code and model (your existing code)
        cad_response = copilot.generate_code(request.prompt)
        model_paths = runner.generate_model(cad_response.code)
        
        # Verify files exist before returning URLs
        if not os.path.exists(model_paths["step_path"]) or not os.path.exists(model_paths["stl_path"]):
            raise HTTPException(500, "Model generation failed")
            
        return {
            **cad_response.dict(),
            "model_url": f"/download-model/{os.path.basename(model_paths['step_path'])}",
            "view_url": f"/download-model/{os.path.basename(model_paths['stl_path'])}"
        }
        
    except Exception as e:
        raise HTTPException(500, detail=str(e))


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