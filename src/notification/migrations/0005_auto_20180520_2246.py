# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-05-20 22:46


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0004_auto_20180520_2240'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='notification',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notification.Notification'),
        ),
    ]