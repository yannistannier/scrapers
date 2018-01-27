# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-08 16:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scrapper', '0003_profiltoparse_site'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scrapper.Job')),
                ('profil', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scrapper.ParsedProfile')),
            ],
        ),
    ]