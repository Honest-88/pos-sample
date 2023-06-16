from django.db import models
from django.utils import timezone
from datetime import datetime
from customers.models import Customer
from products.models import Product
from django.db.models.functions import Coalesce
from django.db.models import F, FloatField, IntegerField, ExpressionWrapper


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
        return "Sale ID: " + str(self.id) + " | Grand Total: " + str(self.grand_total) + " | Datetime: " + str(self.date)


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

    
    def __str__(self):
        return "Detail ID: " + str(self.id) + " Sale ID: " + str(self.sale.id) + " Quantity: " + str(self.quantity)

    
    def save(self, *args, **kwargs):
        print("SaleDetail save method called")
        self.total_detail = self.price * self.quantity
        self.profit = self.total_detail - (self.buying_price * self.quantity) if self.buying_price else 0.0
        super().save(*args, **kwargs)
        self.sale.update_totals()

        # Deduct sold quantity from product's quantity
        product = self.product
        product.quantity = ExpressionWrapper(F('quantity') - self.quantity, output_field=IntegerField())
        product.grand_product_total = ExpressionWrapper(F('grand_product_total') - self.total_detail, output_field=FloatField())
        product.total_amount = ExpressionWrapper(F('total_amount') - self.total_detail, output_field=FloatField())
        product.save()

        # Add print statement to verify if product is saved
        print("Product saved:", product)


    #def __init__(self, *args, **kwargs):
    #    super().__init__(*args, **kwargs)
    #    self.quantity = self.quantity

        #product.deduct_quantity(self.quantity)

