# FlimBaaz - Movie Recommender API

This repository contains a **FastAPI-based Movie Recommender System** that provides movie recommendations using a precomputed similarity matrix. It also fetches detailed movie info from the TMDb API.



## Features

- Recommend movies based on a given movie title.
- Fetch additional movie details: poster, summary, rating, genres, release date, runtime, and YouTube trailer link.
- Case-insensitive search with suggestions if the movie is not found.
- Debug endpoints to explore data and available movies.



## Installation

Clone the repository:

```bash
git clone https://github.com/Spiatron/FlimBaaz-Movie-Recommender-API.git
cd FlimBaaz-Movie-Recommender-API
```

Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```



## Files

- `main.py` - FastAPI application with recommendation logic.
- `requirements.txt` - Python dependencies.



## Run the Movie Recommender Notebook:
   - Open the `MovieRecommender.ipynb` file in a Jupyter Notebook environment or within VS Code.
   - Download the dataset from [Kaggle](https://www.kaggle.com/datasets/aayushsoni4/tmdb-6000-movie-dataset-with-ratings).
   - Place the dataset in the specified directory as mentioned in the notebook.
   - Execute the notebook cells to generate the `movie_list.pkl` and `similarity.pkl` files.

## Running the API

```bash
uvicorn main:app --reload
```

- Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
- `/` - API home with available endpoints.
- `/recommend` - POST endpoint to get recommendations.


## API Usage

### **POST /recommend**

**Request Body:**

```json
{
  "movie_title": "The Conjuring",
  "top_n": 5
}
```

**Response:**

```json
{
  "success": true,
  "input_movie": "Insidious",
  "recommendations": [
    {
      "title": "Insidious",
      "similarity_score": 0.381,
      "poster_url": "https://image.tmdb.org/t/p/w500//1egpmVXuXed58TH2UOnX1nATTrf.jpg",
      "summary": "A family discovers that dark spirits have invaded their home after their son inexplicably falls into an endless sleep. When they reach out to a professional for help, they learn things are a lot more personal than they thought.",
      "rating": 6.943,
      "genres": "Horror, Thriller",
      "release_date": "2011-03-31",
      "runtime": "1h 42m",
      "trailer_url": "https://www.youtube.com/watch?v=M-irQA7NIrk"
    },
    .....
  ]
}
```



## TMDb API Key

- The API uses TMDb API to fetch movie details.
- Replace the key in `main.py` with your own TMDb API key for production use:

```python
api_key = "YOUR_TMDB_API_KEY"
```



## Logging

- Logs info and errors for debugging.
- Logs include:
  - Movie list and similarity matrix info
  - Recommendation requests
  - Errors during fetching or processing movie details

---
