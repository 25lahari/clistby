# Generated by Django 3.1.14 on 2022-04-17 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clist', '0081_auto_20220417_1400'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='n_hidden',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
