from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

BookStatus = Literal["want", "reading", "read"]


def _required_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Поле не может быть пустым")
    return value


def _optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=72)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Логин должен содержать минимум 3 символа")
        if any(ch.isspace() for ch in value):
            raise ValueError("Логин не должен содержать пробелы")
        return value


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=72)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        return value.strip()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class GenreCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _required_text(value)

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: Optional[str]) -> Optional[str]:
        return _optional_text(value)


class GenreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _required_text(value)

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: Optional[str]) -> Optional[str]:
        return _optional_text(value)


class GenreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None


class PublisherCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    city: Optional[str] = Field(None, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _required_text(value)

    @field_validator("city")
    @classmethod
    def clean_city(cls, value: Optional[str]) -> Optional[str]:
        return _optional_text(value)


class PublisherUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    city: Optional[str] = Field(None, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _required_text(value)

    @field_validator("city")
    @classmethod
    def clean_city(cls, value: Optional[str]) -> Optional[str]:
        return _optional_text(value)


class PublisherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: Optional[str] = None


class ShelfCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _required_text(value)


class ShelfUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _required_text(value)


class ShelfOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    status: BookStatus = "want"
    rating: Optional[int] = Field(None, ge=1, le=5)
    pages: Optional[int] = Field(None, ge=1, le=100_000)
    is_favorite: bool = False
    genre_id: Optional[int] = Field(None, ge=1)
    publisher_id: Optional[int] = Field(None, ge=1)
    shelf_id: Optional[int] = Field(None, ge=1)

    @field_validator("title", "author")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _required_text(value)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[BookStatus] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    pages: Optional[int] = Field(None, ge=1, le=100_000)
    is_favorite: Optional[bool] = None
    genre_id: Optional[int] = Field(None, ge=1)
    publisher_id: Optional[int] = Field(None, ge=1)
    shelf_id: Optional[int] = Field(None, ge=1)

    @field_validator("title", "author")
    @classmethod
    def validate_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _required_text(value)


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    status: BookStatus
    rating: Optional[int] = None
    pages: Optional[int] = None
    is_favorite: bool
    created_at: datetime
    owner_id: int
    genre_id: Optional[int] = None
    publisher_id: Optional[int] = None
    shelf_id: Optional[int] = None
    genre: Optional[GenreOut] = None
    publisher: Optional[PublisherOut] = None
    shelf: Optional[ShelfOut] = None


class GenreStat(BaseModel):
    genre_id: Optional[int] = None
    genre_name: str
    count: int


class LibraryStats(BaseModel):
    total: int
    want: int
    reading: int
    read: int
    favorites: int
    by_genre: list[GenreStat]
