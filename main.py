from datetime import datetime
from dateutil.parser import parse

from sqlalchemy import update, select, func, desc
from starlette import status
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from utilities import verify_token
from database import get_async_session
from models.model import user, book, shopping_cart, review
from scheme import *

from auth.auth import register_router
from category.category import category_router
from books.books import book_router


app = FastAPI()
router = APIRouter(tags=['main'])


@router.get('/home')
async def home(
        session: AsyncSession = Depends(get_async_session)
):
    # Query to get the books ordered by average rating
    query = select(
        book.c.id,
        book.c.special_book_id,
        book.c.title,
        book.c.author,
        book.c.publication_date,
        book.c.category,
        book.c.description,
        book.c.price,
        book.c.quantity,
        book.c.language,
        func.round(func.avg(review.c.rating), 1).label('average_rating')
    ).join(
        review, review.c.book_id == book.c.id, isouter=True
    ).group_by(
        book.c.id
    ).order_by(
        desc('average_rating')
    ).limit(2)  # Adjust the limit as needed

    result = await session.execute(query)
    books = result.fetchall()

    # Convert the result to a list of dictionaries
    books_list = [
        {
            "id": b.id,
            "special_book_id": b.special_book_id,
            "title": b.title,
            "author": b.author,
            "publication_date": b.publication_date,
            "category": b.category,
            "description": b.description,
            "price": b.price,
            "quantity": b.quantity,
            "language": b.language,
            "average_rating": b.average_rating if b.average_rating is not None else 0
        }
        for b in books
    ]

    return ['books', books_list]




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


@router.post('/add-review')
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


@router.get('/reviews/{book_id}')
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

    return [
        {
            "user_id": review.user_id,
            "book_id": review.book_id,
            "rating": review.rating,
            "comment": review.comment,
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




app.include_router(register_router, prefix='/auth', tags=['auth'])
app.include_router(category_router, prefix='/category')
app.include_router(book_router, prefix='/book')
app.include_router(router)


