# Generated by Django 5.1.7 on 2025-03-23 01:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgfs', '0006_remove_savingstransaction_weeks_covered_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeekProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_number', models.PositiveIntegerField()),
                ('expected_amount', models.PositiveIntegerField()),
                ('amount_paid', models.PositiveIntegerField(default=0)),
                ('is_fully_paid', models.BooleanField(default=False)),
                ('user_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='week_progress', to='tgfs.userprofile')),
            ],
            options={
                'ordering': ['week_number'],
                'unique_together': {('user_profile', 'week_number')},
            },
        ),
    ]
