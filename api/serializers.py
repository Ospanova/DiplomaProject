from rest_framework import serializers
from api.models import *
from django.db import transaction
import logging
from auth1.serializers import UserSerializer


logger = logging.getLogger(__name__)


class MovieSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())
    creator_name = serializers.SerializerMethodField()
    images_uploaded = serializers.ListField(
        child=serializers.ImageField(), required=False
    )

    class Meta:
        model = Movie
        fields = ('id','movie_id', 'name', 'price', 'premiere', 'creator', 'country', 'genre' ,
                  'rating', 'images_uploaded', 'creator_name', 'movie_logo')

    def get_creator_name(self, obj):
        if obj.creator is not None:
            return obj.creator.username
        return ''

    def validate_price(self, value):
        if value < 0 or value > 15000:
            raise serializers.ValidationError('price must be positive integer and at most 15000')
        return value

    '''
    def create(self, validated_data):
        # imgs = validated_data.pop('images_uploaded')
        imgs = [4]
        movie = Movie(**validated_data)
        movie.save()

        for i in imgs:
            print(i)
            img = MovieImage(image=i, movie=movie)
            img.save()

        return movie
    '''


class MovieImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieImage
        fields = '__all__'


class MovieFullSerializer(MovieSerializer):
    creator = UserSerializer(read_only=True)

    # images = serializers.ListField(
    #     child=serializers.IntegerField(), required=False
    # )

    class Meta(MovieSerializer.Meta):
        fields = MovieSerializer.Meta.fields + ('description', 'images')


class BaseCommentSerializer(serializers.ModelSerializer):
    movie = MovieSerializer

    class Meta:
        model = Comment
        fields = ('id', 'movie', 'reply_to', 'created_by', 'created_at', 'content')
        read_only_fields = ('id', 'created_by', 'created_at')


class BaseMovieLikeSerializer(serializers.ModelSerializer):
    movie = MovieSerializer

    class Meta:
        model = MovieLike
        fields = ('id', 'movie', 'user')
        read_only_fields = ('id', 'user')


class BaseCommentLikeSerializer(serializers.ModelSerializer):
    comment = BaseCommentSerializer

    class Meta:
        model = CommentLike
        fields = ('id', 'comment', 'user')
        read_only_fields = ('id', 'user')