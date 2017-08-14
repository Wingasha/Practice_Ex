# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-08-14 02:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('weather_forecast', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='forecast',
            managers=[
                ('near_forecast', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterField(
            model_name='weather',
            name='description',
            field=models.CharField(max_length=100),
        ),
        migrations.DeleteModel(
            name='WeatherDescription',
        ),
    ]