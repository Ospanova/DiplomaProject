# Generated by Django 3.0.1 on 2019-12-22 21:11

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20191222_2039'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='premiere',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2019, 12, 22, 21, 11, 18, 374007)),
        ),
    ]