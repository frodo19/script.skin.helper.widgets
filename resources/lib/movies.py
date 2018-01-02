#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    script.skin.helper.widgets
    movies.py
    all movies widgets provided by the script
'''

from utils import create_main_entry, KODI_VERSION
from operator import itemgetter
from metadatautils import kodi_constants
from random import randint
import xbmc


class Movies(object):
    '''all movie widgets provided by the script'''

    def __init__(self, addon, metadatautils, options):
        '''Initializations pass our common classes and the widget options as arguments'''
        self.metadatautils = metadatautils
        self.addon = addon
        self.options = options

    def listing(self):
        '''main listing with all our movie nodes'''
        tag = self.options.get("tag", "")
        if tag:
            label_prefix = "%s - " % tag
        else:
            label_prefix = ""
        icon = "DefaultMovies.png"
        all_items = [
            (label_prefix + self.addon.getLocalizedString(32028), "inprogress&mediatype=movies&tag=%s" % tag, icon),
            (label_prefix + self.addon.getLocalizedString(32038), "recent&mediatype=movies&tag=%s" % tag, icon),
            (label_prefix + self.addon.getLocalizedString(32003), "recommended&mediatype=movies&tag=%s" % tag, icon),
            (label_prefix + self.addon.getLocalizedString(32029),
                "inprogressandrecommended&mediatype=movies&tag=%s" % tag, icon),
            (label_prefix + self.addon.getLocalizedString(32048), "random&mediatype=movies&tag=%s" % tag, icon),
            (label_prefix + self.addon.getLocalizedString(32066), "unwatched&mediatype=movies&tag=%s" % tag, icon),
            (label_prefix + self.addon.getLocalizedString(32046), "top250&mediatype=movies&tag=%s" % tag, icon),
            (label_prefix + xbmc.getLocalizedString(135),
                "browsegenres&mediatype=movies&tag=%s" % tag, "DefaultGenres.png")
        ]
        if not tag:
            all_items += [
                (self.addon.getLocalizedString(32006), "similar&mediatype=movies&tag=%s" % tag, icon),
                (xbmc.getLocalizedString(10134), "favourites&mediatype=movies&tag=%s" % tag, icon),
                (xbmc.getLocalizedString(20459), "tagslisting&mediatype=movies", icon)
            ]
        return self.metadatautils.process_method_on_list(create_main_entry, all_items)

    def tagslisting(self):
        '''get tags listing'''
        all_items = []
        for item in self.metadatautils.kodidb.files("videodb://movies/tags"):
            details = (item["label"], "listing&mediatype=movies&tag=%s" % item["label"], "DefaultTags.png")
            all_items.append(create_main_entry(details))
        return all_items

    def recommended(self):
        ''' get recommended movies - library movies with score higher than 7 '''
        filters = [kodi_constants.FILTER_RATING]
        if self.options["hide_watched"]:
            filters.append(kodi_constants.FILTER_UNWATCHED)
        if self.options.get("tag"):
            filters.append({"operator": "contains", "field": "tag", "value": self.options["tag"]})
        return self.metadatautils.kodidb.movies(sort=kodi_constants.SORT_RATING, filters=filters,
                                           limits=(0, self.options["limit"]))

    def recent(self):
        ''' get recently added movies '''
        filters = []
        if self.options["hide_watched"]:
            filters.append(kodi_constants.FILTER_UNWATCHED)
        if self.options.get("tag"):
            filters.append({"operator": "contains", "field": "tag", "value": self.options["tag"]})
        return self.metadatautils.kodidb.movies(sort=kodi_constants.SORT_DATEADDED, filters=filters,
                                           limits=(0, self.options["limit"]))

    def random(self):
        ''' get random movies '''
        filters = []
        if self.options["hide_watched"]:
            filters.append(kodi_constants.FILTER_UNWATCHED)
        if self.options.get("tag"):
            filters.append({"operator": "contains", "field": "tag", "value": self.options["tag"]})
        return self.metadatautils.kodidb.movies(sort=kodi_constants.SORT_RANDOM, filters=filters,
                                           limits=(0, self.options["limit"]))

    def inprogress(self):
        ''' get in progress movies '''
        filters = [kodi_constants.FILTER_INPROGRESS]
        if self.options.get("tag"):
            filters.append({"operator": "contains", "field": "tag", "value": self.options["tag"]})
        return self.metadatautils.kodidb.movies(sort=kodi_constants.SORT_LASTPLAYED, filters=filters,
                                           limits=(0, self.options["limit"]))

    def unwatched(self):
        ''' get unwatched movies '''
        filters = [kodi_constants.FILTER_UNWATCHED]
        if self.options.get("tag"):
            filters.append({"operator": "contains", "field": "tag", "value": self.options["tag"]})
        return self.metadatautils.kodidb.movies(sort=kodi_constants.SORT_TITLE, filters=filters,
                                           limits=(0, self.options["limit"]))

    def similar(self, imdb_id=None):
        ''' get similar movies for given imdbid, or from a recently watched title if no imdbid'''
        all_items = []
        all_titles = list()
        ref_movie = None
        hide_watched = False
        if not imdb_id:
            # check options if imdb_id argument not given
            imdb_id = self.options.get("imdbid", "")
        if imdb_id:
            # get movie from imdb_id if found
            ref_movie = self.metadatautils.kodidb.movie_by_imdbid(imdb_id)
        if not ref_movie:
            # pick a random recently watched movie (for homescreen widget)
            ref_movie = self.get_recently_watched_movie()
            # use hide_watched setting for homescreen widget only
            hide_watched = self.options["hide_watched_similar"]
        if ref_movie:
            # define ref_movie properties for clarity & speed
            ref_title = ref_movie["title"]
            ref_genres = ref_movie["genre"]
            ref_directors = ref_movie["director"]
            ref_writers = ref_movie["writer"]
            ref_rating = ref_movie["rating"]
            ref_setid = ref_movie["setid"]
            ref_year = ref_movie["year"]
            set_genres = set(ref_genres)
            set_directors = set(ref_directors)
            set_writers = set(ref_writers)
            # check every genre for the movie
            for genre in ref_genres:
                # check every movie for the genre
                genre_movies = self.forgenre(genre=genre, hide_watched=hide_watched, limit=1000, sort=False)
                for item in genre_movies:
                    # prevent duplicates so skip reference movie and titles already in the list
                    if not item["title"] in all_titles and not item["title"] == ref_title:
                        # [feature]_score = (numer of matching [features]) / (number of unique [features] between both)
                        genre_score = float(len(set_genres.intersection(item["genre"])))/ \
                            len(set_genres.union(set(item["genre"])))
                        director_score = 0 if len(ref_directors)==0 else \
                            float(len(set_directors.intersection(item["director"])))/ \
                            len(set_directors.union(set(item["director"])))
                        writer_score = 0 if len(ref_writers)==0 else \
                            float(len(set_writers.intersection(item["writer"])))/ \
                            len(set_writers.union(set(item["writer"])))
                        # rating_score is "closeness" in rating, scaled to 1
                        rating_score = 0 if (not ref_rating) or (not item["rating"]) else \
                            1-abs(ref_rating-item["rating"])/10
                        # year_score is "closeness" in release year, scaled to 1 (only for movies in same decade)
                        year_score = 0 if not ref_year or not item["year"] or abs(ref_year-item["year"])>10 else \
                            1-abs(ref_year-item["year"])/10
                        # mpaa_score gets 1 if same mpaa rating, otherwise 0
                        mpaa_score = 1 if ref_movie["mpaa"] and ref_movie["mpaa"]==item["mpaa"] else 0
                        # calculate overall score using weighted average
                        similarscore = .5*genre_score + .2*director_score + .1*writer_score + .1*rating_score + \
                            .05*year_score + .05*mpaa_score
                        # exponentially scale score for movies in same set
                        if ref_setid and ref_setid==item["setid"]:
                            similarscore = similarscore**(1./2)
                        # assign score for movie, used for sorting
                        item["similarscore"] = similarscore
                        # add extraproperties for skinners
                        item["extraproperties"] = {"similartitle": ref_title+" (%2.f%%)"%(100*similarscore),
                            "originalpath": item["file"]}
                        # add items to list
                        all_items.append(item)
                        all_titles.append(item["title"])
        # return the list capped by limit and sorted by number of matching genres then rating
        return sorted(all_items, key=itemgetter("similarscore"), reverse=True)[:self.options["limit"]]

    def forgenre(self, genre=None, hide_watched=None, limit=None, sort=True):
        ''' get top rated movies for given genre'''
        # check options for arguments not provided
        if not genre:
            genre = self.options.get("genre", "")
        if not hide_watched:
            hide_watched = self.options["hide_watched"]
        if not limit:
            limit = self.options["limit"]
        if not genre:
            # get a random genre if no genre found
            genres = self.metadatautils.kodidb.genres("movie")
            if genres:
                genre = genres[0]["label"]
        all_items = []
        if genre:
            # get all movies from the same genre
            for item in self.get_genre_movies(genre, hide_watched=hide_watched, limit=limit, sort=False):
                # append original genre as listitem property for later reference by skinner
                item["extraproperties"] = {"genretitle": genre, "originalpath": item["file"]}
                all_items.append(item)
        if sort:
            # return the list sorted by rating by default
            return sorted(all_items, key=itemgetter("rating"), reverse=True)
        else:
            # skip sort otherwise (i.e. for similar widget)
            return all_items

    def inprogressandrecommended(self):
        ''' get recommended AND in progress movies '''
        all_items = self.inprogress()
        all_titles = [item["title"] for item in all_items]
        for item in self.recommended():
            if item["title"] not in all_titles:
                all_items.append(item)
        return all_items[:self.options["limit"]]

    def inprogressandrandom(self):
        ''' get in progress AND random movies '''
        all_items = self.inprogress()
        all_ids = [item["movieid"] for item in all_items]
        for item in self.random():
            if item["movieid"] not in all_ids:
                all_items.append(item)
        return all_items[:self.options["limit"]]

    def top250(self):
        ''' get imdb top250 movies in library '''
        all_items = []
        filters = []
        if self.options.get("tag"):
            filters.append({"operator": "contains", "field": "tag", "value": self.options["tag"]})
        fields = ["imdbnumber"]
        if KODI_VERSION > 16:
            fields.append("uniqueid")
        all_movies = self.metadatautils.kodidb.get_json(
            'VideoLibrary.GetMovies', fields=fields, returntype="movies", filters=filters)
        top_250 = self.metadatautils.imdb.get_top250_db()
        for movie in all_movies:
            imdbnumber = movie["imdbnumber"]
            if not imdbnumber and "uniqueid" in movie:
                for value in movie["uniqueid"]:
                    if value.startswith("tt"):
                        imdbnumber = value
            if imdbnumber and imdbnumber in top_250:
                movie = self.metadatautils.kodidb.movie(movie["movieid"])
                movie["top250_rank"] = int(top_250[imdbnumber])
                all_items.append(movie)
        return sorted(all_items, key=itemgetter("top250_rank"))[:self.options["limit"]]

    def browsegenres(self):
        '''
            special entry which can be used to create custom genre listings
            returns each genre with poster/fanart artwork properties from 5
            random movies in the genre.
            TODO: get auto generated collage pictures from skinhelper's metadatautils ?
        '''
        all_genres = self.metadatautils.kodidb.genres("movie")
        return self.metadatautils.process_method_on_list(self.get_genre_artwork, all_genres)

    def get_genre_artwork(self, genre_json):
        '''helper method for browsegenres'''
        # for each genre we get 5 random items from the library and attach the artwork to the genre listitem
        genre_json["art"] = {}
        genre_json["file"] = "videodb://movies/genres/%s/" % genre_json["genreid"]
        if self.options.get("tag"):
            genre_json["file"] = "plugin://script.skin.helper.widgets?mediatype=movies&action=forgenre&tag=%s&genre=%s"\
                % (self.options["tag"], genre_json["label"])
        genre_json["isFolder"] = True
        genre_json["IsPlayable"] = "false"
        genre_json["thumbnail"] = genre_json.get("thumbnail",
                                                 "DefaultGenre.png")  # TODO: get icon from resource addon ?
        genre_json["type"] = "genre"
        sort = kodi_constants.SORT_RANDOM if self.options.get("random") else kodi_constants.SORT_TITLE
        genre_movies = self.get_genre_movies(genre_json["label"], False, 5, sort)
        if not genre_movies:
            return None
        for count, genre_movie in enumerate(genre_movies):
            genre_json["art"]["poster.%s" % count] = genre_movie["art"].get("poster", "")
            genre_json["art"]["fanart.%s" % count] = genre_movie["art"].get("fanart", "")
            if "fanart" not in genre_json["art"]:
                # set genre's primary fanart image to first movie fanart
                genre_json["art"]["fanart"] = genre_movie["art"].get("fanart", "")
        return genre_json

    def get_random_watched_movie(self):
        '''gets a random watched movie from kodi_constants.'''
        movies = self.metadatautils.kodidb.movies(sort=kodi_constants.SORT_RANDOM,
                                             filters=[kodi_constants.FILTER_WATCHED], limits=(0, 1))
        if movies:
            return movies[0]
        else:
            return None

    def get_recently_watched_movie(self):
        '''gets a random recently watched movie from kodi_constants.'''
        num_recent_similar = self.options["num_recent_similar"]
        movies = self.metadatautils.kodidb.movies(sort=kodi_constants.SORT_LASTPLAYED,
                                             filters=[kodi_constants.FILTER_WATCHED], limits=(0, num_recent_similar))
        if movies:
            return movies[randint(0,len(movies)-1)]
        else:
            return None

    def get_genre_movies(self, genre, hide_watched=False, limit=100, sort=kodi_constants.SORT_RANDOM):
        '''helper method to get all movies in a specific genre'''
        filters = [{"operator": "is", "field": "genre", "value": genre}]
        if self.options.get("tag"):
            filters.append({"operator": "contains", "field": "tag", "value": self.options["tag"]})
        if hide_watched:
            filters.append(kodi_constants.FILTER_UNWATCHED)
        if sort:
            return self.metadatautils.kodidb.movies(sort=sort, filters=filters, limits=(0, limit))
        else:
            # skip sort if set to false to save computer time
            return self.metadatautils.kodidb.movies(filters=filters, limits=(0, limit))

    def favourites(self):
        '''get favourites'''
        from favourites import Favourites
        self.options["mediafilter"] = "movies"
        return Favourites(self.addon, self.metadatautils, self.options).favourites()

    def favourite(self):
        '''synonym to favourites'''
        return self.favourites()
