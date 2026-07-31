"""Seed the library with books from the Open Library Search API."""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app import app
from data_models import Author, Book, db


TARGET_BOOKS = 100
SEARCH_URL = "https://openlibrary.org/search.json"


def fetch_books() -> list[dict]:
    """Fetch a random batch of English-language books with ISBNs."""
    query = urlencode(
        {
            "q": "language:eng AND isbn:*",
            "fields": "title,author_name,isbn,first_publish_year,cover_i",
            "sort": "random",
            "limit": 300,
        }
    )
    request = Request(
        f"{SEARCH_URL}?{query}",
        headers={"User-Agent": "book-alchemy-learning-project/1.0"},
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)["docs"]


def choose_isbn(isbns: list[str]) -> str | None:
    """Prefer an ISBN-13, otherwise use the first available ISBN."""
    cleaned = [isbn.replace("-", "").strip() for isbn in isbns if isbn.strip()]
    return next((isbn for isbn in cleaned if len(isbn) == 13), cleaned[0] if cleaned else None)


def seed() -> None:
    """Add up to 100 new books and their authors to the database."""
    documents = fetch_books()

    with app.app_context():
        authors_by_name = {author.name: author for author in Author.query.all()}
        known_isbns = {
            isbn
            for (isbn,) in db.session.query(Book.isbn)
            .filter(Book.isbn.isnot(None))
            .all()
        }
        added = 0

        for document in documents:
            author_names = document.get("author_name", [])
            isbn = choose_isbn(document.get("isbn", []))
            title = document.get("title")

            if (
                not title
                or not author_names
                or not isbn
                or not document.get("cover_i")
                or isbn in known_isbns
            ):
                continue

            author_name = author_names[0]
            author = authors_by_name.get(author_name)
            if author is None:
                author = Author(
                    name=author_name,
                    birth_date=None,
                    date_of_death=None,
                )
                db.session.add(author)
                authors_by_name[author_name] = author

            book = Book(
                title=title,
                isbn=isbn,
                publication_year=document.get("first_publish_year"),
                author=author,
            )
            db.session.add(book)
            known_isbns.add(isbn)
            added += 1

            if added == TARGET_BOOKS:
                break

        db.session.commit()
        print(f"Added {added} books.")


if __name__ == "__main__":
    seed()
