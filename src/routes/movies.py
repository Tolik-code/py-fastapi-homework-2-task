from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status
)
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, MovieModel
from schemas import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateUpdateSchema
)
from pydantic import BaseModel, conint
import math
from sqlalchemy.orm import selectinload


router = APIRouter()


class PaginationParams(BaseModel):
    page: conint(ge=1) = 1
    per_page: conint(ge=1, le=20) = 10


async def get_film_or_404(db: AsyncSession, film_id: int):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == film_id)
    )
    film = result.scalar_one_or_none()
    if not film:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return film


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    params: PaginationParams = Depends(), db: AsyncSession = Depends(get_db)
):
    page, per_page = params.page, params.per_page
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset).limit(per_page)
    )
    films = result.scalars().all()

    if not films:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_result = await db.execute(select(func.count(MovieModel.id)))
    total = total_result.scalar()

    total_pages = math.ceil(total / per_page)
    next_page = None if page >= total_pages else page + 1
    prev_page = page - 1 if page > 1 else None

    return MovieListResponseSchema(
        movies=films,
        total_pages=total_pages,
        total_items=total,
        next_page=next_page,
        prev_page=prev_page,
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema
)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    film = await get_film_or_404(db, movie_id)
    return film


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED
)
async def add_film(
        film: MovieCreateUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    existing_movie = await db.execute(
        select(MovieModel).where(
            MovieModel.name == film.name, MovieModel.date == film.date
        )
    )
    if existing_movie.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=(
                "Movie with the same name"
                " and date already exists."
            )
        )

    new_film = MovieModel(**film.dict())
    db.add(new_film)
    await db.commit()
    await db.refresh(new_film)

    return new_film


@router.patch("/movies/{film_id}", response_model=MovieDetailSchema)
async def edit_film(
    film_id: int, film: MovieCreateUpdateSchema, db: AsyncSession = Depends(get_db)
):
    db_film = await get_film_or_404(db, film_id)
    film_data = film.dict(exclude_unset=True)

    model_columns = {col.key for col in MovieModel.__table__.columns}
    for key, value in film_data.items():
        if key in model_columns:
            setattr(db_film, key, value)

    await db.commit()
    await db.refresh(db_film)
    return db_film


@router.delete("/movies/{film_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_film(film_id: int, db: AsyncSession = Depends(get_db)):
    db_film = await get_film_or_404(db, film_id)
    await db.delete(db_film)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
