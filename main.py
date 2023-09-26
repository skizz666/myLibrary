from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from typing import Callable
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import json
import os

TMDB_URL = "https://api.themoviedb.org"
TMDB_API_KEY = os.getenv("TMDB_PASS")
TMDB_API_TOKEN = os.getenv("TMDB_TOKEN")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_PASS")
app.config['SQLALCHEMY_DATABASE_URI'] = \
    "sqlite:///G:/PyCharm Community Edition 2022.1/PycharmProjects/Movie_Project/movie-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Bootstrap(app)


class MySQLAlchemy(SQLAlchemy):
    Column: Callable
    String: Callable
    Integer: Callable
    Float: Callable


db = MySQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(250), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


class NMovie:
    def __init__(self, title, release_date, movie_id):
        self.title = title
        self.release_date = release_date
        self.movie_id = movie_id


class RateMovieForm(FlaskForm):
    movie_rating = StringField(label="Neue Bewertung",
                               validators=[DataRequired(message="Bitte die neue Bewertung eingeben.")])
    movie_review = StringField(label="Neue Review",
                               validators=[DataRequired(message="Bitte eine neue Review eingeben.")])
    submit_btn = SubmitField(label="Bewertung ändern")


class AddMovieForm(FlaskForm):
    movie_name = StringField(label="Neuer Film",
                             validators=[DataRequired(message="Bitte den Namen des Films eingeben.")])
    submit_btn = SubmitField(label="Film hinzufügen")


all_movies = []


def rate_movies():
    query = db.session.query(Movie).order_by(Movie.rating.desc())
    count = 0
    for i in query:
        count += 1
        movie = Movie.query.get(i.id)
        movie.ranking = count
        db.session.commit()


@app.route("/")
def home():
    movies = db.session.query(Movie).order_by(Movie.rating.desc())
    return render_template("index.html", movies=movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    id_to_change = request.args.get('id_to_change')
    if request.method == "GET":
        movie = Movie.query.get(id_to_change)
        return render_template('edit.html', movie=movie, form=form)
    if form.validate_on_submit():
        new_rating = form.movie_rating.data
        new_review = form.movie_review.data
        movie = Movie.query.get(id_to_change)
        movie.rating = new_rating
        movie.review = new_review
        db.session.commit()
        rate_movies()
        return redirect(url_for('home'))


@app.route("/delete_movie")
def delete_movie():
    id_to_delete = request.args.get("id_to_delete")
    movie = Movie.query.get(id_to_delete)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add_movie", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    if request.method == "GET":
        return render_template('add.html', form=form)
    if form.validate_on_submit():
        new_movie_name = form.movie_name.data
        new_movie_name = new_movie_name.replace(" ", "+")
        response = requests.get(f"{TMDB_URL}/3/search/movie?api_key={TMDB_API_KEY}&query={new_movie_name}")
        data = json.loads(response.text)
        list_of_movies = []
        for movie in data['results']:
            new_movie = NMovie(
                title=movie["title"],
                release_date=movie["release_date"],
                movie_id=movie['id']
            )
            list_of_movies.append(new_movie)
        return render_template('select.html', movies_list=list_of_movies)


@app.route("/select_movie", methods=["GET", "POST"])
def select_movie():
    id_of_movie = request.args.get("id_of_movie")
    response = requests.get(f"{TMDB_URL}/3/movie/{id_of_movie}?api_key={TMDB_API_KEY}&language=de-DE")
    data = json.loads(response.text)
    entry = Movie(id=id_of_movie,
                  title=data["title"],
                  year=data["release_date"],
                  description=data["overview"],
                  rating="0",
                  ranking="0",
                  review="blank",
                  img_url=f"https://image.tmdb.org/t/p/w500/{data['poster_path']}",
                  )
    db.session.add(entry)
    db.session.commit()
    return redirect(url_for('edit', id_to_change=id_of_movie))


if __name__ == '__main__':
    app.run(debug=True)
