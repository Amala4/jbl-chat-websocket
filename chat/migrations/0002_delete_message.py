# Generated by Django 5.1.6 on 2025-03-08 00:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Message',
        ),
    ]
