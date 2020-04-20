from rest_framework import serializers
from auth1.models import *
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True)

  class Meta:
    model = MainUser
    fields = ('username', 'email', 'date_joined','password','isAdmin')
    read_only_fields = ('profile',)

  def create(self, validated_data):
    user = MainUser.objects.create_user(**validated_data)
    return user

