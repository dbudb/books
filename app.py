import os
from data_models import db, Author, Book
from flask import Flask, flash, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue

from datetime import date

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URI",
    f"sqlite:///{os.path.join(basedir, 'data', 'library.sqlite')}",
)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "book-alchemy-local-secret",
)

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def index() -> ResponseReturnValue:
    """Display books matching the search and sorting choices."""
    search_term = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "title_asc")
    query = Book.query

    if search_term:
        query = query.filter(Book.title.ilike(f"%{search_term}%"))

    if sort_by == "title_desc":
        query = query.order_by(Book.title.desc())
    elif sort_by == "author_asc":
        query = query.join(Author).order_by(Author.name, Book.title)
    elif sort_by == "author_desc":
        query = query.join(Author).order_by(
            Author.name.desc(),
            Book.title,
        )
    else:
        sort_by = "title_asc"
        query = query.order_by(Book.title)

    books = query.all()
    return render_template(
        "home.html",
        books=books,
        current_sort=sort_by,
        search_term=search_term,
    )


@app.route("/add_author", methods=["GET", "POST"])
def add_author() -> ResponseReturnValue:
    """Display the author form or save a submitted author."""
    if request.method == "GET":
        return render_template("add_author.html")
    name = request.form["name"]
    birth_date = date.fromisoformat(request.form["birthdate"])
    death_text = request.form["date_of_death"]
    death_date = date.fromisoformat(death_text) if death_text else None
    author = Author(
        name=name,
        birth_date=birth_date,
        date_of_death=death_date,
    )

    db.session.add(author)
    db.session.commit()
    return render_template("add_author.html", message="Author added successfully")


@app.route("/add_book", methods=["GET", "POST"])
def add_book() -> ResponseReturnValue:
    """Display the book form or save a submitted book."""
    if request.method == "GET":
        authors = Author.query.all()
        return render_template("add_book.html", authors=authors)
    title = request.form["title"]
    isbn = request.form["isbn"]
    publication_text = request.form["publication_year"]
    publication_year = int(publication_text) if publication_text else None
    author_id = int(request.form["author_id"])
    author = db.session.get(Author, author_id)
    if author is None:
        return "Author does not exist", 400

    book = Book(
        title=title,
        isbn=isbn,
        publication_year=publication_year,
        author=author
    )

    db.session.add(book)
    db.session.commit()
    return render_template("add_book.html", message="Book added successfully")


@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id: int) -> ResponseReturnValue:
    """Delete a book and its author when the author has no other books."""
    book = db.session.get(Book, book_id)
    if book is None:
        return "Book does not exist", 404

    author = book.author
    title = book.title
    author_has_other_books = Book.query.filter(
        Book.author_id == author.id,
        Book.id != book.id,
    ).first() is not None

    db.session.delete(book)
    if not author_has_other_books:
        db.session.delete(author)

    db.session.commit()
    flash(f'"{title}" deleted successfully.')
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
