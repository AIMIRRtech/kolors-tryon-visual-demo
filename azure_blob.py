import os
import uuid
from datetime import datetime, timedelta, timezone

try:
    from dotenv import load_dotenv
    load_dotenv(".env.local", override=True)
except Exception:
    pass

from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
)


def _parse_connection_string(connection_string: str) -> dict:
    connection_string = (connection_string or "").strip().strip('"').strip("'")
    parts = {}
    for pair in connection_string.split(";"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            parts[key.strip()] = value.strip()
    return parts


def upload_to_blob(img_bytes: bytes, original_filename: str, folder: str = "test", sas_days: int = 10) -> str:
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    container_name = os.getenv("AZURE_CONTAINER_NAME", "test")
    if not connection_string:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING is not set")

    conn_parts = _parse_connection_string(connection_string)
    account_name = conn_parts.get("AccountName")
    account_key = conn_parts.get("AccountKey")
    if not account_name or not account_key:
        raise RuntimeError(
            "Azure connection string must include AccountName and AccountKey. "
            "If using shell source, wrap AZURE_STORAGE_CONNECTION_STRING in quotes "
            "because semicolons can truncate the value."
        )

    ext = os.path.splitext(original_filename or "")[1].lower() or ".jpg"
    mime = "image/png" if ext == ".png" else "image/jpeg"
    blob_name = f"{folder.rstrip('/')}/{uuid.uuid4().hex}{ext}"

    service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = service_client.get_container_client(container_name)
    if not container_client.exists():
        container_client.create_container()

    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(
        img_bytes,
        overwrite=True,
        content_settings=ContentSettings(content_type=mime),
    )

    expires_on = datetime.now(timezone.utc) + timedelta(days=sas_days)
    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=expires_on,
    )

    return f"{blob_client.url}?{sas_token}"
