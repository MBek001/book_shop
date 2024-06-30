from fastapi import FastAPI, APIRouter
from fastapi.security import OAuth2PasswordBearer

from auth.auth import register_router
from category.category import category_router

app = FastAPI()
router = APIRouter()





app.include_router(register_router, prefix='/auth')
app.include_router(category_router, prefix='/category')
app.include_router(router, prefix='/main')
