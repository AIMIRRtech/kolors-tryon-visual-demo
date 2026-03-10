from fastapi import FastAPI, Form, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os
import uuid
import shutil
from azure_blob import upload_to_blob

try:
    from dotenv import load_dotenv
    load_dotenv(".env.local", override=True)
except Exception:
    pass

API_URL = os.getenv(
    "AIMIRR_TRYON_API_URL",
    "https://aimirr-kolors-tryon-api-00f4aac34959.herokuapp.com/tryon",
)
API_KEY = (
    os.getenv("TRYON_API_KEY")
    or os.getenv("AIMIRR_TRYON_API_KEY")
    or os.getenv("AIMIRR_API_KEY")
    or ""
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    pass

try:
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except Exception:
    pass

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": None,
            "error": None,
            "person_image_url": "",
            "garment_image_url": "",
            "loading": False,
            "person_upload_preview": None,
        },
    )

@app.post("/tryon", response_class=HTMLResponse)
async def tryon(
    request: Request,
    person_image_url: str = Form(""),
    garment_image_url: str = Form(...),
    person_image_file: UploadFile = File(None),
):
    try:
        # Handle person image: file upload or URL
        person_upload_preview = None
        if person_image_file and person_image_file.filename:
            # Save uploaded file
            ext = os.path.splitext(person_image_file.filename)[1] or ".jpg"
            filename = f"{uuid.uuid4().hex}{ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            with open(filepath, "wb") as f:
                shutil.copyfileobj(person_image_file.file, f)
            # Upload to Azure Blob and pass a SAS URL to upstream API.
            with open(filepath, "rb") as f:
                img_bytes = f.read()
            person_image_url_to_send = upload_to_blob(img_bytes, person_image_file.filename)
            person_upload_preview = f"/uploads/{filename}"
        else:
            person_image_url_to_send = person_image_url

        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers["X-API-Key"] = API_KEY

        payload = {
            "person_image_url": person_image_url_to_send,
            "garment_image_url": garment_image_url,
            "seed": 0,
            "randomize_seed": True,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        img_src = data.get("result_image_url") or data.get("result_image") or data.get("image") or data.get("output")
        if not img_src:
            img_src = str(data)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": img_src,
                "error": None,
                "person_image_url": person_image_url,
                "garment_image_url": garment_image_url,
                "loading": False,
                "person_upload_preview": person_upload_preview,
            },
        )

    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": None,
                "error": str(e),
                "person_image_url": person_image_url,
                "garment_image_url": garment_image_url,
                "loading": False,
                "person_upload_preview": None,
            },
        )
