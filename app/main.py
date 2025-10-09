from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3
import json
import re
import requests
import os

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
DB_PATH = "food_diary.db"

# JSON model for app requests
class FoodRequest(BaseModel):
    food: str

# --- Helper functions ---
def mock_parse_meal(meal_text: str):
    items = [item.strip() for item in meal_text.split(",")]
    cleaned_items = []
    for item in items:
        cleaned = re.sub(r'^\d+\s*(g|kg|ml|cup|slice|pieces|piece)?\s*', '', item, flags=re.I)
        cleaned_items.append(cleaned)
    return cleaned_items

def analyze_food(meal_text: str):
    items = [item.strip() for item in meal_text.split(",")]
    results = []

    for item in items:
        try:
            response = requests.get(
                "https://world.openfoodfacts.org/cgi/search.pl",
                params={"search_terms": item, "search_simple": 1, "action": "process", "json": 1},
                timeout=5
            )
            data = response.json()
            if data.get("products"):
                product = data["products"][0]
                nutrients = product.get("nutriments", {})
                results.append({
                    "name": item,
                    "calories": nutrients.get("energy-kcal_100g", 0),
                    "protein": nutrients.get("proteins_100g", 0),
                    "fat": nutrients.get("fat_100g", 0),
                    "carbs": nutrients.get("carbohydrates_100g", 0),
                })
            else:
                results.append({
                    "name": item,
                    "calories": 0,
                    "protein": 0,
                    "fat": 0,
                    "carbs": 0
                })
        except Exception as e:
            results.append({
                "name": item,
                "calories": 0,
                "protein": 0,
                "fat": 0,
                "carbs": 0,
                "error": str(e)
            })

    return results

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS meals (id INTEGER PRIMARY KEY AUTOINCREMENT, meal_text TEXT, nutrients TEXT)")
    c.execute("SELECT meal_text, nutrients FROM meals ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()

    meals = [(meal_text, json.loads(nutrients_json)) for meal_text, nutrients_json in rows]
    return templates.TemplateResponse("index.html", {"request": request, "meals": meals})

@app.post("/analyze")
async def analyze(meal_text: str = Form(...)):
    results = analyze_meal(meal_text)

    if not os.environ.get("VERCEL"):  # only save locally
        conn = sqlite3.connect("food_diary.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO meals (meal_text, nutrients) VALUES (?, ?)",
            (meal_text, json.dumps(results))
        )
        conn.commit()
        conn.close()

    return {"analysis": results}

    # Save to DB safely
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO meals (meal_text, nutrients) VALUES (?, ?)", (text, json.dumps(results)))
    conn.commit()
    conn.close()

    return templates.TemplateResponse("index.html", {"request": request, "meals": [(text, results)]})
