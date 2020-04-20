# Generated by Django 3.0.1 on 2019-12-22 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_movie_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='no_of_rates',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='movie',
            name='sum_of_rates',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='movie',
            name='rating',
            field=models.FloatField(default=0.0),
        ),
    ]