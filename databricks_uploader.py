# databricks_uploader.py (API-based for Render)
import os
import requests

def upload_to_databricks(local_path: str, dbfs_path: str):
    token = os.getenv("DATABRICKS_TOKEN")
    instance = os.getenv("DATABRICKS_INSTANCE")

    if not token or not instance:
        raise RuntimeError("DATABRICKS_TOKEN or DATABRICKS_INSTANCE not set")

    # Step 1: Read file
    with open(local_path, "rb") as f:
        file_data = f.read()

    # Step 2: Upload to DBFS using Databricks REST API
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a handle
    handle_resp = requests.post(
        f"{instance}/api/2.0/dbfs/create",
        headers=headers,
        json={"path": dbfs_path, "overwrite": True}
    )
    handle_resp.raise_for_status()
    handle = handle_resp.json()["handle"]

    # 2. Add file contents
    requests.post(
        f"{instance}/api/2.0/dbfs/add-block",
        headers=headers,
        json={"handle": handle, "data": file_data.encode("base64")}
    ).raise_for_status()

    # 3. Close handle
    requests.post(
        f"{instance}/api/2.0/dbfs/close",
        headers=headers,
        json={"handle": handle}
    ).raise_for_status()

    print(f"Uploaded {local_path} to {dbfs_path}")
