import operator

import pandas as pd
import numpy as np

from scipy.spatial import distance
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
import logging
from django.http import Http404
from django.db.models import Case, When
from django.shortcuts import get_object_or_404
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from api.models import *
from api.serializers import *
from api import recommendation
from rest_framework.views import APIView
# from django.utils import timezone


import csv
import random
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class MovieImageViewSet(viewsets.ModelViewSet):
    queryset = MovieImage.objects.all()
    serializer_class = MovieImageSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieFullSerializer
        return MovieSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]

    @action(methods=['GET', 'POST'], detail=False)
    def favorite(self, request):
        logger.info('received fovorite request')
        if request.method == 'GET':
            fav_movies = request.user.favorite_movies.all()
            movies = Movie.objects.filter(id__in=fav_movies.values('movie_id'))
            serializer = MovieSerializer(movies, many=True)
            return Response(serializer.data)
        else:
            print(request.data)
            movie_ids = request.data['movie_ids']
            for i in movie_ids:
                logging.info("movie id %s", i)
                try:
                    movie = Movie.objects.get(id=i)
                    FavoriteMovie.objects.create(movie=movie, user=request.user)
                except:
                    raise Exception('not such movie')
            fav_movies = request.user.favorite_movies.all()
            movies = Movie.objects.filter(id__in=fav_movies.values('movie_id'))
            serializer = MovieSerializer(movies, many=True)
            return Response(serializer.data)

    @action(methods=['POST'], detail=False)
    def rate(self, request):
        logger.info('received request: set rating from user %s', request.user)
        movie_id = request.data['movie_id']
        rating = request.data['rating']
        movie = Movie.objects.get(movie_id=movie_id)
        Myrating.objects.create(user=request.user, movie=movie, rating=rating)
        movie.sum_of_rates += rating
        movie.no_of_rates += 1
        movie.rating = movie.sum_of_rates / movie.no_of_rates
        movie.save()
        serializer = MovieSerializer(movie)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_sorted_by_rating(self, request):
        logger.info('received request: get list sorted by rating by user %s', request.user)
        movies = Movie.objects.order_by('-rating')
        ordered = sorted(movies, key=operator.attrgetter('name'))
        serializer = MovieSerializer(ordered, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_movies_by_genre(self, request):
        logger.info('received request: get movies by genre by user %s', request.user)
        genre = request.META.get('HTTP_GENRE')
        # print(request.META)
        movies = Movie.objects.filter(genre=genre)
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def premieres_of_the_week(self, request):
        logger.info('received request: premieres of the week')

        def this_week(premiere):
            premiere_time = premiere.replace(tzinfo=None)
            now_time = datetime.now().replace(tzinfo=None)
            difference = premiere_time - now_time
            logger.info('number of days to wait to %s is : %s', premiere, difference.days)
            return 0 <= difference.days < 7 and premiere_time.weekday() >= now_time.weekday()

        movies = Movie.objects.all()
        movies = [movie for movie in movies if this_week(movie.premiere)]
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def refresh(self, request):
        logger.info('received request: refresh list of movies')
        movies = Movie.objects.all()

        def obsolete_movie(movie):
            premiere_time = movie.premiere.replace(tzinfo=None)
            now_time = datetime.now().replace(tzinfo=None)
            difference = now_time - premiere_time
            return difference.days >= 60

        [movie.delete() for movie in movies if obsolete_movie(movie)]

        return Response("OK")

    @action(methods=['GET'], detail=False)
    def attach(self, request):
        user = request.user
        logger.info('received request: attach movies')
        csv_path = "/Users/aida/Downloads/cinema 2/api/views/web_movie.csv"

        with open(csv_path, "r") as f_obj:
            csv_reader(f_obj, user)

    @action(methods=['GET'], detail=False)
    def recommend(self, request):
        df = pd.DataFrame(list(Myrating.objects.all().values()))
        print(df.shape)
        current_user_id = request.user.id
        logger.info('received request: recommend with user_id %s', current_user_id)
        prediction_matrix, Ymean, predicted_X = recommendation.recommender()
        prediction_for_user = prediction_matrix[:, current_user_id - 1] + Ymean.flatten()

        pred_idxs_sorted = np.argsort(prediction_for_user)
        pred_idxs_sorted[:] = pred_idxs_sorted[::-1]
        pred_idxs_sorted = pred_idxs_sorted + 1

        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pred_idxs_sorted)])
        predicted_movies = list(Movie.objects.filter(movie_id__in=pred_idxs_sorted, ).order_by(preserved)[:10])

        serializer = MovieSerializer(predicted_movies, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_similar(self, request):
        movie = Movie.objects.get(id=int(request.query_params.get('id')))
        movie_id = movie.movie_id
        prediction_matrix, Ymean, predicted_X = recommendation.recommender()
        sorted_movies = recommendation.get_similar_content_based_movies(movie_id, predicted_X)
        sorted_movies = [movie.movie_id for movie in sorted_movies]
        sorted_movies = sorted_movies[:5]
        movies = Movie.objects.filter(movie_id__in=sorted_movies)
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def fill_ratings(self, request):
        csv_path = "/Users/aida/Downloads/cinema 2/api/views/web_myrating.csv"

        with open(csv_path, "r") as f_obj:
            csv_reader = csv.DictReader(f_obj)
            for line in csv_reader:
                # "id","rating","movie_id","user_id"
                rating = line["rating"]
                movie = Movie.objects.get(movie_id=line["movie_id"])
                user = MainUser.objects.get(id=line["user_id"])

                Myrating.objects.create(user=user, movie=movie, rating=rating)
        return Response("OK")


# def get_similar_movie_ids(movie_id):
#     prediction_matrix, Ymean, predicted_X = recommendation.recommender()
#     movies = Movie.objects.all()
#     current_movie_features = predicted_X[movie_id - 1, :]
#     sorted_movies = sorted(movies, key=lambda movie: distance.euclidean(current_movie_features,
#                                                                         predicted_X[movie.movie_id - 1, :]))
#     return sorted_movies


def csv_reader(file_obj, user):
    """
    Read a csv file
    """
    csv_reader = csv.DictReader(file_obj)
    for line in csv_reader:
        print(line)
        movie_id = line["id"]
        title = line["title"]
        genre = line["genre"]
        movie_logo = line["movie_logo"]
        step = timedelta(days=1)
        start = datetime(2020, 4, 1, tzinfo=timezone.utc)
        end = datetime(2020, 4, 20, tzinfo=timezone.utc)
        random_date = start + random.randrange((end - start) // step + 1) * step
        Movie.objects.create(movie_id=movie_id, name=title, genre=genre, movie_logo=movie_logo, creator=user,
                             premiere=random_date)


class CommentListViewSet(mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    serializer_class = BaseCommentSerializer

    @action(methods=['get'], detail=True)
    def comment_to_movie(self, request, pk):
        comments = Comment.comments.filter(movie=pk)
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = BaseCommentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Comment.comments.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        return serializer.save(created_by=self.request.user)


class MovieLikeListViewSet(mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = BaseMovieLikeSerializer

    @action(methods=['get'], detail=True)
    def like_to_movie(self, request, pk):
        likes = MovieLike.likes.filter(movie=pk)
        serializer = self.get_serializer(likes, many=True)
        return Response(serializer.data)


class MovieLikeViewSet(viewsets.ModelViewSet):
    serializer_class = BaseMovieLikeSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return MovieLike.likes.filter(user=self.request.user)

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)


class CommentLikeListViewSet(mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = BaseCommentLikeSerializer

    @action(methods=['get'], detail=True)
    def like_to_comment(self, request, pk):
        likes = CommentLike.likes.filter(comment=pk)
        serializer = self.get_serializer(likes, many=True)
        return Response(serializer.data)


class CommentLikeViewSet(viewsets.ModelViewSet):
    serializer_class = BaseCommentLikeSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return CommentLike.likes.filter(user=self.request.user)

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)