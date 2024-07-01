from datetime import datetime
from dateutil.parser import parse

from sqlalchemy import update, select
from starlette import status
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth import register_router
from utilities import verify_token
from database import get_async_session
from models.model import user, book, shopping_cart, review
from scheme import *
from category.category import category_router

app = FastAPI()
router = APIRouter()


@router.post('/add-book')
async def add_book(
        title: str,
        author: str,
        publication_date: str,
        quantity: int,
        genre: BookGenreEnum,
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
        genre= str(genre.value),
        description= description,
        price= price,
        quantity= quantity,
        language= str(language.value)
    )
    await session.execute(query)
    await session.commit()

    return {"message": "Book added successfully"}


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
        review_data: Review,
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
        select(book).where(book.c.id == review_data.book_id)
    )
    if not book_result.scalar():
        raise HTTPException(status_code=404, detail='Book not found')

    if review_data.rating < 1 or review_data.rating > 5:
        raise HTTPException(status_code=400, detail='Rating must be between 1 and 5')

    insert_query = review.insert().values(
        user_id=user_id,
        book_id=review_data.book_id,
        rating=review_data.rating,
        comment=review_data.comment,
        review_date=datetime.utcnow()
    )
    await session.execute(insert_query)
    await session.commit()

    return {
        "user_id": user_id,
        "book_id": review_data.book_id,
        "rating": review_data.rating,
        "comment": review_data.comment,
        "review_date": datetime.utcnow()
    }


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




app.include_router(register_router, prefix='/auth')
app.include_router(router)
app.include_router(category_router, prefix='/category')

