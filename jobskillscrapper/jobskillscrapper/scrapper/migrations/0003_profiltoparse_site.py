# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-08 12:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrapper', '0002_profiltoparse'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiltoparse',
            name='site',
            field=models.CharField(max_length=250, null=True),
        ),
    ]
