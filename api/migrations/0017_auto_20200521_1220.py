# Generated by Django 2.0.12 on 2020-05-21 12:20

import datetime
from django.conf import settings
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0016_auto_20200508_2010'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='liked_by',
            field=models.ManyToManyField(related_name='liked_comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='movie',
            name='premiere',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2020, 5, 21, 12, 20, 21, 667724, tzinfo=utc)),
        ),
    ]
