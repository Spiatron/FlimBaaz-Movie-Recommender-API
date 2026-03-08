import pickle
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import logging
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Read variables
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
PORT = int(os.getenv("PORT", 8000))
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Allow all origins (for development purposes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the movie list and similarity matrix
try:
    with open('movie_list.pkl', 'rb') as file:
        movie_list = pickle.load(file)
        logger.info(f"Movie list type: {type(movie_list)}")
        
    with open('similarity.pkl', 'rb') as file:
        similarity_matrix = pickle.load(file)
        logger.info(f"Similarity matrix type: {type(similarity_matrix)}")
        logger.info(f"Similarity matrix shape: {similarity_matrix.shape if hasattr(similarity_matrix, 'shape') else 'Unknown'}")

    # Convert to DataFrame if it's not already
    if isinstance(movie_list, pd.DataFrame):
        movies = movie_list
    elif isinstance(movie_list, list):
        movies = pd.DataFrame(movie_list)
    elif isinstance(movie_list, dict):
        movies = pd.DataFrame([movie_list])
    else:
        movies = pd.DataFrame(movie_list)
    
    logger.info(f"Movies DataFrame shape: {movies.shape}")
    logger.info(f"Movies columns: {movies.columns.tolist()}")
    logger.info(f"First few titles: {movies['title'].head(3).tolist() if 'title' in movies.columns else 'No title column'}")
    
except FileNotFoundError as e:
    logger.error(f"Error loading pickle files: {e}")
    movies = pd.DataFrame()
    similarity_matrix = np.array([])
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    movies = pd.DataFrame()
    similarity_matrix = np.array([])

# Function to fetch movie details from TMDb
def fetch_movie_details(movie_id):
    try:
        # TMDb movie details API
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # Fetching poster, summary, rating, genres, release date, and runtime
        poster_path = data.get('poster_path', '')
        poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None
        summary = data.get('overview', 'No summary available.')
        rating = data.get('vote_average', 'No rating available.')
        genres = ', '.join([genre['name'] for genre in data.get('genres', [])])
        release_date = data.get('release_date', 'Unknown release date')
        runtime = data.get('runtime', 'Unknown runtime')
        runtime_str = f"{runtime // 60}h {runtime % 60}m" if isinstance(runtime, int) and runtime else "Unknown"
        
        # Fetching YouTube trailer link
        video_url = None
        videos_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}&language=en-US"
        video_response = requests.get(videos_url, timeout=5)
        video_data = video_response.json()
        for video in video_data.get('results', []):
            if video['site'] == 'YouTube' and video['type'] == 'Trailer':
                video_url = f"https://www.youtube.com/watch?v={video['key']}"
                break
        
        return {
            "poster_url": poster_url,
            "summary": summary,
            "rating": rating,
            "genres": genres,
            "release_date": release_date,
            "runtime": runtime_str,
            "trailer_url": video_url
        }
    except Exception as e:
        logger.error(f"Error fetching details for movie {movie_id}: {e}")
        return {
            "poster_url": None,
            "summary": "Error fetching details",
            "rating": "N/A",
            "genres": "N/A",
            "release_date": "N/A",
            "runtime": "N/A",
            "trailer_url": None
        }

# Request schema
class RecommendationRequest(BaseModel):
    movie_title: str
    top_n: int = 5

# Recommendation logic
@app.post("/recommend")
def recommend(request: RecommendationRequest):
    movie_title = request.movie_title
    top_n = request.top_n
    
    logger.info(f"Recommendation request for: {movie_title}, top_n: {top_n}")
    
    # Check if data is loaded
    if movies.empty:
        return {"success": False, "message": "Movie data not loaded properly!"}
    
    # Check if title column exists
    if 'title' not in movies.columns:
        return {"success": False, "message": "Title column not found in data!", "columns": movies.columns.tolist()}
    
    # Case-insensitive search
    movie_match = movies[movies['title'].str.lower() == movie_title.lower()]
    
    if movie_match.empty:
        # Try partial match for debugging
        similar_titles = movies[movies['title'].str.contains(movie_title, case=False, na=False)]['title'].tolist()[:5]
        return {
            "success": False, 
            "message": f"Movie '{movie_title}' not found!",
            "suggestions": similar_titles if similar_titles else None
        }

    # Find index of the movie
    movie_index = movie_match.index[0]
    logger.info(f"Found movie at index: {movie_index}")

    # Fetch similarity scores
    try:
        if hasattr(similarity_matrix, 'toarray'):  # If sparse matrix
            sim_scores = list(enumerate(similarity_matrix[movie_index].toarray()[0]))
        else:  # If dense array
            sim_scores = list(enumerate(similarity_matrix[movie_index]))
        
        sorted_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n + 1]
        logger.info(f"Found {len(sorted_scores)} recommendations")
    except Exception as e:
        logger.error(f"Error getting similarity scores: {e}")
        return {"success": False, "message": f"Error computing similarities: {e}"}

    # Get recommended movie titles, posters, summaries, ratings, genres, release dates, runtimes, and trailers
    recommended_movies = []
    for i, score in sorted_scores:
        try:
            movie_info = movies.iloc[i]
            
            # Get tmdbId - check different possible column names
            movie_id = None
            for col in ['tmdbId', 'tmdb_id', 'id', 'movie_id']:
                if col in movie_info:
                    movie_id = movie_info[col]
                    break
            
            if movie_id:
                movie_details = fetch_movie_details(movie_id)
            else:
                movie_details = {
                    "poster_url": None,
                    "summary": "No ID available",
                    "rating": "N/A",
                    "genres": "N/A",
                    "release_date": "N/A",
                    "runtime": "N/A",
                    "trailer_url": None
                }
            
            recommended_movies.append({
                'title': movie_info['title'],
                'similarity_score': round(float(score), 3),
                'poster_url': movie_details['poster_url'],
                'summary': movie_details['summary'],
                'rating': movie_details['rating'],
                'genres': movie_details['genres'],
                'release_date': movie_details['release_date'],
                'runtime': movie_details['runtime'],
                'trailer_url': movie_details['trailer_url']
            })
        except Exception as e:
            logger.error(f"Error processing recommendation {i}: {e}")
            continue

    return {
        "success": True, 
        "input_movie": movie_title,
        "recommendations": recommended_movies
    }

@app.get("/")
def root():
    return {
        "message": "Movie Recommender API",
        "endpoints": {
            "POST /recommend": "Get movie recommendations",
        }
    }