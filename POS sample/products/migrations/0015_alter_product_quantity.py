# Generated by Django 4.1.5 on 2023-06-15 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0014_rename_profits_product_profit_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='quantity',
            field=models.FloatField(default=0),
        ),
    ]