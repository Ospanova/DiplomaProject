from __future__ import absolute_import, unicode_literals

import pandas as pd
import numpy as np
from celery import shared_task
import logging
from django.db.models import Case, When
from api import recommendation

from api.models import Myrating, Movie
from api.serializers import MovieSerializer

logger = logging.getLogger(__name__)

@shared_task
def recommend_async(current_user_id):
    df = pd.DataFrame(list(Myrating.objects.all().values()))
    logger.info('received request: recommend with user_id %s', current_user_id)
    prediction_matrix, Ymean, predicted_X = recommendation.recommender()
    prediction_for_user = prediction_matrix[:, current_user_id - 1] + Ymean.flatten()

    pred_idxs_sorted = np.argsort(prediction_for_user)
    pred_idxs_sorted[:] = pred_idxs_sorted[::-1]
    pred_idxs_sorted = pred_idxs_sorted + 1

    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pred_idxs_sorted)])
    predicted_movies = list(Movie.objects.filter(movie_id__in=pred_idxs_sorted, ).order_by(preserved)[:10])
    serializer = MovieSerializer(predicted_movies, many=True)
    return serializer.data