# databricks_uploader.py
import os
import subprocess

def upload_to_databricks(local_path: str, dbfs_path: str):
    try:
        cmd = [
            "databricks", "fs", "cp",
            local_path, dbfs_path,
            "--overwrite"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Upload failed: {result.stderr}")
        print(f"Uploaded: {local_path} -> {dbfs_path}")
    except Exception as e:
        print(f"Error uploading {local_path}: {str(e)}")
