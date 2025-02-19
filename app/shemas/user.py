# app/models/user.py
from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

# Кастомный тип для ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Модель пользователя
class User(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    last_name: str
    first_name: str
    group: str
    login: str
    password: str

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "last_name": "Иванов",
                "first_name": "Иван",
                "group": "ИТ1-28",
                "login": "иваиваe73a",
                "password": "2f491847"
            }
        }

# Модель для создания пользователя (без ID)
class UserCreate(BaseModel):
    last_name: str
    first_name: str
    group: str
    login: str
    password: str

# Модель для обновления пользователя (все поля опциональны)
class UserUpdate(BaseModel):
    last_name: Optional[str]
    first_name: Optional[str]
    group: Optional[str]
    login: Optional[str]
    password: Optional[str]