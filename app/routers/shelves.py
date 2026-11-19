from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Book, Shelf, User
from app.schemas import ShelfCreate, ShelfOut, ShelfUpdate

router = APIRouter(prefix="/api/shelves", tags=["shelves"])


def _get_owned_shelf(db: Session, shelf_id: int, owner_id: int) -> Shelf:
    shelf = db.scalar(
        select(Shelf).where(
            Shelf.id == shelf_id,
            Shelf.owner_id == owner_id,
        )
    )
    if shelf is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Полка не найдена",
        )
    return shelf


@router.get("", response_model=list[ShelfOut], summary="Мои полки")
def list_shelves(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Shelf]:
    return list(
        db.scalars(
            select(Shelf)
            .where(Shelf.owner_id == user.id)
            .order_by(Shelf.name.asc())
        ).all()
    )


@router.post(
    "",
    response_model=ShelfOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать полку",
)
def create_shelf(
    payload: ShelfCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Shelf:
    shelf = Shelf(name=payload.name, owner_id=user.id)
    db.add(shelf)
    db.commit()
    db.refresh(shelf)
    return shelf


@router.patch(
    "/{shelf_id}",
    response_model=ShelfOut,
    summary="Переименовать полку",
)
def update_shelf(
    shelf_id: int,
    payload: ShelfUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Shelf:
    shelf = _get_owned_shelf(db, shelf_id, user.id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(shelf, field, value)

    db.commit()
    db.refresh(shelf)
    return shelf


@router.delete(
    "/{shelf_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить полку",
)
def delete_shelf(
    shelf_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    shelf = _get_owned_shelf(db, shelf_id, user.id)

    db.execute(
        update(Book).where(Book.shelf_id == shelf.id).values(shelf_id=None)
    )
    db.delete(shelf)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
