# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-03 09:59


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('true_coders', '0002_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='coder',
            name='first_name_native',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='coder',
            name='last_name_native',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]