from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session, select
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

DB_PATH = Path("food_diary.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

class Entry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    items: List["EntryItem"] = Relationship(back_populates="entry")

class EntryItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entry_id: int = Field(foreign_key="entry.id")
    name: str
    grams: float
    off_product_name: Optional[str] = None
    off_code: Optional[str] = None
    energy_kcal: float = 0
    protein_g: float = 0
    fat_g: float = 0
    carbs_g: float = 0
    sugars_g: float = 0
    fiber_g: float = 0
    salt_g: float = 0
    sodium_mg: float = 0

    entry: Entry = Relationship(back_populates="items")

def init_db():
    SQLModel.metadata.create_all(engine)

def save_entry(text: str, items: list, created_at: Optional[datetime] = None) -> int:
    from datetime import datetime
    created = created_at or datetime.utcnow()
    with Session(engine) as session:
        entry = Entry(text=text, created_at=created)
        session.add(entry)
        session.flush()
        for it in items:
            ei = EntryItem(
                entry_id=entry.id,
                name=it["name"],
                grams=it["grams"],
                off_product_name=it.get("off_product_name"),
                off_code=it.get("off_code"),
                energy_kcal=it["nutrients"]["energy_kcal"],
                protein_g=it["nutrients"]["protein_g"],
                fat_g=it["nutrients"]["fat_g"],
                carbs_g=it["nutrients"]["carbs_g"],
                sugars_g=it["nutrients"]["sugars_g"],
                fiber_g=it["nutrients"]["fiber_g"],
                salt_g=it["nutrients"]["salt_g"],
                sodium_mg=it["nutrients"]["sodium_mg"],
            )
            session.add(ei)
        session.commit()
        return entry.id

def list_entries(limit: int = 50):
    with Session(engine) as session:
        stmt = select(Entry).order_by(Entry.created_at.desc()).limit(limit)
        return session.exec(stmt).all()

def get_entry(entry_id: int):
    with Session(engine) as session:
        e = session.get(Entry, entry_id)
        if not e:
            return None
        _ = e.items  # load relationship
        return e
