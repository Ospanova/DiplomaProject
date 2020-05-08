from django.urls import path
from api.views import *

from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework import routers

urlpatterns = [
]

router = routers.DefaultRouter()
router.register('movies', MovieViewSet, basename='api')
router.register('images', MovieImageViewSet, basename='api')
router.register('comments', CommentListViewSet, base_name='api')

urlpatterns += router.urls