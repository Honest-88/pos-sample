# Generated by Django 4.1.5 on 2023-05-25 21:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0005_rename_date_added_sale_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sale',
            name='created_at',
        ),
    ]