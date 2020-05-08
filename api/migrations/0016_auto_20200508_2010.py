# Generated by Django 2.0.12 on 2020-05-08 20:10

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0015_auto_20200504_1807'),
    ]

    operations = [
        migrations.CreateModel(
            name='MovieLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'MovieLike',
                'verbose_name_plural': 'MovieLikes',
            },
            managers=[
                ('likes', django.db.models.manager.Manager()),
            ],
        ),
        migrations.RemoveField(
            model_name='postlike',
            name='movie',
        ),
        migrations.RemoveField(
            model_name='postlike',
            name='user',
        ),
        migrations.AlterField(
            model_name='movie',
            name='premiere',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2020, 5, 8, 20, 10, 20, 846467, tzinfo=utc)),
        ),
        migrations.DeleteModel(
            name='PostLike',
        ),
        migrations.AddField(
            model_name='movielike',
            name='movie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movie_likes', to='api.Movie'),
        ),
        migrations.AddField(
            model_name='movielike',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
