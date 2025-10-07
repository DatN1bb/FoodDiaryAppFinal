from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3
import httpx
import json
import re

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DB_PATH = "food_diary.db"

# --- DB setup ---
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

# --- Meal parsing & nutrients ---
def mock_parse_meal(meal_text):
    items = [item.strip() for item in meal_text.split(",")]
    cleaned_items = []
    for item in items:
        cleaned = re.sub(r'^\d+\s*(g|kg|ml|cup|slice|pieces|piece)?\s*', '', item, flags=re.I)
        cleaned_items.append(cleaned)
    return cleaned_items

def fetch_nutrients(item_name):
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

def analyze_meal(meal_text):
    items = mock_parse_meal(meal_text)
    results = []
    for item in items:
        nutrients = fetch_nutrients(item)
        results.append(nutrients if nutrients else {"name": item, "calories": 0, "protein": 0, "fat": 0, "carbs": 0})
    return results

# --- JSON model for API requests ---
class MealRequest(BaseModel):
    meal_text: str

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    c = conn.cursor()
    c.execute("SELECT meal_text, nutrients FROM meals ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    meals = [(meal_text, json.loads(nutrients_json)) for meal_text, nutrients_json in rows]
    return templates.TemplateResponse("index.html", {"request": request, "meals": meals})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, meal_text: str = Form(None), meal: MealRequest = Body(None)):
    """
    Handles both form submissions (meal_text) and JSON body (meal.meal_text)
    """
    # Determine source
    if meal_text:  # form data
        text = meal_text
    elif meal and meal.meal_text:  # JSON
        text = meal.meal_text
    else:
        return {"error": "No meal_text provided"}  # could also return a 422

    results = analyze_meal(text)

    # Save to DB
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    c = conn.cursor()
    c.execute("INSERT INTO meals (meal_text, nutrients) VALUES (?, ?)", (text, json.dumps(results)))
    conn.commit()
    conn.close()

    return templates.TemplateResponse("index.html", {"request": request, "meals": [(text, results)]})
