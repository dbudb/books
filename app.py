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
    """Display the homepage, shows all books in the library."""
    books = Book.query.all()
    return render_template("home.html", books=books)


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
    publication_year = int(request.form["publication_year"])
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
