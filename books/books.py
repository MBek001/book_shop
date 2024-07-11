from datetime import datetime
from typing import List

from dateutil.parser import parse

from sqlalchemy import update, select
from starlette import status
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from utilities import verify_token
from database import get_async_session
from models.model import user, book
from category.scheme import CategoryEnum


from books.scheme import *

book_router = APIRouter(tags=['books'])

@book_router.post('/add-book')
async def add_book(
        title: str,
        author: str,
        publication_date: str,
        quantity: int,
        category: CategoryEnum,
        description: str,
        price: float,
        language: BookLanguageEnum,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')
    user_id = token.get('user_id')
    result = await session.execute(
        select(user).where(
            (user.c.id == user_id) &
            (user.c.is_admin == True)
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    existing_book = await session.execute(
        select(book).where(
            (book.c.title == title) &
            (book.c.author == author)
        )
    )
    if existing_book.scalar():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Book already exists')

    selected_date = parse(publication_date).date()

    query = book.insert().values(
        title= title,
        author= author,
        publication_date=selected_date,
        category= str(category.value),
        description= description,
        price= price,
        quantity= quantity,
        language= str(language.value)
    )
    await session.execute(query)
    await session.commit()

    return {"message": "Book added successfully"}


@book_router.get('/get-books',response_model=List[BooksList])
async def get_books(
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')
    user_id = token.get('user_id')
    result = await session.execute(
        select(user).where(
            (user.c.id == user_id)
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    query = select(book).order_by(book.c.title)
    books = await session.execute(query)
    return books.fetchall()