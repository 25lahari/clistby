# Generated by Django 3.1.14 on 2022-05-22 18:39

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0026_notificationmessage_sender'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendar',
            name='descriptions',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveSmallIntegerField(choices=[('1', 'Url'), ('2', 'Host'), ('3', 'Duration')]), null=True, size=None),
        ),
    ]