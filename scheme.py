from typing import Optional
from datetime import date
from pydantic import BaseModel


class ShoppingCartItem(BaseModel):
    book_id: int
    quantity: int

class BooksList(BaseModel):
    id: int
    special_book_id: int
    title: str
    author: str
    publication_date: date
    quantity: int
    description: Optional[str]
    price: float
    barcode: str
    language: str
    category: str
