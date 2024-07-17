from datetime import datetime
from typing import List

from dateutil.parser import parse

from sqlalchemy import update, select, func, desc, and_, insert
from starlette import status
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import or_

from models.model import review
from utilities import verify_token
from database import get_async_session
from models.model import *
from scheme import *

from auth.auth import register_router
from category.category import category_router
from books.books import BOOK_router
from superuser import role_router


app = FastAPI()
router = APIRouter()


@router.get('/home')
async def home(
        session: AsyncSession = Depends(get_async_session)
):
    # Query to get the top-rated books
    top_rated_query = (
        select(
            book.c.id,
            book.c.title,
            book.c.author,
            book.c.publication_date,
            book.c.category,
            book.c.description,
            book.c.price,
            book.c.quantity,
            book.c.language,
            func.round(func.avg(rate.c.rating), 1).label('average_rating')
        ).join(
            rate, rate.c.book_id == book.c.id, isouter=True
        ).group_by(
            book.c.id
        ).order_by(
            book.c.id
        ).having(
            func.round(func.avg(rate.c.rating), 1) >= 4
        ).limit(5)  # Adjust the limit as needed
    )

    top_rated_result = await session.execute(top_rated_query)
    top_rated_books = top_rated_result.fetchall()

    # Fetch photos for each top-rated book
    top_rated_book_ids = [b.id for b in top_rated_books]
    top_rated_photo_query = select(images).where(images.c.book_id.in_(top_rated_book_ids))
    top_rated_photo_result = await session.execute(top_rated_photo_query)
    top_rated_photos_by_book_id = {book_id: [] for book_id in top_rated_book_ids}

    for photo in top_rated_photo_result.fetchall():
        top_rated_photos_by_book_id[photo.book_id].append(photo.photo_url)

    # Convert the top-rated result to a list of dictionaries with photos included
    top_rated_books_list = [
        {
            "book_id": b.id,
            "title": b.title,
            "author": b.author,
            "publication_date": b.publication_date,
            "category": b.category,
            "description": b.description,
            "price": b.price,
            "quantity": b.quantity,
            "language": b.language,
            "average_rating": b.average_rating if b.average_rating is not None else 0,
            "photos": top_rated_photos_by_book_id.get(b.id, [])  # Get photos for this book
        }
        for b in top_rated_books
    ]

    # Query to get the latest books
    latest_books_query = (
        select(
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
            func.coalesce(func.round(func.avg(rate.c.rating), 1), 0).label('average_rating')
        ).join(
            rate, rate.c.book_id == book.c.id, isouter=True
        ).join(
            review, review.c.book_id == book.c.id, isouter=True
        ).group_by(
            book.c.id
        ).order_by(
            desc(book.c.publication_date)
        ).limit(3)
    )

    latest_books_result = await session.execute(latest_books_query)
    latest_books = latest_books_result.fetchall()

    # Fetch photos for each latest book
    latest_book_ids = [b.id for b in latest_books]
    latest_photo_query = select(images).where(images.c.book_id.in_(latest_book_ids))
    latest_photo_result = await session.execute(latest_photo_query)
    latest_photos_by_book_id = {book_id: [] for book_id in latest_book_ids}

    for photo in latest_photo_result.fetchall():
        latest_photos_by_book_id[photo.book_id].append(photo.photo_url)

    # Convert the latest result to a list of dictionaries with photos included
    latest_books_list = [
        {
            "id": b.id,
            "special_book_id": b.special_book_id,
            "title": b.title,
            "author": b.author,
            "publication_date": b.publication_date,
            "quantity": b.quantity,
            "description": b.description,
            "price": b.price,
            "barcode": b.barcode,
            "language": b.language,
            "category": b.category,
            "average_rating": b.average_rating if b.average_rating is not None else 1,
            "photos": latest_photos_by_book_id.get(b.id, [])  # Get photos for this book
        }
        for b in latest_books
    ]

    return {
        'Top Rated Books': top_rated_books_list,
        'Latest Books': latest_books_list
    }


