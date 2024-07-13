import datetime
import enum

from fastapi import HTTPException
from pydantic import BaseModel
from enum import Enum

class AgesEnum(enum.Enum):
    zero_to_two = "for children from 0 to 2 ages"
    three_to_five = "for children from 3 to 5 ages"
    six_to_nine = "for children from 6 to 9 ages"
    ten_to_fourteen = "for children from 10 to 15 ages"


class CategoryEnum(enum.Enum):
    Fairy_tales = 'Сказки/Стихи/Рассказы'
    Interactive_books = 'Интерактивные книги'
    developmental_books = 'Развивающие пособия'
    Encyclopedias = 'Энциклопедии'
    Creation = 'Творчество-лепка/раскраски/наклейки '
    Developmental='Развивающие-игры/игрушки '
    English_books='Книги на английском языке'
    Toy_books='Книжки/Игрушки-музыкальные/деревянные/мягкие'
    Science_and_tech = 'Наука и техника'
    Puzzles='Пазлы'


class CategoryList(BaseModel):
    id: int
    category_name: str

class Books_in_category(BaseModel):
    id: int
    title: str
    author: str
    publication_date: datetime.date
    category: str
    description: str
    price: float
    quantity: int
    language: str





