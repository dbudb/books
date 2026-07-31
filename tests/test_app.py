"""Tests for the library routes and database behavior."""

from datetime import date

import pytest

from data_models import Author, Book, db


def add_author(name: str = "Test Author") -> Author:
    """Add an author directly for use in a test."""
    author = Author(name=name, birth_date=None, date_of_death=None)
    db.session.add(author)
    db.session.commit()
    return author


def add_book(title: str, author: Author, isbn: str | None = None) -> Book:
    """Add a book directly for use in a test."""
    book = Book(
        title=title,
        isbn=isbn,
        publication_year=2000,
        author=author,
    )
    db.session.add(book)
    db.session.commit()
    return book


def test_homepage_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Book Alchemy" in response.get_data(as_text=True)


def test_add_author_saves_submitted_values(app, client):
    response = client.post(
        "/add_author",
        data={
            "name": "Octavia E. Butler",
            "birthdate": "1947-06-22",
            "date_of_death": "2006-02-24",
        },
    )

    assert response.status_code == 200
    assert "Author added successfully" in response.get_data(as_text=True)

    with app.app_context():
        author = Author.query.one()
        assert author.name == "Octavia E. Butler"
        assert author.birth_date == date(1947, 6, 22)
        assert author.date_of_death == date(2006, 2, 24)


def test_add_book_connects_selected_author(app, client):
    with app.app_context():
        author_id = add_author("Ursula K. Le Guin").id

    response = client.post(
        "/add_book",
        data={
            "title": "A Wizard of Earthsea",
            "isbn": "9780547773742",
            "publication_year": "1968",
            "author_id": str(author_id),
        },
    )

    assert response.status_code == 200
    assert "Book added successfully" in response.get_data(as_text=True)

    with app.app_context():
        book = Book.query.one()
        assert book.author_id == author_id
        assert book.author.name == "Ursula K. Le Guin"


def test_add_book_rejects_unknown_author(client):
    response = client.post(
        "/add_book",
        data={
            "title": "Unknown Book",
            "isbn": "9780000000001",
            "publication_year": "",
            "author_id": "999",
        },
    )

    assert response.status_code == 400


def test_search_is_partial_and_case_insensitive(app, client):
    with app.app_context():
        author = add_author()
        add_book("Dune", author)
        add_book("Foundation", author)

    response = client.get("/?q=dUN")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Dune" in page
    assert "Foundation" not in page


def test_search_displays_no_match_message(client):
    response = client.get("/?q=does-not-exist")

    assert response.status_code == 200
    assert "No books matched" in response.get_data(as_text=True)


@pytest.mark.parametrize(
    ("sort_by", "first_title", "second_title"),
    [
        ("title_asc", "Alpha", "Zulu"),
        ("title_desc", "Zulu", "Alpha"),
        ("author_asc", "Zulu", "Alpha"),
        ("author_desc", "Alpha", "Zulu"),
    ],
)
def test_sorting(app, client, sort_by, first_title, second_title):
    with app.app_context():
        alpha_author = add_author("Alpha Author")
        beta_author = add_author("Beta Author")
        add_book("Zulu", alpha_author)
        add_book("Alpha", beta_author)

    page = client.get(f"/?sort={sort_by}").get_data(as_text=True)
    first_heading = f'<h2 class="book-title">{first_title}</h2>'
    second_heading = f'<h2 class="book-title">{second_title}</h2>'

    assert page.index(first_heading) < page.index(second_heading)


def test_delete_last_book_also_deletes_author(app, client):
    with app.app_context():
        author = add_author()
        author_id = author.id
        book_id = add_book("Only Book", author).id

    response = client.post(
        f"/book/{book_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "deleted successfully" in response.get_data(as_text=True)

    with app.app_context():
        assert db.session.get(Book, book_id) is None
        assert db.session.get(Author, author_id) is None


def test_delete_one_book_keeps_author_with_other_books(app, client):
    with app.app_context():
        author = add_author()
        author_id = author.id
        deleted_book_id = add_book("First Book", author).id
        remaining_book_id = add_book("Second Book", author).id

    response = client.post(f"/book/{deleted_book_id}/delete")

    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Book, deleted_book_id) is None
        assert db.session.get(Book, remaining_book_id) is not None
        assert db.session.get(Author, author_id) is not None


def test_delete_unknown_book_returns_404(client):
    response = client.post("/book/999/delete")

    assert response.status_code == 404
