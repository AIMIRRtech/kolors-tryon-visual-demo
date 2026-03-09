from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os

API_URL = "https://aimirr-kolors-tryon-api-00f4aac34959.herokuapp.com/tryon"
API_KEY = os.getenv("TRYON_API_KEY", "")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

try:
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")
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
            "person_image_url": None,
            "garment_image_url": None,
            "loading": False,
        },
    )


@app.post("/tryon", response_class=HTMLResponse)
async def tryon(
    request: Request,
    person_image_url: str = Form(...),
    garment_image_url: str = Form(...),
    seed: int = Form(0),
    randomize_seed: bool = Form(False),
):
    payload = {
        "person_image_url": person_image_url,
        "garment_image_url": garment_image_url,
        "seed": seed,
        "randomize_seed": randomize_seed,
    }

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                API_URL,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": API_KEY,
                },
                json=payload,
            )
        data = resp.json()
        if not resp.is_success:
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "result": None,
                    "error": data.get("message", f"Request failed ({resp.status_code})"),
                    "person_image_url": person_image_url,
                    "garment_image_url": garment_image_url,
                    "loading": False,
                },
            )

        # Try common response field names
        result_b64 = (
            data.get("result_image_base64")
            or data.get("image_base64")
            or data.get("image")
        )
        result_url = data.get("result_image_url") or data.get("image_url")

        if result_b64:
            img_src = f"data:image/png;base64,{result_b64}"
        elif result_url:
            img_src = result_url
        else:
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "result": None,
                    "error": f"Unexpected API response keys: {list(data.keys())}",
                    "person_image_url": person_image_url,
                    "garment_image_url": garment_image_url,
                    "loading": False,
                },
            )

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": img_src,
                "error": None,
                "person_image_url": person_image_url,
                "garment_image_url": garment_image_url,
                "loading": False,
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
            },
        )
