# Generated by Django 2.2.2 on 2019-06-25 23:25

from django.db import migrations, models
import seekers.models


class Migration(migrations.Migration):

    dependencies = [
        ('seekers', '0010_auto_20190625_1749'),
    ]

    operations = [
        migrations.AddField(
            model_name='seeker',
            name='ready_to_pair',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='seekerpairing',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='seekerpairing',
            name='pair_date',
            field=models.DateField(default=seekers.models.today),
        ),
    ]
