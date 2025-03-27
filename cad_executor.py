import hashlib
import os
import cadquery as cq
from cadquery import exporters

class CadQueryRunner:
    def __init__(self):
        self.last_code = None
        # Verify CadQuery is properly installed
        try:
            test_assembly = cq.Workplane("XY").box(1, 1, 1)
            exporters.export(test_assembly, "test_verify.step")
        except Exception as e:
            raise RuntimeError(f"CadQuery test failed: {str(e)}")

    def generate_model(self, code: str) -> dict:
        try:
            # Ensure model_cache exists
            model_cache = os.path.join(os.getcwd(), "model_cache")
            os.makedirs(model_cache, exist_ok=True)

            # Generate unique filename
            code_hash = hashlib.md5(code.encode()).hexdigest()
            step_path = os.path.join(model_cache, f"{code_hash}.step")
            stl_path = os.path.join(model_cache, f"{code_hash}.stl")

            # Execute code
            locals_dict = {}
            exec(code, {'cq': cq}, locals_dict)

            if 'result' not in locals_dict:
                raise ValueError("Code must define 'result' variable")

            # Get the model result
            model = locals_dict['result']

            # Export STEP
            exporters.export(model, step_path)

            # Export STL
            exporters.export(model, stl_path)

            # Verify exports succeeded
            if not os.path.exists(step_path) or not os.path.exists(stl_path):
                raise RuntimeError("Model files were not generated")

            return {
                "step_path": step_path,
                "stl_path": stl_path
            }

        except Exception as e:
            raise RuntimeError(f"Model generation failed: {str(e)}")

    def export_stl(self, model_path: str) -> str:
        """Convert STEP file to STL for frontend viewing"""
        # Generate STL path from STEP path
        stl_path = model_path.replace('.step', '.stl')

        # If STEP file exists but STL doesn't, generate it
        if os.path.exists(model_path) and not os.path.exists(stl_path):
            try:
                # Load the STEP file
                doc = cq.importers.importStep(model_path)
                # Export as STL
                exporters.export(doc, stl_path, exporters.ExportTypes.STL)
            except Exception as e:
                raise RuntimeError(f"STL conversion failed: {str(e)}")

        return stl_path

# Example usage:
# "model_url": "/models/abc123.step"  # This must exist
