# Movie Recommendation App

A Flask-based movie recommendation web application that helps users discover movies, explore trending titles, browse by genre, save favorites to a wishlist, and view recommendations based on their selected movies.

## Overview

This project is a web application built with Python and Flask. It integrates with the TMDB API to fetch movie data and provides a simple user interface for browsing and discovering content.

## Features

- User registration and login
- Secure password handling
- Movie search functionality
- Trending movie listings
- Genre-based movie browsing
- Detailed movie pages with overview and trailer support
- Wishlist management
- User profile editing
- Recommendation page
- SQLite database storage

## Tech Stack

- Python
- Flask
- Jinja2
- HTML
- CSS
- JavaScript
- SQLite
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- Flask-Migrate
- Requests
- TMDB API

## Project Structure

```text
movie_app/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── static/
│   │   ├── home_style.css
│   │   ├── script.js
│   │   └── style.css
│   └── templates/
│       ├── about.html
│       ├── home.html
│       ├── how_it_works.html
│       ├── index.html
│       ├── movie_details.html
│       ├── movie_genre.html
│       ├── profile.html
│       ├── recommendation.html
│       └── wishlist.html
├── migrations/
├── instance/
├── requirements.txt
├── pyproject.toml
├── run.py
├── README.md
├── .gitignore
└── .venv/
```

## Installation

1. Clone the repository.
2. Navigate to the project folder.
3. Create a virtual environment:

```bash
python -m venv .venv
```

4. Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate
```

5. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the App

Start the application with:

```bash
python run.py
```

Then visit:

```text
http://127.0.0.1:5000/
```

## Configuration

The app uses the TMDB API to fetch movie data. In `app/routes.py`, set your own API key:

```python
TMDB_API_KEY = 'your_api_key_here'
```

## Database

The app uses SQLite with SQLAlchemy. Database tables are created automatically when the app starts.

## Usage

1. Register a new account or log in.
2. Explore the home page for trending movies.
3. Search for a movie by title.
4. Open a movie details page.
5. Add movies to your wishlist.
6. Browse movies by genre.
7. View recommendations and manage your profile.

## License

This project is intended for educational and demonstration purposes.

## Author

Developed using Python and Flask for movie discovery and recommendation.

