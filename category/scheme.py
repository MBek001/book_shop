import enum

from fastapi import HTTPException
from pydantic import BaseModel
from enum import Enum

class AgesEnum(enum.Enum):
    zero_to_two = "for children from 0 to 2 ages"
    three_to_five = "for children from 3 to 5 ages"
    six_to_nine = "for children from 6 to 9 ages"
    ten_to_fourteen = "for children from 10 to 15 ages"

class CategoryScheme(BaseModel):
    age_category_id: int
    category_name: str
