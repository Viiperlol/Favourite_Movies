from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

MOVIE_API_KEY = "02b2e2217debd7d354856c75efbec078"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

headers = {"accept": "application/json",
           "Authorization": "Bearer 02b2e2217debd7d354856c75efbec078"}

# CREATE DB
class Base(DeclarativeBase):
    pass

# Create local db file
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
# Create the extension
db = SQLAlchemy(model_class=Base)
# initialise the app with the extension
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

class RateMovieForm(FlaskForm):
    new_rating = StringField("Your rating out of 10", validators=[DataRequired()])
    new_review = StringField("Your review")
    submit = SubmitField("Submit", validators=[DataRequired()])

class AddMovie(FlaskForm):
    movie_title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Submit")

# ----- SAMPLE DB DATA -----
# new_movie = Movie(
#     title="Oppenheimer",
#     year=2023,
#     description="During World War II, Lt. Gen. Leslie Groves Jr. "
#                 "appoints physicist J. Robert Oppenheimer to work "
#                 "on the top-secret Manhattan Project. Oppenheimer "
#                 "and a team of scientists spend years developing and "
#                 "designing the atomic bomb. Their work comes to "
#                 "fruition on July 16, 1945, as they witness the world's "
#                 "first nuclear explosion, forever changing the course of history.",
#     rating=8.3,
#     ranking=1,
#     review="One of the greatest biopic films of the century",
#     img_url="https://www.hollywoodreporter.com/wp-content/uploads/2022/07/Oppenheimer-Movie-Poster-Universal-Publicity-EMBED-2022-.jpg"
# )
#
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()
#
# second_movie = Movie(
#     title="Interstellar",
#     year=2014,
#     description="When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, "
#                 "Joseph Cooper, is tasked to pilot a spacecraft, along with a team of researchers, "
#                 "to find a new planet for humans.",
#     rating=8.7,
#     ranking=2,
#     review="Beautifully explained the concept of time and space in an entertaining manner",
#     img_url="https://s3.amazonaws.com/nightjarprod/content/uploads/sites/130/2021/08/19085635/gEU2QniE6E77NI6lCU6MxlNBvIx-scaled.jpg"
# )
#
# with app.app_context():
#     db.session.add(second_movie)
#     db.session.commit()


@app.route("/", methods=["GET", "POST"])
def home():
    result = db.session.execute(db.select(Movie))
    all_movies = result.scalars().all()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.new_rating.data)
        if form.new_review.data == "":
            movie.review = movie.review
        else:
            movie.review = form.new_review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form)


@app.route("/delete", methods=["GET", "POST"])
def delete():
    movie_id = int(request.args.get("id"))
    movie_to_delete = db.get_or_404(Movie, movie_id)
    if movie_to_delete:
        db.session.delete(movie_to_delete)
        db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        movie_title = form.movie_title.data

        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_API_KEY, "query": movie_title})
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()

        # Redirect to /edit route
        return redirect(url_for("rate_movie", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
