# Generated by Django 3.0.5 on 2020-04-14 18:18

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_auto_20200402_1039'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='premiere',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2020, 4, 14, 18, 18, 49, 791097, tzinfo=utc)),
        ),
    ]