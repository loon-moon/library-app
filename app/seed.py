from sqlalchemy import select

from app.database import SessionLocal
from app.models import Genre, Publisher

GENRES = [
    ("Фантастика", "Научная фантастика и космос"),
    ("Фэнтези", "Магия, миры и приключения"),
    ("Детектив", "Расследования и тайны"),
    ("Роман", "Классика и современная проза"),
    ("Нон-фикшн", "Документальная литература"),
    ("Психология", "Книги о человеке и отношениях"),
    ("История", "Исторические исследования"),
    ("Поэзия", "Стихотворные сборники"),
]

PUBLISHERS = [
    ("Эксмо", "Москва"),
    ("АСТ", "Москва"),
    ("Питер", "Санкт-Петербург"),
    ("Азбука", "Санкт-Петербург"),
    ("МИФ", "Москва"),
]


def seed() -> None:
    db = SessionLocal()
    try:
        if db.scalar(select(Genre.id).limit(1)) is None:
            db.add_all(
                Genre(name=name, description=description)
                for name, description in GENRES
            )

        if db.scalar(select(Publisher.id).limit(1)) is None:
            db.add_all(
                Publisher(name=name, city=city)
                for name, city in PUBLISHERS
            )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Seed OK")
