from django.urls import path
from api.views import *

from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework import routers

urlpatterns = [
    path('comments/<int:pk>/', CommentListViewSet.as_view({'get': 'comment_to_movie'})),
    path('movie_likes/<int:pk>/', MovieLikeListViewSet.as_view({'get': 'like_to_movie'})),
    path('comment_likes/<int:pk>/', CommentLikeListViewSet.as_view({'get': 'like_to_comment'})),

]

router = routers.DefaultRouter()
router.register('movies', MovieViewSet, basename='api')
router.register('images', MovieImageViewSet, basename='api')
router.register('comment', CommentViewSet, base_name='api')
router.register('movie_like', MovieLikeViewSet, base_name='api')
router.register('comment_like', CommentLikeViewSet, base_name='api')


urlpatterns += router.urls