# Generated by Django 4.2.3 on 2023-09-17 13:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clist', '0119_resource_problem_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='slug',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='contest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='individual_problem_set', to='clist.contest'),
        ),
    ]