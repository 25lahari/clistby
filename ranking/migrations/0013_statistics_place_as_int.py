# Generated by Django 2.1.7 on 2019-11-22 18:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ranking', '0012_account_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='statistics',
            name='place_as_int',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
