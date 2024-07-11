import datetime
import enum

from pydantic import BaseModel

class BookCategoryEnum(enum.Enum):
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

class BooksList(BaseModel):
    id: int
    title: str
    author: str
    publication_date: datetime.date
    category: str
    description: str
    price: float
    quantity: int
    language: str
    average_rating: float
    number_of_reviews: int
