# Generated by Django 3.1.14 on 2023-07-22 10:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('true_coders', '0054_auto_20230528_1859'),
        ('ranking', '0082_verifiedaccount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='verifiedaccount',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verified_accounts', to='ranking.account'),
        ),
        migrations.AlterField(
            model_name='verifiedaccount',
            name='coder',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verified_accounts', to='true_coders.coder'),
        ),
    ]
