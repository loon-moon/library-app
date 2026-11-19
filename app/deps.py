from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

SESSION_USER_KEY = "user_id"


def login_session(request: Request, user_id: int) -> None:
    request.session[SESSION_USER_KEY] = user_id


def logout_session(request: Request) -> None:
    request.session.clear()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user_id = request.session.get(SESSION_USER_KEY)
    if not isinstance(user_id, int):
        raise _unauthorized()

    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise _unauthorized()
    return user


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не авторизован",
        headers={"WWW-Authenticate": "Cookie"},
    )
