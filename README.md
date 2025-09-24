# Online Food Diary via ChatGPT + Open Food Facts

This starter lets users enter meals in plain text. The backend:
1) Uses OpenAI to parse the text into structured items with gram estimates
2) Fetches **real nutrient data** from **Open Food Facts (OFF)**
3) Computes totals and stores everything in SQLite
4) Displays results in a minimal web UI

> You keep ChatGPT for understanding the meal; you keep OFF for **grounded nutrition data**.

---

## Quickstart

1. **Clone or unzip** this folder.
2. Create a virtual env and install deps:
   ```bash
   python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set your `OPENAI_API_KEY`.
4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Open: http://127.0.0.1:8000

---

## How it works

- **/api/parse** → Sends your free‑text to OpenAI with a strict JSON schema, returning items with names + gram estimates.  
- **/api/analyze** → For each item, hits Open Food Facts search endpoints to find the best product match and its nutrients per 100g, then scales to the grams estimate.  
- **/api/entries** → Persists the entry, items, and nutrient totals into SQLite (via `sqlmodel`).  
- **Frontend**: minimal HTML at `/` that posts your meal, shows parsed items + real nutrients, and lets you save.

**Note on accuracy**: OFF data varies by product. This starter picks the top relevant result. For serious use, consider:
- Allowing the user to pick among multiple matches
- Caching favorite products
- Adding barcode scanning on mobile
- Handling cooked/raw distinctions

---

## Project Structure

```
app/
  main.py            # FastAPI app + routes
  off.py             # Open Food Facts helpers
  db.py              # SQLite models and CRUD
  schemas.py         # Pydantic/SQLModel schemas
  prompts.py         # System + JSON schema for parsing
  templates/
    index.html       # Minimal UI
```

---

## Example cURL

```
curl -X POST http://127.0.0.1:8000/api/parse -H "Content-Type: application/json" -d '{"text":"2 eggs, 1 slice wholegrain bread with butter, 1 banana"}'
```

---

## License

MIT — do whatever you want, no warranty.
