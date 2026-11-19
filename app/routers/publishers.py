from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Publisher, User
from app.schemas import PublisherCreate, PublisherOut, PublisherUpdate

router = APIRouter(prefix="/api/publishers", tags=["publishers"])


@router.get("", response_model=list[PublisherOut], summary="Список издательств")
def list_publishers(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Publisher]:
    return list(
        db.scalars(select(Publisher).order_by(Publisher.name.asc())).all()
    )


@router.post(
    "",
    response_model=PublisherOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать издательство",
)
def create_publisher(
    payload: PublisherCreate,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Publisher:
    publisher = Publisher(name=payload.name, city=payload.city)
    db.add(publisher)
    db.commit()
    db.refresh(publisher)
    return publisher


@router.patch(
    "/{publisher_id}",
    response_model=PublisherOut,
    summary="Обновить издательство",
)
def update_publisher(
    publisher_id: int,
    payload: PublisherUpdate,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Publisher:
    publisher = db.get(Publisher, publisher_id)
    if publisher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Издательство не найдено",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(publisher, field, value)

    db.commit()
    db.refresh(publisher)
    return publisher


@router.delete(
    "/{publisher_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить издательство",
)
def delete_publisher(
    publisher_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    publisher = db.get(Publisher, publisher_id)
    if publisher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Издательство не найдено",
        )
    db.delete(publisher)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
