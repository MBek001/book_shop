import enum
from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import TIMESTAMP


class BookGenreEnum(enum.Enum):
    fiction = "Fiction"
    non_fiction = "Non-Fiction"
    biography = "Biography"
    science_fiction = "Science Fiction"
    history = "History"
    poetry = "Poetry"
    cooking = "Cooking"


class BookLanguageEnum(enum.Enum):
    russian = "Russian"
    english = "English"
    french = "French"
    uzbek = "Uzbek"

class ShoppingCartItem(BaseModel):
    book_id: int
    quantity: int


class Review(BaseModel):
    book_id: int
    rating: int
    comment: str
