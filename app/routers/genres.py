from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Genre, User
from app.schemas import GenreCreate, GenreOut, GenreUpdate

router = APIRouter(prefix="/api/genres", tags=["genres"])


@router.get("", response_model=list[GenreOut], summary="Список жанров")
def list_genres(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Genre]:
    return list(
        db.scalars(select(Genre).order_by(func.py_lower(Genre.name).asc())).all()
    )


@router.post(
    "",
    response_model=GenreOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать жанр",
)
def create_genre(
    payload: GenreCreate,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Genre:
    existing = db.scalar(
        select(Genre).where(func.py_lower(Genre.name) == payload.name.lower())
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Такой жанр уже существует",
        )

    genre = Genre(name=payload.name, description=payload.description)
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre


@router.patch(
    "/{genre_id}",
    response_model=GenreOut,
    summary="Обновить жанр",
)
def update_genre(
    genre_id: int,
    payload: GenreUpdate,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Genre:
    genre = db.get(Genre, genre_id)
    if genre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Жанр не найден",
        )

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        duplicate = db.scalar(
            select(Genre).where(
                func.py_lower(Genre.name) == data["name"].lower(),
                Genre.id != genre_id,
            )
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Такой жанр уже существует",
            )

    for field, value in data.items():
        setattr(genre, field, value)

    db.commit()
    db.refresh(genre)
    return genre


@router.delete(
    "/{genre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить жанр",
)
def delete_genre(
    genre_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    genre = db.get(Genre, genre_id)
    if genre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Жанр не найден",
        )
    db.delete(genre)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
