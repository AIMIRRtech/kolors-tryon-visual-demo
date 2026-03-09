# Kolors Virtual Try-On Visual Demo

A Heroku-deployable web UI for the [Kolors Virtual Try-On API](https://github.com/AIMIRRtech/kolors-tryon-api). Enter a person image URL and a garment image URL to generate a virtual try-on result.

## Features

- Dark-themed responsive UI
- Live image preview as you type URLs
- Loading spinner during generation
- Supports base64 and URL-based API responses

## Project Structure

```
app.py                  # FastAPI backend (proxies to Kolors API)
templates/index.html    # Jinja2 HTML template
static/                 # Static assets (placeholder)
Procfile                # Heroku process config
requirements.txt        # Python dependencies
runtime.txt             # Python version for Heroku
```

## Deploy to Heroku

```bash
git clone https://github.com/AIMIRRtech/kolors-tryon-visual-demo.git
cd kolors-tryon-visual-demo

heroku create your-app-name
heroku config:set TRYON_API_KEY=your_api_key_here
git push heroku main
```

## Run Locally

```bash
pip install -r requirements.txt
export TRYON_API_KEY=your_api_key_here
uvicorn app:app --reload --port 8000
```

Then open http://localhost:8000

## Environment Variables

| Variable | Description |
|---|---|
| `TRYON_API_KEY` | API key for the Kolors try-on backend |

## Tech Stack

- **Backend:** FastAPI + Uvicorn
- **Frontend:** Jinja2 templates, vanilla CSS/JS
- **HTTP Client:** httpx (async)
- **Deployment:** Heroku (Python buildpack)
