from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Author(db.Model):
    """An author stored in the library."""
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)  # pretty sure there are Authors whos birthdate is not know
    date_of_death = db.Column(db.Date, nullable=True)

    books = db.relationship("Book", back_populates="author")

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"ID: {self.id}, Name: {self.name}, Birth: {self.birth_date}, Death: {self.date_of_death}"


class Book(db.Model):
    """A book stored in the library."""
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=True)
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.Integer, nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)

    author = db.relationship("Author", back_populates="books")

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"ID: {self.id}, Title: {self.title}, "
