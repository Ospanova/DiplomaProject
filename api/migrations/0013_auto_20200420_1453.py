# Generated by Django 2.0.12 on 2020-04-20 14:53

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_auto_20200419_1523'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='premiere',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2020, 4, 20, 14, 53, 31, 795821, tzinfo=utc)),
        ),
    ]
