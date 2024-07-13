from datetime import datetime
from typing import List,Optional

from dateutil.parser import parse

from sqlalchemy import update, select, func, delete
from starlette import status
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from utilities import verify_token
from database import get_async_session
from models.model import user, book, review
from category.scheme import CategoryEnum


from books.scheme import *

book_router = APIRouter(tags=['books'])


@book_router.post('/add-book')
async def add_book(
        special_book_id: int,
        title: str,
        author: str,
        publication_date: str,
        quantity: int,
        category: CategoryEnum,
        description: str,
        price: float,
        language: BookLanguageEnum,
        barcode: str,
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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Book with this TITLE and AUTHOR already exists')

    checking_book = await session.execute(
        select(book).
        where((book.c.special_book_id == special_book_id)|
              (book.c.barcode == barcode)
              )
    )
    if checking_book.scalar():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Book with this SPECIAL_BOOK_ID or BARCODE already exists')

    selected_date = parse(publication_date).date()
    barcode_info = len(barcode)

    if barcode_info<8 and barcode_info>13:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Barcode should be between 8 and 13 digits')


    query = book.insert().values(
        special_book_id=special_book_id,
        title=title,
        author=author,
        publication_date=selected_date,
        category=str(category.value),
        description=description,
        price= price,
        quantity=quantity,
        barcode=barcode,
        language=str(language.value)
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


    query = select(
        book.c.id,
        book.c.special_book_id,
        book.c.title,
        book.c.author,
        book.c.publication_date,
        book.c.quantity,
        book.c.description,
        book.c.price,
        book.c.barcode,
        book.c.language,
        book.c.category,
        func.coalesce(func.round(func.avg(review.c.rating), 1), 1).label('average_rating')
    ).join(
        review, review.c.book_id == book.c.id, isouter=True
    ).group_by(
        book.c.id
    ).order_by(
        book.c.id
    )

    books = await session.execute(query)
    books_list = books.fetchall()

    return books_list


@book_router.delete('/delete-book')
async def delete_book(
        special_book_id: Optional[int] = None,
        title: Optional[str] = None,
        book_id: Optional[int] = None,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    user_id = token.get('user_id')
    result = await session.execute(
        select(user).where(
            (user.c.id == user_id) &
            (user.c.is_admin == True)
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    # Build the query based on provided parameters
    if special_book_id:
        book_query = select(book).where(book.c.special_book_id == special_book_id)
    elif title:
        book_query = select(book).where(book.c.title == title)
    elif book_id:
        book_query = select(book).where(book.c.id == book_id)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Provide at least one identifier (special_book_id, title, or book_id)')

    existing_book = await session.execute(book_query)
    book_to_delete = existing_book.scalar_one_or_none()
    if book_to_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Book not found')

    print('delete book', book_to_delete)

    # Delete associated reviews first
    await session.execute(delete(review).where(review.c.book_id == book_to_delete))

    # Then delete the book
    if special_book_id:
        delete_query = book.delete().where(book.c.special_book_id == special_book_id)
    elif title:
        delete_query = book.delete().where(book.c.title == title)
    elif book_id:
        delete_query = book.delete().where(book.c.id == book_id)

    await session.execute(delete_query)
    await session.commit()

    return {"message": "Book deleted successfully"}

