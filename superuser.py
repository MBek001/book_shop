from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
from database import get_async_session
from models.model import user, superuser
from utilities import verify_token

role_router = APIRouter()

@role_router.post('/add-superuser')
async def add_superuser(
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    is_user = token.get('user_id')

    is_admin_query = await session.execute(
        select(user).where(
            (user.c.id == is_user) &
            (user.c.is_admin == True)
        )
    )
    is_admin = is_admin_query.scalar()

    if not is_admin:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    if user_id and email:
        raise HTTPException(status_code=400, detail='Provide only one identifier (user_id or email)')

    if user_id:
        user_query = await session.execute(select(user).where(user.c.id == user_id))
    elif email:
        user_query = await session.execute(select(user).where(user.c.email == email))
        user_row = user_query.fetchone()
        if user_row:
            user_id = user_row.id
        else:
            raise HTTPException(status_code=404, detail='User with provided email not found')
    else:
        raise HTTPException(status_code=400, detail='Provide at least one identifier (user_id or email)')

    user_row = await session.execute(select(user).where(user.c.id == user_id))
    if not user_row.scalar():
        raise HTTPException(status_code=404, detail='User not found')

    superuser_query = await session.execute(select(superuser).where(superuser.c.user_id == user_id))
    if superuser_query.scalar():
        # User is already in the superuser table, update the is_superuser flag to True
        update_query = (
            update(superuser).
            where(superuser.c.user_id == user_id).
            values(is_superuser=True)
        )
        await session.execute(update_query)
    else:
        # Add to superuser table
        stmt = superuser.insert().values(user_id=user_id, is_superuser=True)
        await session.execute(stmt)

    await session.commit()

    return {"message": "Superuser added successfully"}




@role_router.get('/get-superusers')
async def get_superusers(
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    is_user = token.get('user_id')

    is_admin = await session.execute(
        select(user).where(
            (user.c.id == is_user) &
            (user.c.is_admin == True)
        )
    )

    if not is_admin.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    # Join superuser and user tables to fetch superuser details
    query = select(
        superuser.c.id,
        user.c.name,
        superuser.c.user_id,
        user.c.email,
        superuser.c.is_superuser
    ).join(
        user, superuser.c.user_id == user.c.id
    )

    result = await session.execute(query)
    superusers = result.fetchall()

    # Convert the result to a list of dictionaries
    superusers_list = [
        {
            "id": su.id,
            "name": su.name,
            "user_id": su.user_id,
            "email": su.email,
            "is_superuser": su.is_superuser
        }
        for su in superusers
    ]

    return superusers_list


@role_router.patch('/delete-superuser')
async def delete_superuser(
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    is_user = token.get('user_id')

    is_admin_query = await session.execute(
        select(user).where(
            (user.c.id == is_user) &
            (user.c.is_admin == True)
        )
    )
    is_admin = is_admin_query.scalar()

    if not is_admin:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    if user_id and email:
        raise HTTPException(status_code=400, detail='Provide only one identifier (user_id or email)')

    if user_id:
        superuser_query = await session.execute(select(superuser).where(superuser.c.user_id == user_id))
        superuser_data = superuser_query.scalar()
        if not superuser_data:
            raise HTTPException(status_code=404, detail='User with provided id not found')
    elif email:
        user_query = await session.execute(select(user).where(user.c.email == email))
        user_data = user_query.fetchone()
        if user_data:
            user_id = user_data.id
        else:
            raise HTTPException(status_code=404, detail='User with provided email not found')
    else:
        raise HTTPException(status_code=400, detail='Provide at least one identifier (user_id or email)')

    update_query = (
        update(superuser).
        where(superuser.c.user_id == user_id).
        values(is_superuser=False)
    )
    await session.execute(update_query)
    await session.commit()

    return {"message": "Superuser status removed successfully"}

