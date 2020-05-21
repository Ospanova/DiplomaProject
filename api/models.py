from django.db import models

from api.managers import *
from auth1.models import MainUser
from utils.constants import *
from utils.upload import *
from utils.validators import *
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator


class Movie(models.Model):
    movie_id = models.IntegerField(default=0)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=2550)
    price = models.IntegerField(default=1000)

    sum_of_rates = models.IntegerField(default=0)
    no_of_rates = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)

    premiere = models.DateTimeField(default=timezone.now(), blank=True)

    country = models.CharField(max_length=255, default="Kazakhstan")
    genre = models.CharField(max_length=255, default="Fantasy")
    movie_logo = models.CharField(max_length=255, default="")
    directed_by = models.CharField(max_length=255, default="Alikhan")
    creator = models.ForeignKey(MainUser, on_delete=models.CASCADE, related_name='movies')

    def __str__(self):
        return f'{self.movie_id}: {self.id} {self.name}'


class MovieImage(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=image_path, validators=[image_size, image_extension],
                              null=True)


class FavoriteMovie(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE, related_name='favorite_movies')


class Myrating(models.Model):
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE, related_name='user_ratings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.IntegerField(default=1, validators=[MaxValueValidator(5), MinValueValidator(0)])





class Comment(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='movie_comments')
    reply_to = models.IntegerField(null=True, default=0)
    created_by = models.ForeignKey(MainUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(max_length=1000, default='')
    comments = CommentManager()

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

    def __str__(self):
        return f'{self.created_by}: {self.movie}'


class MovieLike(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='movie_likes')
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE)
    likes = MovieLikeManager()

    class Meta:
        verbose_name = 'MovieLike'
        verbose_name_plural = 'MovieLikes'

    def __str__(self):
        return f'{self.created_by}: {self.movie}'


class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_likes')
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE)
    likes = CommentLikeManager()

    class Meta:
        verbose_name = 'CommentLike'
        verbose_name_plural = 'CommentLikes'

    def __str__(self):
        return f'{self.created_by}: {self.comment}'
