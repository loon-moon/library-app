from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, login_session, logout_session
from app.models import User
from app.schemas import UserCreate, UserLogin, UserOut
from app.security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _find_by_username(db: Session, username: str) -> User | None:
    return db.scalar(
        select(User).where(func.py_lower(User.username) == username.lower())
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
)
def register(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    if _find_by_username(db, payload.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким логином уже существует",
        )

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    login_session(request, user.id)
    return user


@router.post(
    "/login",
    response_model=UserOut,
    summary="Вход по логину и паролю",
)
def login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user = _find_by_username(db, payload.username)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Cookie"},
        )

    login_session(request, user.id)
    return user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из аккаунта",
)
def logout(request: Request) -> Response:
    logout_session(request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Текущий пользователь",
)
def me(user: User = Depends(get_current_user)) -> User:
    return user
