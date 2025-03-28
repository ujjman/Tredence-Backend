from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

from cad_executor import CadQueryRunner
from llm_handler import CADCopilot, CADResponse
from fastapi.middleware.cors import CORSMiddleware
import time

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


@app.get("/health")
async def health_check():
    """Health check endpoint for frontend status indicator"""
    try:
        # You can add more checks here as needed
        # e.g., database connection, external services, etc.
        return {"status": "healthy", "timestamp": str(datetime.now())}
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    

# Add this to your main.py file to ensure each parameter update generates a unique file

@app.post("/update-parameters")
async def update_parameters(request: DesignRequest):
    try:
        # Get the last generated code from the prompt
        # You should modify this to either:
        # 1. Store the last code in a database/cache with the prompt as key
        # 2. Get the code from the parameters and prompt
        
        # For now, we'll assume we can generate new code from the prompt + parameters
        cad_response = copilot.generate_code(request.prompt)
        
        # Apply parameter changes to the code
        modified_code = apply_parameters_to_code(cad_response.code, request.parameters)
        
        # Generate the model with the updated code
        model_paths = runner.generate_model(modified_code)
        
        # Verify files exist
        if not os.path.exists(model_paths["step_path"]) or not os.path.exists(model_paths["stl_path"]):
            raise HTTPException(500, "Model generation failed")
            
        # Use timestamp to ensure unique URLs that bypass caching
        timestamp = int(time.time())
        
        return {
            "code": modified_code,
            "parameters": request.parameters,
            "model_url": f"/download-model/{os.path.basename(model_paths['step_path'])}?t={timestamp}",
            "view_url": f"/download-model/{os.path.basename(model_paths['stl_path'])}?t={timestamp}"
        }
        
    except Exception as e:
        raise HTTPException(500, detail=str(e))
        
def apply_parameters_to_code(code: str, parameters: dict) -> str:
    """
    Replace parameter values in the CadQuery code
    This is a simple implementation - you'll need to adapt based on your code structure
    """
    # For each parameter, replace its value in the code
    # This is highly dependent on your code structure
    
    # Example:
    # If your code has lines like: width = 10
    # You can replace them with: width = parameters['width']['value']
    
    # This is a simplified version - customize based on your actual code structure
    
    # For now, we'll just return the code as is
    return code