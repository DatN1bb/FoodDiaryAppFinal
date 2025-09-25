import httpx
from typing import Optional, Dict, Any, Tuple

BASE = "https://world.openfoodfacts.org"

async def search_best_match(client: httpx.AsyncClient, query: str) -> Optional[Dict[str, Any]]:
    # Try advanced search first
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5,
        "sort_by": "relevancy",
    }
    r = await client.get(f"{BASE}/cgi/search.pl", params=params, timeout=20.0)
    r.raise_for_status()
    data = r.json()
    products = data.get("products", []) or []
    if not products:
        return None
    # Heuristic: prefer products with nutriments and nutrition_grade/fr
    products = sorted(
        products,
        key=lambda p: (
            -int(bool(p.get("nutriments"))),
            -int(bool(p.get("nutrition_grade_fr"))),
            -int(p.get("nutriments", {}).get("energy-kcal_100g") is not None),
        ),
    )
    return products[0]

def scale_nutrients(nutriments: Dict[str, Any], grams: float) -> Dict[str, float]:
    # OFF fields are per 100g typically
    per100 = 100.0
    factor = grams / per100 if per100 else 0
    def get(k, default=0.0):
        return float(nutriments.get(k, default) or 0.0)
    # Try common keys, falling back to energy in kJ conversion when needed
    energy_kcal_100g = nutriments.get("energy-kcal_100g")
    if energy_kcal_100g is None:
        # Convert from kJ to kcal if possible
        energy_kj_100g = nutriments.get("energy_100g")
        if energy_kj_100g is not None:
            energy_kcal_100g = float(energy_kj_100g) / 4.184
        else:
            energy_kcal_100g = 0.0

    return {
        "energy_kcal": float(energy_kcal_100g) * factor,
        "protein_g": get("proteins_100g") * factor,
        "fat_g": get("fat_100g") * factor,
        "carbs_g": get("carbohydrates_100g") * factor,
        "sugars_g": get("sugars_100g") * factor,
        "fiber_g": get("fiber_100g") * factor,
        "salt_g": get("salt_100g") * factor,
        "sodium_mg": get("sodium_100g") * factor * 1000.0,
    }
