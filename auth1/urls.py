from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token


from auth1.views import RegisterUserAPIView, UserViewSet, GenerateRegisterAPIView

urlpatterns = [
    path('login/', obtain_jwt_token),
    path('register/', RegisterUserAPIView.as_view()),
    path('generate/', GenerateRegisterAPIView)
]

router = DefaultRouter()
router.register('auth1', UserViewSet, basename='auth1')


urlpatterns += router.urls