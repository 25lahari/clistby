# Generated by Django 4.2.11 on 2024-03-31 11:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ranking', '0115_remove_stage_contests'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stage',
            old_name='new_contests',
            new_name='contests',
        ),
    ]