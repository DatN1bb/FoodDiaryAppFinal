from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from mangum import Mangum
import os

app = FastAPI()

# Get absolute paths for static and templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates_dir = os.path.join(BASE_DIR, "app", "templates")
static_dir = os.path.join(BASE_DIR, "static")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        return HTMLResponse(f"Error: {e}", status_code=500)

# For Vercel
handler = Mangum(app)