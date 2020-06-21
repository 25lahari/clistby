# Generated by Django 2.2.13 on 2020-06-16 02:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clist', '0041_contest_writers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contest',
            name='writers',
            field=models.ManyToManyField(blank=True, related_name='writer_set', to='ranking.Account'),
        ),
    ]
