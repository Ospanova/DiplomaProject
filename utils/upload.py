import os
import shutil
from datetime import datetime


def image_path(instance, filename):
    movie_id = instance.movie.id
    return f'movies/{movie_id}/{filename}'


def image_delete_path(image):
    image_path = os.path.abspath(os.path.join(image.path, '..'))
    shutil.rmtree(image_path)
