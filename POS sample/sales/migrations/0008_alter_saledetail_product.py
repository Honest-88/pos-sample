# Generated by Django 4.1.5 on 2023-06-15 08:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0014_rename_profits_product_profit_amount'),
        ('sales', '0007_alter_sale_customer_alter_saledetail_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saledetail',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product'),
        ),
    ]
