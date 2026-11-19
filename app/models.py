from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    shelves: Mapped[list["Shelf"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    books: Mapped[list["Book"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Shelf(Base):
    __tablename__ = "shelves"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    owner: Mapped["User"] = relationship(back_populates="shelves")
    books: Mapped[list["Book"]] = relationship(back_populates="shelf")


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    books: Mapped[list["Book"]] = relationship(back_populates="genre")


class Publisher(Base):
    __tablename__ = "publishers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    books: Mapped[list["Book"]] = relationship(back_populates="publisher")


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint(
            "status IN ('want', 'reading', 'read')",
            name="ck_books_status",
        ),
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="ck_books_rating",
        ),
        CheckConstraint(
            "pages IS NULL OR pages > 0",
            name="ck_books_pages",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="want", nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    genre_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("genres.id", ondelete="SET NULL"), nullable=True
    )
    publisher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("publishers.id", ondelete="SET NULL"), nullable=True
    )
    shelf_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("shelves.id", ondelete="SET NULL"), nullable=True
    )

    owner: Mapped["User"] = relationship(back_populates="books")
    genre: Mapped[Optional["Genre"]] = relationship(back_populates="books")
    publisher: Mapped[Optional["Publisher"]] = relationship(back_populates="books")
    shelf: Mapped[Optional["Shelf"]] = relationship(back_populates="books")