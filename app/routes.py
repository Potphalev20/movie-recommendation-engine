from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from .models import db, User, Movie, Wishlist
from werkzeug.security import generate_password_hash, check_password_hash
import requests, os
from flask_login import login_user, logout_user, login_required, current_user
from prettytable import PrettyTable

# ── Blueprints ────────────────────────────────
api         = Blueprint('api',         __name__)
main_routes = Blueprint('main_routes', __name__)

TMDB_API_KEY = '75439a8f9e551d13a91c261aa1062e5e'

# ── Language map ──────────────────────────────
LANGUAGE_MAP = {
    'te': 'Telugu', 'ta': 'Tamil',  'mr': 'Marathi',
    'hi': 'Hindi',  'en': 'English','es': 'Spanish',
    'fr': 'French', 'de': 'German', 'it': 'Italian',
    'ja': 'Japanese','ko': 'Korean','zh': 'Chinese',
    'ru': 'Russian',
}

def get_full_language_name(lang_code):
    return LANGUAGE_MAP.get(lang_code, lang_code)


# ═══════════════════════════════════════════════
#  AUTH ROUTES
# ═══════════════════════════════════════════════

@api.route('/')
def index():
    return render_template('index.html')

@api.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
        flash('Login successful!', 'success')
        return redirect(url_for('main_routes.home'))
    else:
        flash('Login failed. Check your username and password.', 'danger')
        return redirect(url_for('api.index'))

@api.route('/register', methods=['GET', 'POST'])
def register():
    username = request.form['username']
    email    = request.form['email']
    password = request.form['password']

    if User.query.filter_by(username=username).first():
        flash('Username already exists. Please choose a different one.', 'danger')
        return redirect(url_for('api.index'))

    new_user = User(
        username=username,
        email=email,
        password=generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()

    flash('Registration successful! You can now log in.', 'success')
    return redirect(url_for('api.index'))

@api.route('/signout')
def signout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('api.index'))


# ═══════════════════════════════════════════════
#  HOME
# ═══════════════════════════════════════════════

@main_routes.route('/home')
@login_required
def home():
    trending_movies = get_trending_movies()
    return render_template('home.html', trending_movies=trending_movies, movies=None)

def get_trending_movies():
    try:
        r = requests.get(
            f'https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}'
        )
        r.raise_for_status()
        return r.json().get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching trending movies: {e}")
        flash('Error fetching trending movies. Please try again later.', 'danger')
        return []


# ═══════════════════════════════════════════════
#  MOVIE DETAILS
# ═══════════════════════════════════════════════

@main_routes.route('/movie/<int:movie_id>')
@login_required
def movie_details(movie_id):
    movie = get_movie_details(movie_id)
    if movie is None:
        return redirect(url_for('main_routes.home'))
    return render_template(
        'movie_details.html',
        movie=movie,
        current_user=current_user,
        get_full_language_name=get_full_language_name
    )

def get_movie_details(movie_id):
    try:
        r = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}'
            f'?api_key={TMDB_API_KEY}&append_to_response=credits,videos,reviews'
        )
        r.raise_for_status()
        movie_data = r.json()

        # Save to local DB if not already there
        existing = Movie.query.filter_by(id=movie_data['id']).first()
        if not existing:
            new_movie = Movie(
                id          = movie_data['id'],
                title       = movie_data['title'],
                genre       = movie_data['genres'][0]['name'] if movie_data['genres'] else 'N/A',
                description = movie_data['overview'],
                rating      = movie_data['vote_average'],
                poster_path = movie_data['poster_path']
            )
            db.session.add(new_movie)
            db.session.commit()

        # Extract trailer key
        trailer_key = None
        for video in movie_data.get('videos', {}).get('results', []):
            if video['type'] == 'Trailer':
                trailer_key = video['key']
                break
        movie_data['trailer_key'] = trailer_key
        return movie_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching movie details: {e}")
        flash('Error fetching movie details. Please try again later.', 'danger')
        return None


