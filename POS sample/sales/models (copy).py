from django.db import models
from django.utils import timezone
from datetime import datetime
from customers.models import Customer
from products.models import Product
from django.db.models.functions import Coalesce


class Sale(models.Model):
    date = models.DateTimeField(default=timezone.now)
    customer = models.ForeignKey(Customer, models.DO_NOTHING, db_column='customer')
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    tax_percentage = models.FloatField(default=0)
    amount_payed = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)
    profit = models.FloatField(default=0)
 

    class Meta:
        db_table = 'Sales'


    def __str__(self):
        return f"Sale ID: {self.id} | Grand Total: {self.grand_total} | Date: {self.date}"


    def update_totals(self):
        details = self.saledetail_set.all()
        self.sub_total = details.aggregate(total=Coalesce(models.Sum(models.F('total_detail')), 0))['total']
        self.grand_total = self.sub_total + self.tax_amount
        self.profit = details.aggregate(total=Coalesce(models.Sum(models.F('profit')), 0))['total']
        self.save(update_fields=['sub_total', 'grand_total', 'profit'])


class SaleDetail(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.FloatField()
    quantity = models.IntegerField()
    total_detail = models.FloatField()
    buying_price = models.FloatField(null=True)  # Nullable field
    profit = models.FloatField(default=0)  # Set default value


    class Meta:
        db_table = 'SaleDetails'

    
    def save(self, *args, **kwargs):
        self.total_detail = self.price * self.quantity
        self.profit = self.total_detail - (self.buying_price * self.quantity) if self.buying_price else 0
        super().save(*args, **kwargs)
        self.sale.update_totals()

        # Deduct sold quantity from product's quantity
        product = self.product
        product.deduct_quantity(self.quantity)


    def __str__(self):
        return f"Detail ID: {self.id} | Sale ID: {self.sale.id} | Quantity: {self.quantity}"

