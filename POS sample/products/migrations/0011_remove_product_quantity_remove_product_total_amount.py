# Generated by Django 4.1.5 on 2023-06-13 13:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_product_price_product_quantity_product_total_amount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='quantity',
        ),
        migrations.RemoveField(
            model_name='product',
            name='total_amount',
        ),
    ]
