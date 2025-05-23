from typing import Optional, List
from decimal import Decimal
from datetime import timedelta
import datetime
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    condecimal
)
from enum import Enum


class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]

    total_pages: int
    total_items: int
    next_page: int | None
    prev_page: int | None


class CountrySchema(BaseModel):
    id: int
    name: str | None

    class Config:
        from_attributes = True


class GenreSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActorSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class LanguageSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# Main Movie schema for output (with nested relations)
class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: condecimal(max_digits=15, decimal_places=2)
    revenue: float

    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    class Config:
        from_attributes = True


# For creation or update input (you can choose to just accept IDs for relations)
class MovieCreateUpdateSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: condecimal(max_digits=15, decimal_places=2)
    revenue: float

    country_id: Optional[int]
    country: Optional[str] = None
    genre_ids: Optional[List[str]] = []
    actor_ids: Optional[List[str]] = []
    languages: Optional[List[str]] = []

    class Config:
        from_attributes = True

    @field_validator("name")
    @classmethod
    def name_max_length(cls, v):
        if len(v) > 255:
            raise ValueError("Name must not exceed 255 characters.")
        return v

    @field_validator("date")
    @classmethod
    def date_within_one_year(cls, v):
        if v > datetime.date.today() + timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future.")
        return v

    @field_validator("score")
    @classmethod
    def score_between_0_and_100(cls, v):
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100.")
        return v

    @field_validator("budget")
    @classmethod
    def non_negative_budget(cls, v):
        if v < 0:
            raise ValueError("Budget must be non-negative.")
        return v

    @field_validator("revenue")
    @classmethod
    def non_negative_revenue(cls, v):
        if v < 0:
            raise ValueError("Revenue must be non-negative.")
        return v
