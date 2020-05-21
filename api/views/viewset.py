import operator

import pandas as pd
import numpy as np

from scipy.spatial import distance
from rest_framework import viewsets
from rest_framework import mixins, status
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
from api.tasks import *
from rest_framework.views import APIView
# from django.utils import timezone


import csv
import random
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)
recommendation_dict = dict()


class MovieImageViewSet(viewsets.ModelViewSet):
    queryset = MovieImage.objects.all()
    serializer_class = MovieImageSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.order_by('-rating')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        current_user_id = request.user.id
        if current_user_id is not None:
            print("HERE")
            n = recommend_async.delay(current_user_id)
            recommendation_dict[current_user_id] = n.get()

        return Response(serializer.data)

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
        rating = request.data['rating']
        m_id = request.data['id']
        movie = Movie.objects.get(id=m_id)
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
        current_user_id = request.user.id
        if current_user_id is not None:
            n = recommend_async.delay(current_user_id)
            recommendation_dict[current_user_id] = n.get()
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
        current_user_id = request.user.id
        if current_user_id in recommendation_dict.keys():
            print("Already known info")
            return Response(recommendation_dict[current_user_id])
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
    def get_similar_by_user_ratings(self, request):
        movie = Movie.objects.get(id=int(request.query_params.get('id')))
        movie_id = movie.movie_id
        logger.info('received get similar movies by user ratings request for movie with movie_id %s', movie_id)

        prediction_matrix, Ymean, predicted_X = recommendation.recommender()
        sorted_movies = recommendation.get_similar_content_based_movies(movie_id, predicted_X)
        sorted_movies = [movie.movie_id for movie in sorted_movies]
        sorted_movies = sorted_movies[:5]
        movies = Movie.objects.filter(movie_id__in=sorted_movies)
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_similar_by_content(self, request):
        movie = Movie.objects.get(id=int(request.query_params.get('id')))
        movie_id = movie.movie_id
        logger.info('received get similar movies by content request for movie with movie_id %s', movie_id)

        properties = {}
        total = 0
        movies = Movie.objects.all()
        for movie in movies:
            genres = movie.genre.split('|')
            for genre in genres:
                if genre not in properties:
                    properties[genre] = total
                    total += 1

        matrix = []
        for movie in movies:
            values = []
            for i in range(total):
                values.append(0)
            genres = movie.genre.split('|')
            for genre in genres:
                values[properties[genre]] = 1
            matrix.append(values)

        matrix = np.array(matrix)
        sorted_movies = recommendation.get_similar_content_based_movies(movie_id, matrix)
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


def has_permission(created_by, user):
    return created_by.id == user.id


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = BaseCommentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Comment.comments.filter(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        if not has_permission(instance.created_by, self.request.user):
            return Response(serializer.data, status=status.HTTP_404_NOT_FOUND)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def perform_create(self, serializer):
        return serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not has_permission(instance.created_by, self.request.user):
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        if not has_permission(instance.created_by, self.request.user):
            return Response(serializer.data, status=status.HTTP_404_NOT_FOUND)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not has_permission(instance.created_by, self.request.user):
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if CommentLike.likes.all().filter(comment=serializer.validated_data['comment']) is not None:
            print("REPEATED ")
            return Response(status=status.HTTP_201_CREATED)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        print(serializer.validated_data['comment'])
        return serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not has_permission(instance.created_by, self.request.user):
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()
