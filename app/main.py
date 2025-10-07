from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3
import json
import re
import httpx

app = FastAPI()

# Mount static and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

DB_PATH = "food_diary.db"

# --- Pydantic model for JSON requests ---
class FoodRequest(BaseModel):
    food: str

# --- Initialize DB ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_text TEXT,
            nutrients TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Helper functions ---
def mock_parse_meal(meal_text: str):
    items = [item.strip() for item in meal_text.split(",")]
    cleaned_items = []
    for item in items:
        cleaned = re.sub(r'^\d+\s*(g|kg|ml|cup|slice|pieces|piece)?\s*', '', item, flags=re.I)
        cleaned_items.append(cleaned)
    return cleaned_items

def fetch_nutrients(item_name: str):
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {"search_terms": item_name, "search_simple": 1, "action": "process", "json": 1, "page_size": 1}
    try:
        response = httpx.get(url, params=params, timeout=10)
        data = response.json()
    except Exception:
        return None

    if data.get("count", 0) == 0:
        return None

    product = data["products"][0]
    return {
        "name": product.get("product_name", item_name),
        "calories": product.get("nutriments", {}).get("energy-kcal_100g", 0),
        "protein": product.get("nutriments", {}).get("proteins_100g", 0),
        "fat": product.get("nutriments", {}).get("fat_100g", 0),
        "carbs": product.get("nutriments", {}).get("carbohydrates_100g", 0),
    }

# --- Main meal analysis function ---
def analyze_food(meal_text: str):
    items = mock_parse_meal(meal_text)
    results = []
    for item in items:
        nutrients = fetch_nutrients(item)
        results.append(nutrients if nutrients else {"name": item, "calories": 0, "protein": 0, "fat": 0, "carbs": 0})
    return results

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Fetch last 10 meals from DB
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    c = conn.cursor()
    c.execute("SELECT meal_text, nutrients FROM meals ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()

    meals = [(meal_text, json.loads(nutrients_json)) for meal_text, nutrients_json in rows]
    return templates.TemplateResponse("index.html", {"request": request, "meals": meals})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    meal_text: str = Form(None),        # for HTML forms
    food: FoodRequest = Body(None)      # for JSON requests
):
    """
    Handles both:
    - Form submissions (meal_text)
    - JSON submissions (food)
    """
    if meal_text:
        text = meal_text
    elif food and food.food:
        text = food.food
    else:
        return {"error": "No meal data provided"}  # prevents 422

    # Analyze the meal
    results = analyze_food(text)

    # Save to DB
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    c = conn.cursor()
    c.execute("INSERT INTO meals (meal_text, nutrients) VALUES (?, ?)", (text, json.dumps(results)))
    conn.commit()
    conn.close()

    # Return HTML template
    return templates.TemplateResponse("index.html", {"request": request, "meals": [(text, results)]})
