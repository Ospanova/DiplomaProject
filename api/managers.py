from django.db import models


class CommentManager(models.Manager):
    def movie_comments(self, movie):
        return super().get_queryset().order_by('-created_date').filter(movie=movie)


# class MovieLikeManager(models.Manager):
#     def get_movie_likes(self, movie):
#         return movie.movie_likes.all()


class CommentLikeManager(models.Manager):
    def get_comment_like(self, comment):
        return comment.comment_likes.all()