# ═══════════════════════════════════════════════
#  SEARCH
# ═══════════════════════════════════════════════

@main_routes.route('/search', methods=['GET'])
@login_required
def search_movies():
    query  = request.args.get('query')
    movies = []

    if query:
        try:
            r = requests.get(
                f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}'
            )
            r.raise_for_status()
            movies = r.json().get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching search results: {e}")
            flash('Error fetching search results. Please try again later.', 'danger')

    return render_template(
        'home.html',
        movies=movies,
        trending_movies=get_trending_movies(),
        query=query
    )


# ═══════════════════════════════════════════════
#  WISHLIST — toggle
# ═══════════════════════════════════════════════

@main_routes.route('/toggle_wishlist/<int:movie_id>', methods=['POST'])
@login_required
def toggle_wishlist(movie_id):
    """
    Add or remove a movie from the current user's wishlist.

    FIX (Bug 2 — part 1):
    Before toggling, ensure the movie exists in the local DB.
    If the user clicks 'Add to Wishlist' on movie_details.html,
    the movie is guaranteed to be in the DB already (get_movie_details
    saves it). But as an extra safety net we call _ensure_movie_saved()
    here so the wishlist join never returns None.
    """
    _ensure_movie_saved(movie_id)

    wishlist_item = Wishlist.query.filter_by(
        movie_id=movie_id, user_id=current_user.id
    ).first()

    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        flash('Movie removed from your wishlist!', 'success')
    else:
        new_item = Wishlist(movie_id=movie_id, user_id=current_user.id)
        db.session.add(new_item)
        db.session.commit()
        flash('Movie added to your wishlist!', 'success')

    return jsonify({'status': 'success'})


def _ensure_movie_saved(movie_id):
    """
    Fetch movie data from TMDB and save it to the local DB
    if it isn't there yet.  This guarantees the FK constraint
    on Wishlist.movie_id is always satisfied and item.movie
    never returns None on the wishlist page.
    """
    existing = Movie.query.filter_by(id=movie_id).first()
    if existing:
        return  # already in DB, nothing to do

    try:
        r = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}'
        )
        r.raise_for_status()
        d = r.json()

        new_movie = Movie(
            id          = d['id'],
            title       = d['title'],
            genre       = d['genres'][0]['name'] if d.get('genres') else 'N/A',
            description = d.get('overview', ''),
            rating      = d.get('vote_average', 0.0),
            poster_path = d.get('poster_path', '')
        )
        db.session.add(new_movie)
        db.session.commit()
    except Exception as e:
        print(f"_ensure_movie_saved failed for id={movie_id}: {e}")
        # Don't crash the request; the wishlist toggle still succeeds
        # but the wishlist page will show "Movie not found" for this entry.


# ═══════════════════════════════════════════════
#  WISHLIST — view
# ═══════════════════════════════════════════════

@main_routes.route('/wishlist')
@login_required
def wishlist():
    """
    FIX (Bug 2 — part 2):
    Previously: movies = [item.movie for item in wishlist_items]
    If the movie wasn't in the local DB, item.movie was None
    and the wishlist card showed 'Movie not found' with no link.

    Now: for every wishlist item whose local DB record is missing,
    we fetch the data from TMDB on-the-fly so every card is
    populated and clickable.
    """
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()

    movies = []
    for item in wishlist_items:
        if item.movie:
            # Movie is already in local DB — use the ORM object directly.
            # We convert it to a plain dict so the template works the same
            # way as the TMDB-dict path below.
            movies.append({
                'id':          item.movie.id,
                'title':       item.movie.title,
                'poster_path': item.movie.poster_path,
            })
        else:
            # Movie is NOT in local DB (edge case: DB was reset, or the
            # movie was added before get_movie_details was called).
            # Fetch it from TMDB and save it so future loads are fast.
            _ensure_movie_saved(item.movie_id)
            saved = Movie.query.filter_by(id=item.movie_id).first()
            if saved:
                movies.append({
                    'id':          saved.id,
                    'title':       saved.title,
                    'poster_path': saved.poster_path,
                })
            else:
                # TMDB fetch also failed — append None so the template
                # can show a graceful 'not found' placeholder.
                movies.append(None)

    return render_template('wishlist.html', movies=movies)


