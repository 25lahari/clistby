# Generated by Django 4.2.3 on 2023-10-28 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('true_coders', '0063_alter_coderlist_access_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coderlist',
            name='access_level',
            field=models.CharField(choices=[('public', 'Public'), ('private', 'Private'), ('restricted', 'Restricted')], default='private', max_length=10),
        ),
    ]
