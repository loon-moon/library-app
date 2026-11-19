import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY, SESSION_COOKIE_NAME, SESSION_MAX_AGE
from app.routers import auth, books, genres, publishers, shelves
from app.seed import seed

logger = logging.getLogger("libspace")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        seed()
    except SQLAlchemyError:
        logger.warning(
            "Не удалось заполнить справочники. "
            "Сначала выполните: alembic upgrade head"
        )
    yield


app = FastAPI(
    title="LibSpace — Личная библиотека",
    description="Учебный проект: личная библиотека с жанрами, статусами и оценками.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie=SESSION_COOKIE_NAME,
    max_age=SESSION_MAX_AGE,
    same_site="lax",
    https_only=False,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(genres.router)
app.include_router(publishers.router)
app.include_router(shelves.router)


@app.get("/health", tags=["service"], summary="Проверка работоспособности")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def index_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/index.html", include_in_schema=False)
def index_page_alias() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/login", include_in_schema=False)
def login_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/register", include_in_schema=False)
def register_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "register.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)
