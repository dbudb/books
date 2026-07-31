import os
from data_models import db, Author, Book
from flask import Flask, render_template, request
from flask.typing import ResponseReturnValue

from datetime import date

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"sqlite:///{os.path.join(basedir, 'data', 'library.sqlite')}"
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


if __name__ == "__main__":
    app.run(debug=True)
