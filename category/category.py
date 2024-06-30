from fastapi import FastAPI, APIRouter,HTTPException, Depends,status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update,insert
from sqlalchemy.ext.asyncio import AsyncSession
from utilities import generate_token, verify_token
from database import get_async_session
from models.model import age_categories, user, categories



from category.scheme import AgesEnum,CategoryScheme


app = FastAPI

category_router = APIRouter()


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
        category_data: CategoryScheme,
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

        query = insert(categories).values(
            age_category_id=category_data.age_category_id,
            categories=category_data.category_name
        )
        await session.execute(query)
        await session.commit()
        return {'success': True, 'message': f'Category added successfully!'}
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail='Category already exists')