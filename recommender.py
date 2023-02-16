import datetime

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
        self.db = st.session_state['db']

        if not self.db:
            self.db = data.get_data()

        st.session_state['db'] = self.db

        self.movies = self.db['movies']
        self.tv = self.db['tv']

        self.liked = self.db['liked']
        self.tv_liked = self.db['tv_liked']

        self.skipped = self.db['skipped']
        self.tv_skipped = self.db['tv_skipped']

        self.query = ''

        st.set_page_config(page_title='Recommender')

        cols = st.columns(4)
        with cols[0]:
            page = st.selectbox('', ['Movies', 'TV', 'Actors', 'Directors', 'Writers'])

        if page == 'Movies':
            with cols[0]:
                self.query, self.start_date, self.end_date, self.min_rating, self.max_rating = self.add_filters()
            self.recommendations('movies', cols)
        if page == 'TV':
            with cols[0]:
                self.query, self.start_date, self.end_date, self.min_rating, self.max_rating = self.add_filters()
            self.recommendations('tv', cols)
        elif page == 'Actors':
            self.actors()
        elif page == 'Directors':
            self.directors()
        elif page == 'Writers':
            self.writers()

    @staticmethod
    def add_filters():
        query = st.text_input('', value='', placeholder="Search", key='query')
        start_year = 1900
        current_year = datetime.date.today().year
        date_range = range(start_year, current_year + 11)
        start_date = st.selectbox('Start Date', date_range)
        end_date = st.selectbox('End Date', date_range, index=current_year - start_year)
        rating_range = range(0, 11)
        min_rating = st.selectbox('Minimum Rating', rating_range)
        max_rating = st.selectbox('Maximum Rating', rating_range, index=10)
        return query, start_date, end_date, min_rating, max_rating

    def actors(self):
        actors = []

        def scan_casts(output, liked, get_item):
            for item_id in liked:
                item = get_item(item_id)
                item_credits = item.get('credits')
                if item_credits:
                    cast = item_credits.get('cast')
                    if cast:
                        output += cast

        scan_casts(actors, self.liked, self._get_movie)
        scan_casts(actors, self.tv_liked, self._get_tv)

        self._people(actors)

    def directors(self):
        self._crew(['Director'])

    def writers(self):
        self._crew(['Writer', 'Screenplay'])

    def _crew(self, jobs):
        people = []

        def scan_crew(output, liked, get_item):
            for item_id in liked:
                item = get_item(item_id)
                item_credits = item.get('credits')
                if item_credits:
                    item_crew = item_credits.get('crew')
                    if item_crew:
                        item_people = [person for person in item_crew if person['job'] in jobs]
                        output += item_people

        scan_crew(people, self.liked, self._get_movie)
        scan_crew(people, self.tv_liked, self._get_tv)

        self._people(people)

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
            if k not in self.liked and k not in self.skipped
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

        return movie

    def _get_tv(self, tv_id):
        tv = self.tv.get(str(tv_id))

        if not tv:
            tv = tmdb.get_tv(tv_id)
            self.tv[str(tv_id)] = tv

        return tv

    def recommendations(self, item_type, cols):
        get_item, get_top_rated, items, like, liked, search_item, skip, skipped = self._setup(
            item_type
        )
        item = self.get_current_item(get_item, get_top_rated, search_item, item_type, items, liked, skipped)
        if item:
            self.add_poster(item, item_type, cols)
            self.add_buttons(like, skip)
        else:
            data.put_data(self.db)

    def _setup(self, item_type):
        if item_type == 'movies':
            return self._get_movie, tmdb.get_movies_top_rated, \
                   self.movies, self.like, self.liked, tmdb.search_movie, self.skip, self.skipped
        elif item_type == 'tv':
            return self._get_tv, tmdb.get_tv_top_rated, \
                   self.tv, self.tv_like, self.tv_liked, tmdb.search_tv, self.tv_skip, self.tv_skipped
        else:
            raise ValueError(f'No such item type: {item_type}')

    def get_current_item(self, get_item, get_top_rated, search_item, item_type, items, liked, skipped):
        recommendations = []
        if self.query:
            results = search_item(self.query)
            results = [result['id'] for result in results]
            results = [result for result in results
                       if result not in liked and result not in skipped]
            if results:
                recommendations = [results[0]]
        else:
            if len(items) < 1:
                items = get_top_rated()
                items = {item['id']: item for item in items[:20]}
                self.db[item_type] = items
            st.session_state['db'] = self.db
            if len(liked) < 1:
                liked = items
            recommendations = self._get_recommendations(get_item, liked, skipped)

        for item_id, score in recommendations:
            item = items.get(item_id, None)
            if not item:
                item = get_item(item_id)
                items[str(item_id)] = item

            print(f"{item.get('title')} ({score})")

            rating = item.get('vote_average', 6)
            release_date = item.get('release_date', item.get('first_air_date', datetime.date.today().year))
            if not release_date:
                release_date = datetime.date.today().year + 1
            year = int(str(release_date)[:4])

            if not item['poster_path']:
                pass
            elif year not in list(range(self.start_date, self.end_date + 1)):
                pass
            elif rating < self.min_rating or rating > self.max_rating:
                pass
            else:
                st.session_state['id'] = item_id
                return item

    @staticmethod
    def add_poster(item, item_type, cols):
        poster_path = item.get('poster_path')
        imdb_id = item.get('imdb_id')
        name = item.get('name')
        with cols[1]:
            if poster_path:
                url = ""
                if item_type == "movies":
                    url = f"https://www.imdb.com/title/{imdb_id}/"
                elif item_type == "tv":
                    url = f"https://www.imdb.com/find?s=tt&q={name}"
                st.markdown(
                    f'<a href="{url}" target="_blank">'
                    f'<img src="{tmdb.POSTER_PREFIX + poster_path}"></a>',
                    unsafe_allow_html=True
                )

    @staticmethod
    def add_buttons(like, skip):
        cols = st.columns(9)
        with cols[4]:
            st.button('👎', on_click=skip)
        with cols[5]:
            st.button('👍', on_click=like)

    @staticmethod
    def _get_recommendations(get_item, liked, skipped):
        recommendations = {}
        for item_id in liked:
            item = get_item(item_id)
            for rec in item.get('recommendations', []):
                if rec in recommendations:
                    recommendations[rec] += 1
                else:
                    recommendations[rec] = 1
        recommendations = [
            (k, v) for k, v in reversed(sorted(recommendations.items(), key=lambda i: i[1]))
            if k not in liked and k not in skipped
        ]
        return recommendations

    def like(self):
        self._button_click('liked')

    def skip(self):
        self._button_click('skipped')

    def tv_like(self):
        self._button_click('tv_liked')

    def tv_skip(self):
        self._button_click('tv_skipped')

    @staticmethod
    def _button_click(item_type):
        db = st.session_state['db']
        db[item_type].append(st.session_state['id'])
        data.put_data(db)
        st.session_state['query'] = ''


Recommender()
