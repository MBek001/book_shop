from typing import List

from fastapi import FastAPI, APIRouter,HTTPException, Depends,status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update,insert, and_
from sqlalchemy.ext.asyncio import AsyncSession
from utilities import generate_token, verify_token
from database import get_async_session
from models.model import age_categories, user, categories, categories_in_ages,book

from category.scheme import *




category_router = APIRouter(tags=['category'])


@category_router.post('/add_age_category')
async def add_age_category(
        age_category: AgesEnum,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
    ):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        user_id = token.get('user_id')
        admin = await session.execute(
            select(user).where(
                (user.c.id == user_id) &
                (user.c.is_admin == True)
            )
        )
        if not admin.scalar():
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
        query = insert(age_categories).values(ages=age_category.value)
        await session.execute(query)
        await session.commit()
        return {'success': True, 'message': f'Category added successfully!'}
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail='Category already exists!')


@category_router.post('/add_category')
async def add_category(
        age_category: AgesEnum,
        category_data: CategoryEnum,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        user_id = token.get('user_id')
        admin = await session.execute(
            select(user).where(
                (user.c.id == user_id) &
                (user.c.is_admin == True)
            )
        )
        if not admin.scalar():
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

        category_query = select(categories.c.id).where(categories.c.category_name == category_data.value)
        category_result = await session.execute(category_query)
        existing_category_id = category_result.scalar()

        # Insert category_data into categories table
        if existing_category_id is None:
            # Insert category_data into categories table if it doesn't exist
            category_insert_query = insert(categories).values(
                category_name=category_data.value
            ).returning(categories.c.id)
            result = await session.execute(category_insert_query)
            category_id = result.scalar()
        else:
            # Use the existing category_id if category already exists
            category_id = existing_category_id

        age_category_query = select(age_categories.c.id).where(age_categories.c.ages == age_category.value)
        age_category_result = await session.execute(age_category_query)
        age_category_id = age_category_result.scalar()

        if age_category_id:
            existing_entry_query = select(categories_in_ages.c.id).where(
                and_(
                    categories_in_ages.c.age_id == age_category_id,
                    categories_in_ages.c.category_id == category_id
                )
            )
            existing_entry_result = await session.execute(existing_entry_query)
            existing_entry = existing_entry_result.scalar()

            if existing_entry:
                raise HTTPException(status_code=400,detail='This subcategory is already in this age category ')

            books_category_query = insert(categories_in_ages).values(
                age_id=age_category_id,
                category_id=category_id
            )
            await session.execute(books_category_query)
            await session.commit()

            return {'success': True, 'message': 'Category added successfully!'}
        else:
            raise HTTPException(status_code=400, detail='Age category does not exist')

    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail='Category already exists')



@category_router.get('/all_categories', response_model=List[CategoryList])
async def get_categories(
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')

    all_category = await session.execute(select(categories))
    return all_category.fetchall()


@category_router.get('/books_in category',response_model=List[Books_in_category])
async def get_books_in_category(
        category_enum: CategoryEnum,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')
    user_id = token.get('user_id')
    usr = await session.execute(
        select(user).
        where(user.c.id == user_id))

    if not usr.scalar():
        raise HTTPException(status_code=403, detail='Forbidden')
    books_in_category = await session.execute(select(book).where(book.c.category == category_enum.value))
    return books_in_category.fetchall()