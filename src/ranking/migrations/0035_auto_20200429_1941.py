# Generated by Django 2.2.10 on 2020-04-29 21:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ranking', '0034_auto_20200429_1924'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='url',
            field=models.CharField(blank=True, max_length=4096, null=True),
        ),
    ]