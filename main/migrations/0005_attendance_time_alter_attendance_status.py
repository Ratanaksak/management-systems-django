# Generated by Django 5.1.2 on 2024-12-13 07:44

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_remove_attendance_timestamp_attendance_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='time',
            field=models.TimeField(auto_now_add=True, default=datetime.time(8, 0)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='attendance',
            name='status',
            field=models.CharField(choices=[('Present', 'Present'), ('Late', 'Late')], default='Present', max_length=10),
        ),
    ]
