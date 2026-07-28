import os
from data_models import db, Author, Book
from flask import Flask, render_template, request
from datetime import date

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"sqlite:///{os.path.join(basedir, 'data', 'library.sqlite')}"
)

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/add_author", methods=["GET", "POST"])
def add_author():
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


"""@app.route("/add_book")
def add_book():
    return render_template("add_book.html")"""

if __name__ == "__main__":
    app.run(debug=True)
