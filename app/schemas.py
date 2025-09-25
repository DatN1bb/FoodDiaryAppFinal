from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class ParseRequest(BaseModel):
    text: str

class ParsedItem(BaseModel):
    name: str
    quantity_text: str
    grams: float
    notes: Optional[str] = ""

class ParseResponse(BaseModel):
    items: List[ParsedItem]

class AnalyzeRequest(BaseModel):
    text: str

class NutrientNumbers(BaseModel):
    energy_kcal: float = 0
    protein_g: float = 0
    fat_g: float = 0
    carbs_g: float = 0
    sugars_g: float = 0
    fiber_g: float = 0
    salt_g: float = 0
    sodium_mg: float = 0

class AnalyzedItem(BaseModel):
    name: str
    grams: float
    off_product_name: Optional[str] = None
    off_code: Optional[str] = None
    nutrients: NutrientNumbers

class AnalyzeResponse(BaseModel):
    items: List[AnalyzedItem]
    totals: NutrientNumbers

class SaveEntryRequest(BaseModel):
    text: str
    items: List[AnalyzedItem]
    created_at: Optional[datetime] = None

class SaveEntryResponse(BaseModel):
    id: int
