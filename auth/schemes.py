from fastapi import HTTPException
from pydantic import BaseModel ,EmailStr, validator
import phonenumbers

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    phone_number: str
    password1: str
    password2: str


    @validator('phone_number')
    def validate_phone_number(cls, v):
        try:
            parsed_number = phonenumbers.parse(v)
            if not phonenumbers.is_valid_number(parsed_number):
               raise HTTPException(detail='Enter phone number correctly !', status_code=400)
        except phonenumbers.phonenumberutil.NumberParseException:
            raise HTTPException(detail='Enter phone number correctly !', status_code=400)
        return v


class UserDb(BaseModel):
    name: str
    email: str
    phone_number: str
    is_admin: bool
    password: str


class GetUSerInfo(BaseModel):
    name: str
    email: str
    phone_number: str

class UserLogin(BaseModel):
    email: str
    password: str

