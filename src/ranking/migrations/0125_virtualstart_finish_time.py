# Generated by Django 4.2.11 on 2024-04-26 22:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ranking', '0124_countryaccount_raw_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='virtualstart',
            name='finish_time',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]