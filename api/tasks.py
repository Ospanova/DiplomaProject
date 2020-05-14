from __future__ import absolute_import, unicode_literals
from celery import shared_task

@shared_task
def send_post_signup():
    return ("Here")