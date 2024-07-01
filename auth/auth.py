import re
from typing import List
from fastapi import APIRouter, FastAPI,Depends,status, HTTPException
from sqlalchemy import select, update, insert, delete
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from models.model import *
from database import get_async_session
from auth.schemes import UserLogin, UserDb, UserRegister, GetUSerInfo, AllUserInfo
from utilities import *



from passlib.context import CryptContext

app = FastAPI(title='Task', version='1.0.0')
pwd_contex = CryptContext(schemes=['bcrypt'], deprecated='auto')

register_router = APIRouter()



@register_router.post('/registration')
async def register(
        user_data: UserRegister,
        session: AsyncSession = Depends(get_async_session)
    ):
    if user_data.password1 == user_data.password2:
        email_exists = await session.execute(select(user).where(user.c.email == user_data.email))
        email_exists_value = email_exists.scalar()

        if email_exists_value is not None:
            return {'success': False, 'message': 'Email already exists!'}

        hash_password = pwd_contex.hash(user_data.password1)

        # checking database users there are users or not
        result = await session.execute(select(user.c.id))
        first_user = result.scalar()
        if first_user is None:
            first_user = True
        else:
            first_user = False

        user_in_db = UserDb(**dict(user_data), password=hash_password,is_admin=first_user)
        query = insert(user).values(**dict(user_in_db))
        await session.execute(query)
        await session.commit()
        return {'success': True, 'message': "Account created successfully ✅"}
    else:
        raise HTTPException(status_code=400, detail="Passwords are not the same ❗️")



@register_router.post('/login')
async def login(
        user_data: UserLogin,
        session: AsyncSession = Depends(get_async_session)
):
    email = select(user).where(user.c.email == user_data.email)
    userdata = await session.execute(email)
    user_d = userdata.one_or_none()
    if user_d is None:
        return {'success': False, 'message': 'Email or Password is not correct ❗️'}
    else:
        if pwd_contex.verify(user_data.password, user_d.password):
            token = generate_token(user_d.id)
            return token
        else:
            return {'success': False, 'message': 'Email or Password is not correct ❗️'}

@register_router.patch('/edit-profile')
async def edit_profile(
        email: str = None,
        name: str = None,
        phone_number: str = None,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)

):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    try:
        user_id = token.get('user_id')
        query = select(user).where(user.c.id == user_id)
        result = await session.execute(query)
        user_data = result.scalar_one_or_none()

        update_values = {}
        if email is not None:
            update_values['email'] = email

        if name is not None:
            update_values['name'] = name

        if phone_number is not None:
            if re.match(r'^\+\d{11}$', phone_number):
                update_values['phone_number'] = phone_number
            else:
                raise HTTPException(status_code=400, detail='Enter phone number correctly')

        if update_values:
            query = update(user).where(user.c.id == user_data).values(**update_values)
            await session.execute(query)
            await session.commit()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {'success': True, 'message': 'Profile updated successfully!'}


@register_router.get('/user_info', response_model=List[GetUSerInfo])
async def get_user_info(
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    user_id = token.get('user_id')
    usr = await session.execute(
        select(user).
        where(user.c.id == user_id)
    )
    if not usr.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
    result = await session.execute(select(user).where(user.c.id == user_id))
    return result.fetchall()



@register_router.get('/all_users_info', response_model=List[AllUserInfo])
async def get_users(
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    print('token', token)
    user_id = token.get('user_id')
    admin = await session.execute(
        select(user).where(
            (user.c.id == user_id) &
            (user.c.is_admin==True)
        )
    )
    print(user_id)
    if not admin.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
    result = await session.execute(select(user))
    return result.fetchall()







app.include_router(register_router)