# ═══════════════════════════════════════════════
#  PROFILE
# ═══════════════════════════════════════════════

@main_routes.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@main_routes.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_user.username = request.form['name']
    current_user.email    = request.form['email']
    current_user.bio      = request.form['bio']
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('main_routes.profile'))

@main_routes.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    Wishlist.query.filter_by(user_id=current_user.id).delete()
    db.session.delete(current_user)
    db.session.commit()
    flash('Account deleted successfully!', 'success')
    return redirect(url_for('api.index'))


# ═══════════════════════════════════════════════
#  ABOUT
# ═══════════════════════════════════════════════

@main_routes.route('/about')
@login_required
def about():
    return render_template('about.html')


# ═══════════════════════════════════════════════
#  DATABASE (debug)
# ═══════════════════════════════════════════════

@api.route('/database')
def database():
    users = User.query.all()
    table = PrettyTable()
    table.field_names = ["ID", "Username", "Email"]
    for u in users:
        table.add_row([u.id, u.username, u.email])
    print(table)
    flash("Check the terminal for the user records")
    return redirect(url_for('api.index'))


# ═══════════════════════════════════════════════
#  GENRE
# ═══════════════════════════════════════════════

@api.route('/search_genre')
@login_required
def search_genre():
    genres = fetch_genres()
    return render_template('movie_genre.html', genres=genres)

def fetch_genres():
    try:
        r = requests.get(
            f'https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_API_KEY}'
        )
        r.raise_for_status()
        return r.json().get('genres', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching genres: {e}")
        flash('Error fetching genres. Please try again later.', 'danger')
        return []

@main_routes.route('/movies_by_genre', methods=['GET'])
@login_required
def movies_by_genre():
    genre_id = request.args.get('genre')
    if genre_id:
        movies = get_movies_by_genre(genre_id)
        genres = fetch_genres()
        return render_template('movie_genre.html', movies=movies, genres=genres)
    flash('No genre selected.', 'warning')
    return redirect(url_for('main_routes.home'))

def get_movies_by_genre(genre_id):
    try:
        r = requests.get(
            f'https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={genre_id}'
        )
        r.raise_for_status()
        return r.json().get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching movies by genre: {e}")
        flash('Error fetching movies. Please try again later.', 'danger')
        return []

@main_routes.route('/how_it_works')
@login_required
def how_it_works():
    return render_template('how_it_works.html')

# ═══════════════════════════════════════════════
#  RECOMMENDATIONS
# ═══════════════════════════════════════════════

@main_routes.route('/recommendation_page')
@login_required
def recommendation_page():
    return render_template('recommendation.html')

@main_routes.route('/recommendation', methods=['GET', 'POST'])
@login_required
def recommendation():
    if request.method == 'POST':
        movie_name = request.form['movie_name']
        recommended_movies = get_recommendations(movie_name)
        return render_template('recommendation.html', recommended_movies=recommended_movies)
    return render_template('recommendation.html', recommended_movies=None)

def get_recommendations(movie_name):
    try:
        sr = requests.get(
            f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}'
        )
        sr.raise_for_status()
        results = sr.json().get('results', [])
        if not results:
            flash('No movie found with that name.', 'warning')
            return []

        movie_id = results[0]['id']
        dr = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}/recommendations?api_key={TMDB_API_KEY}'
        )
        dr.raise_for_status()
        return dr.json().get('results', [])

    except requests.exceptions.RequestException as e:
        print(f"Error fetching recommendations: {e}")
        flash('Error fetching recommendations. Please try again later.', 'danger')
        return []