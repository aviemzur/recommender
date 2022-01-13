import streamlit as st

import data
import tmdb

if 'db' not in st.session_state:
    st.session_state['db'] = {}

if 'id' not in st.session_state:
    st.session_state['id'] = 0

if 'query' not in st.session_state:
    st.session_state['query'] = ''


class Recommender:

    def __init__(self) -> None:
        self.db = data.get_data()

        self.movies = self.db['movies']
        self.tv = self.db['tv']

        self.liked = self.db['liked']
        self.disliked = self.db['disliked']
        self.skipped = self.db['skipped']

        self.tv_liked = self.db['tv_liked']
        self.tv_disliked = self.db['tv_disliked']
        self.tv_skipped = self.db['tv_skipped']

        self.query = ''

        st.set_page_config(page_title='Recommender')

        cols = st.columns(5)
        with cols[2]:
            page = st.selectbox('', ['Movies', 'TV', 'Actors', 'Directors', 'Writers'])

        if page == 'Movies':
            with cols[3]:
                self.query = st.text_input('', value='', placeholder="Search", key='query')
            self.recommendations('movies')
        if page == 'TV':
            with cols[3]:
                self.query = st.text_input('', value='', placeholder="Search", key='query')
            self.recommendations('tv')
        elif page == 'Actors':
            self.actors()
        elif page == 'Directors':
            self.directors()
        elif page == 'Writers':
            self.writers()

    def actors(self):
        actors = []
        for movie_id in self.liked:
            movie = self._get_movie(movie_id)
            movie_credits = movie.get('credits')
            if movie_credits:
                cast = movie_credits.get('cast')
                if cast:
                    actors += cast
        self._people(actors)

    def directors(self):
        self._crew(['Director'])

    def writers(self):
        self._crew(['Writer', 'Screenplay'])

    def _crew(self, jobs):
        directors = []
        for movie_id in self.liked:
            movie = self._get_movie(movie_id)
            movie_credits = movie.get('credits')
            if movie_credits:
                movie_crew = movie_credits.get('crew')
                if movie_crew:
                    movie_directors = [person for person in movie_crew if person['job'] in jobs]
                    directors += movie_directors
        self._people(directors)

    def _people(self, people):
        people_dict = {person['id']: person for person in people}
        people_recommendations = {}
        for person in people:
            person_id = person['id']
            if person_id in people_recommendations:
                people_recommendations[person_id] += 1
            else:
                people_recommendations[person_id] = 1
        people = [
            people_dict.get(k) for k, _ in
            reversed(sorted(people_recommendations.items(), key=lambda item: item[1]))
            if k not in self.liked and k not in self.disliked and k not in self.skipped
        ]
        if len(people) >= 100:
            people = people[:99]
        for person in people:
            name = person['name']
            profile_path = person.get('profile_path')
            profile_src = f'{tmdb.PROFILE_PREFIX}{profile_path}'
            if not profile_path:
                profile_src = 'https://themoviedb.org/assets/2/v4/glyphicons/basic/' + \
                              'glyphicons-basic-4-user-grey-d8fe957375e70239d6abdd549fd75' + \
                              '68c89281b2179b5f4470e2e12895792dfa5.svg'
            image = f'<img style="object-fit: cover;border-radius: 50%;height: 75px;width: 75px;" ' + \
                    f'src="{profile_src}">'
            st.markdown(image +
                        '&nbsp;&nbsp;&nbsp;' +
                        f'<a href="https://www.imdb.com/search/name/?name={name}" target="_blank">{name}</a>',
                        unsafe_allow_html=True)

    def _get_movie(self, movie_id):
        movie = self.movies.get(str(movie_id))

        if not movie:
            movie = tmdb.get_movie(movie_id)
            self.movies[str(movie_id)] = movie
            data.put_data(self.db)

        return movie

    def _get_tv(self, tv_id):
        tv = self.tv.get(str(tv_id))

        if not tv:
            tv = tmdb.get_tv(tv_id)
            self.tv[str(tv_id)] = tv
            data.put_data(self.db)

        return tv

    def recommendations(self, item_type):
        dislike, disliked, get_item, get_top_rated, items, like, liked, search_item, skip, skipped = self._setup(
            item_type
        )
        item = self.get_current_item(get_item, get_top_rated, search_item, item_type, items, liked, disliked, skipped)
        self.add_poster(item)
        self.add_buttons(dislike, like, skip)

    def _setup(self, item_type):
        if item_type == 'movies':
            return self.dislike, self.disliked, self._get_movie, tmdb.get_movies_top_rated, \
                   self.movies, self.like, self.liked, tmdb.search_movie, self.skip, self.skipped
        elif item_type == 'tv':
            return self.tv_dislike, self.tv_disliked, self._get_tv, tmdb.get_tv_top_rated, \
                   self.tv, self.tv_like, self.tv_liked, tmdb.search_tv, self.tv_skip, self.tv_skipped
        else:
            raise ValueError(f'No such item type: {item_type}')

    def get_current_item(self, get_item, get_top_rated, search_item, item_type, items, liked, disliked, skipped):
        recommendations = []
        if self.query:
            results = search_item(self.query)
            results = [result['id'] for result in results]
            results = [result for result in results
                       if result not in liked and result not in disliked and result not in skipped]
            if results:
                recommendations = [results[0]]
        else:
            if len(items) < 1:
                items = get_top_rated()
                items = {item['id']: item for item in items[:20]}
                self.db[item_type] = items
                data.put_data(self.db)
            st.session_state['db'] = self.db
            if len(liked) < 1:
                liked = items
            recommendations = self._get_recommendations(get_item, liked, disliked, skipped)

        for item_id in recommendations:
            item = items.get(item_id, None)
            if not item:
                item = get_item(item_id)
                items[str(item_id)] = item
                data.put_data(self.db)
            if not item['poster_path']:
                pass
            else:
                st.session_state['id'] = item_id
                return item

    @staticmethod
    def add_poster(item):
        poster_path = item.get('poster_path', None)
        imdb_id = item.get('imdb_id', None)
        cols = st.columns(3)
        with cols[1]:
            if poster_path:
                st.markdown(
                    f'<a href="https://www.imdb.com/title/{imdb_id}/" target="_blank">'
                    f'<img src="{tmdb.POSTER_PREFIX + poster_path}" width=300></a>',
                    unsafe_allow_html=True
                )

    @staticmethod
    def add_buttons(dislike, like, skip):
        cols = st.columns(8)
        with cols[3]:
            st.button('👎', on_click=dislike)
        with cols[4]:
            st.button('⏭️', on_click=skip)
        with cols[5]:
            st.button('👍', on_click=like)

    @staticmethod
    def _get_recommendations(get_item, liked, disliked, skipped):
        recommendations = {}
        for item_id in liked:
            item = get_item(item_id)
            for rec in item.get('recommendations', []):
                if rec in recommendations:
                    recommendations[rec] += 1
                else:
                    recommendations[rec] = 1
        for item_id in disliked:
            item = get_item(item_id)
            for rec in item.get('recommendations', []):
                if rec in recommendations:
                    recommendations[rec] -= 1
                else:
                    recommendations[rec] = -1
        for item_id in skipped:
            item = get_item(item_id)
            for rec in item.get('recommendations', []):
                if rec in recommendations:
                    recommendations[rec] -= 0.5
                else:
                    recommendations[rec] = -0.5
        recommendations = [
            k for k, _ in reversed(sorted(recommendations.items(), key=lambda i: i[1]))
            if k not in liked and k not in disliked and k not in skipped
        ]
        return recommendations

    def like(self):
        self._button_click('liked')

    def skip(self):
        self._button_click('skipped')

    def dislike(self):
        self._button_click('disliked')

    def tv_like(self):
        self._button_click('tv_liked')

    def tv_skip(self):
        self._button_click('tv_skipped')

    def tv_dislike(self):
        self._button_click('tv_disliked')

    @staticmethod
    def _button_click(item_type):
        db = st.session_state['db']
        db[item_type].append(st.session_state['id'])
        data.put_data(db)
        st.session_state['query'] = ''


Recommender()
