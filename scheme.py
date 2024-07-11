import enum
from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import TIMESTAMP



class ShoppingCartItem(BaseModel):
    book_id: int
    quantity: int


class Review(BaseModel):
    book_id: int
    rating: int
    comment: str