@router.get('/get-comments')
async def get_reviews(
        book_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    book_result = await session.execute(
        select(book).where(book.c.id == book_id)
    )
    if not book_result.scalar():
        raise HTTPException(status_code=404, detail='Book not found')

    # Sharhlarni olish
    reviews_result = await session.execute(
        select(review).where(review.c.book_id == book_id)
    )

    reviews = reviews_result.fetchall()
    print('review', reviews)



    return [
        {
            "user_id": review.user_id,
            "comments": review.comments,
            "review_date": review.review_date
        }
        for review in reviews
    ]


@router.get('/get-shopping-cart')
async def get_shopping_cart(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    user_id = token.get('user_id')

    user_query = select(user).where(user.c.id == user_id)
    user_result = await session.execute(user_query)
    user_data = user_result.scalar_one_or_none()
    if not user_data:
        raise HTTPException(status_code=404, detail=f'User with id {user_id} not found')

    query = select(shopping_cart).where(shopping_cart.c.user_id == user_id)

    result = await session.execute(query)
    shopping_cart_items = result.fetchall()
    print(shopping_cart_items)
    result = []
    for row in shopping_cart_items:
        result.append({
            "id": row.id,
            "user_id": row.user_id,
            "book_title": (await session.execute(select(book.c.title).where(book.c.id == row.book_id))).scalar(),
            "quantity": row.quantity,
            "price": (await session.execute(select(book.c.price).where(book.c.id == row.book_id))).scalar()
        })
    return result



@router.post('/add-comment')
async def add_review(
        book_id: int,
        rating:int,
        comment: str,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    user_id = token.get('user_id')
    result = await session.execute(
        select(user).where(user.c.id == user_id)
    )
    if not result.scalar():
        raise HTTPException(status_code=404, detail='User not found')

    book_result = await session.execute(
        select(book).where(book.c.id == book_id)
    )
    if not book_result.scalar():
        raise HTTPException(status_code=404, detail='Book not found')

    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail='Rating must be between 1 and 5')

    insert_query = review.insert().values(
        user_id=user_id,
        book_id=book_id,
        rating=rating,
        comment=comment,
        review_date=datetime.utcnow()
    )
    await session.execute(insert_query)
    await session.commit()

    return {'message': 'Review added successfully'}


@router.post("/book-rating")
async def create_rate(
        book_id: int,
        rating: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    book_query =  await session.execute(select(book).where(book.c.id == book_id))
    books = book_query.fetchone()

    if not books:
        raise HTTPException(status_code=404, detail="Book not found")

    user_id = token.get('user_id')
    query = select(rate).where(and_(rate.c.user_id == user_id, rate.c.book_id == book_id))
    result = await session.execute(query)
    existing_rate = result.fetchall()

    if existing_rate:
        raise HTTPException(status_code=400, detail="User has already rated this book")

    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    query = insert(rate).values(user_id=user_id, book_id=book_id, rating=rating)
    await session.execute(query)
    await session.commit()

    return {"message": "Rating created successfully"}


@router.post('/add-to-cart')
async def add_to_cart(
        item: ShoppingCartItem,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    user_id = token.get('user_id')

    user_result = await session.execute(
        select(user).where(user.c.id == user_id)
    )
    user_record = user_result.scalar()
    if not user_record:
        raise HTTPException(status_code=404, detail='User not found')

    book_result = await session.execute(
        select(book).where(book.c.id == item.book_id)
    )
    book_record = book_result.fetchone()
    if not book_record:
        raise HTTPException(status_code=404, detail='Book not found')
    print(book_record.quantity)
    if book_record.quantity < item.quantity:
        raise HTTPException(status_code=400, detail='Not enough stock available')

    cart_item_result = await session.execute(
        select(shopping_cart).where(
            (shopping_cart.c.user_id == user_id) &
            (shopping_cart.c.book_id == item.book_id)
        )
    )
    existing_cart_item = cart_item_result.fetchone()

    if existing_cart_item:
        new_quantity = existing_cart_item.quantity + item.quantity
        if book_record.quantity < new_quantity:
            raise HTTPException(status_code=400, detail='Not enough quantity available')
        update_query = (
            update(shopping_cart)
            .where(
                (shopping_cart.c.user_id == user_id) &
                (shopping_cart.c.book_id == item.book_id)
            )
            .values(quantity=new_quantity)
        )
        await session.execute(update_query)
    else:

        insert_query = shopping_cart.insert().values(
            user_id=user_id,
            book_id=item.book_id,
            quantity=item.quantity,
        )
        await session.execute(insert_query)

    new_book_quantity = book_record.quantity - item.quantity
    update_book_query = (
        update(book)
        .where(book.c.id == item.book_id)
        .values(quantity=new_book_quantity)
    )
    await session.execute(update_book_query)
    await session.commit()

    return {"message": "Item added to cart successfully"}



search_router = APIRouter()

@search_router.get('/search-books', response_model=List[BooksList])
async def search_books(
        query: str,
        session: AsyncSession = Depends(get_async_session),
):

    search_query = f"%{query}%"

    stmt = select(
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
        book.c.category
    ).where(
        or_(
            book.c.title.ilike(search_query),
            book.c.author.ilike(search_query),
            book.c.category.ilike(search_query)
        )
    ).order_by(book.c.id)

    result = await session.execute(stmt)
    books_list = result.fetchall()

    # Convert the result to a list of dictionaries
    books_list = [
        {
            "id": b.id,
            "special_book_id": b.special_book_id,
            "title": b.title,
            "author": b.author,
            "publication_date": b.publication_date,
            "quantity": b.quantity,
            "description": b.description,
            "price": b.price,
            "barcode": b.barcode,
            "language": b.language,
            "category": b.category
        }
        for b in books_list
    ]

    return books_list





app.include_router(search_router, tags=['Search'])
app.include_router(register_router, prefix='/auth', tags=['auth'])
app.include_router(role_router, tags=['superuser'])
app.include_router(category_router, prefix='/category')
app.include_router(BOOK_router, prefix='/book')
app.include_router(router, tags=['for users'])


