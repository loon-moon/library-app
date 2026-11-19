from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import Book, Genre, Publisher, Shelf, User
from app.schemas import (
    BookCreate,
    BookOut,
    BookStatus,
    BookUpdate,
    GenreStat,
    LibraryStats,
)

router = APIRouter(prefix="/api/books", tags=["books"])

SortField = Literal["created_at", "title", "rating"]
SortOrder = Literal["asc", "desc"]


def _book_select():
    return (
        select(Book)
        .options(
            selectinload(Book.genre),
            selectinload(Book.publisher),
            selectinload(Book.shelf),
        )
        .execution_options(populate_existing=True)
    )


def _get_owned_book(db: Session, book_id: int, owner_id: int) -> Book:
    book = db.scalar(
        _book_select().where(Book.id == book_id, Book.owner_id == owner_id)
    )
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена",
        )
    return book


def _validate_links(db: Session, data: dict, owner_id: int) -> None:
    if "genre_id" in data and data["genre_id"] is not None:
        if db.get(Genre, data["genre_id"]) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Жанр не найден",
            )

    if "publisher_id" in data and data["publisher_id"] is not None:
        if db.get(Publisher, data["publisher_id"]) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Издательство не найдено",
            )

    if "shelf_id" in data and data["shelf_id"] is not None:
        shelf = db.get(Shelf, data["shelf_id"])
        if shelf is None or shelf.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Полка не найдена",
            )


@router.get(
    "/stats",
    response_model=LibraryStats,
    summary="Статистика библиотеки пользователя",
)
def library_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LibraryStats:
    total = (
        db.scalar(
            select(func.count(Book.id)).where(Book.owner_id == user.id)
        )
        or 0
    )
    favorites = (
        db.scalar(
            select(func.count(Book.id)).where(
                Book.owner_id == user.id,
                Book.is_favorite.is_(True),
            )
        )
        or 0
    )

    status_rows = db.execute(
        select(Book.status, func.count(Book.id))
        .where(Book.owner_id == user.id)
        .group_by(Book.status)
    ).all()
    counts = {"want": 0, "reading": 0, "read": 0}
    for book_status, count in status_rows:
        if book_status in counts:
            counts[book_status] = count

    genre_rows = db.execute(
        select(Genre.id, Genre.name, func.count(Book.id))
        .join(Book, Book.genre_id == Genre.id)
        .where(Book.owner_id == user.id)
        .group_by(Genre.id, Genre.name)
        .order_by(func.count(Book.id).desc(), Genre.name.asc())
    ).all()

    return LibraryStats(
        total=total,
        want=counts["want"],
        reading=counts["reading"],
        read=counts["read"],
        favorites=favorites,
        by_genre=[
            GenreStat(genre_id=genre_id, genre_name=name, count=count)
            for genre_id, name, count in genre_rows
        ],
    )


@router.get(
    "",
    response_model=list[BookOut],
    summary="Список книг с поиском, фильтрами и сортировкой",
)
def list_books(
    q: Optional[str] = Query(None, max_length=200, description="Поиск по названию/автору"),
    status_filter: Optional[BookStatus] = Query(None, alias="status"),
    genre_id: Optional[int] = Query(None, ge=1),
    sort: SortField = Query("created_at"),
    order: SortOrder = Query("desc"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Book]:
    stmt = _book_select().where(Book.owner_id == user.id)

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Book.title.ilike(pattern),
                Book.author.ilike(pattern),
                func.py_lower(Book.title).like(func.py_lower(pattern)),
                func.py_lower(Book.author).like(func.py_lower(pattern)),
            )
        )

    if status_filter is not None:
        stmt = stmt.where(Book.status == status_filter)

    if genre_id is not None:
        stmt = stmt.where(Book.genre_id == genre_id)

    if sort == "title":
        column = func.py_lower(Book.title)
        stmt = stmt.order_by(column.asc() if order == "asc" else column.desc())
    elif sort == "rating":
        stmt = stmt.order_by(
            Book.rating.is_(None),
            Book.rating.asc() if order == "asc" else Book.rating.desc(),
        )
    else:
        stmt = stmt.order_by(
            Book.created_at.asc() if order == "asc" else Book.created_at.desc(),
            Book.id.asc() if order == "asc" else Book.id.desc(),
        )

    stmt = stmt.limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


@router.get(
    "/{book_id}",
    response_model=BookOut,
    summary="Одна книга пользователя",
)
def get_book(
    book_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Book:
    return _get_owned_book(db, book_id, user.id)


@router.post(
    "",
    response_model=BookOut,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить книгу",
)
def create_book(
    payload: BookCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Book:
    data = payload.model_dump()
    _validate_links(db, data, user.id)

    book = Book(owner_id=user.id, **data)
    db.add(book)
    db.commit()

    return _get_owned_book(db, book.id, user.id)


@router.patch(
    "/{book_id}",
    response_model=BookOut,
    summary="Частично обновить книгу",
)
def update_book(
    book_id: int,
    payload: BookUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Book:
    book = _get_owned_book(db, book_id, user.id)
    data = payload.model_dump(exclude_unset=True)
    _validate_links(db, data, user.id)

    for field, value in data.items():
        setattr(book, field, value)

    db.commit()
    return _get_owned_book(db, book_id, user.id)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить книгу",
)
def delete_book(
    book_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    book = _get_owned_book(db, book_id, user.id)
    db.delete(book)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
