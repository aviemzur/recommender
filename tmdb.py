import json
import os

import requests

API_KEY_FILE_NAME = 'API_KEY'

if not os.path.exists(API_KEY_FILE_NAME):
    open(API_KEY_FILE_NAME, 'a').close()

with open(API_KEY_FILE_NAME) as f:
    _API_KEY = f.read().strip()

API_KEY = f'?api_key={_API_KEY}'
API = 'https://api.themoviedb.org/3'

POSTER_PREFIX = 'https://www.themoviedb.org/t/p/w400/'
PROFILE_PREFIX = 'https://www.themoviedb.org/t/p/w200/'


def search_movie(query):
    print(f'search_movie()')
    return _get(f'/search/movie', query=query).get('results', [])


def search_tv(query):
    print(f'search_tv()')
    return _get(f'/search/tv', query=query).get('results', [])


def get_movie(movie_id):
    print(f'get_movie({movie_id})')
    movie = _get(f'/movie/{movie_id}')
    movie['recommendations'] = get_movie_recommendations(movie['id'])
    movie['credits'] = get_movie_credits(movie['id'])
    return movie


def get_tv(tv_id):
    print(f'get_tv({tv_id})')
    tv = _get(f'/tv/{tv_id}')
    if 'id' in tv:
        tv['recommendations'] = get_tv_recommendations(tv['id'])
        tv['credits'] = get_tv_credits(tv['id'])
    else:
        tv['recommendations'] = []
        tv['credits'] = {}
    return tv


def get_movie_recommendations(movie_id):
    print(f'get_movie_recommendations({movie_id})')
    recommendations = _get(f'/movie/{movie_id}/recommendations').get('results', [])
    return [recommendation['id'] for recommendation in recommendations]


def get_tv_recommendations(tv_id):
    print(f'get_tv_recommendations({tv_id})')
    recommendations = _get(f'/tv/{tv_id}/recommendations').get('results', [])
    return [recommendation['id'] for recommendation in recommendations]


def get_movie_credits(movie_id):
    print(f'get_movie_credits({movie_id})')
    return _get(f'/movie/{movie_id}/credits')


def get_tv_credits(tv_id):
    print(f'get_tv_credits({tv_id})')
    return _get(f'/tv/{tv_id}/credits')


def get_movies_top_rated():
    print(f'get_movies_top_rated()')
    movies = _get(f'/movie/top_rated').get('results', [])
    for movie in movies:
        movie['recommendations'] = get_movie_recommendations(movie['id'])
    return movies


def get_tv_top_rated():
    print(f'get_tv_top_rated()')
    tv = _get(f'/tv/top_rated').get('results', [])
    for show in tv:
        show['recommendations'] = get_tv_recommendations(show['id'])
    return tv


def _get(path, **kwargs):
    url = f'{API}{path}{API_KEY}'
    for k, v in kwargs.items():
        url += f'&{k}={v}'
    res = requests.get(url)
    return json.loads(res.content)


pass
