from django.db import models
from django.forms import model_to_dict
from django.utils import timezone
from datetime import datetime
from django.db.models import F, ExpressionWrapper, FloatField, IntegerField



class Category(models.Model):
    STATUS_CHOICES = (  # new
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )

    name = models.CharField(max_length=256)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the category",
    )

    class Meta:
        # Table's name
        db_table = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    STATUS_CHOICES = (  # new
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )
    date = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=256)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the product",
    )
    category = models.ForeignKey(
        Category, related_name="category", on_delete=models.CASCADE, db_column='category')

    buying_price = models.FloatField(default=0)
    price = models.FloatField(default=0)
    quantity = models.IntegerField(default=0)
    total_amount = models.FloatField(default=0)
    profit_amount = models.FloatField(default=0)  # Add this field
    
    
    class Meta:
        # Table's name
        db_table = "Product"

    def __str__(self) -> str:
        return self.name

    @property
    def profit(self):
        return (self.price - self.buying_price) * self.quantity

    def save(self, *args, **kwargs):
        self.total_amount = self.price * self.quantity
        #self.profit_display = self.price - self.buying_price
        self.profit_amount  = (self.price - self.buying_price) * self.quantity
        super().save(*args, **kwargs)

    def to_json(self):
        item = model_to_dict(self)
        item['id'] = self.id
        item['text'] = self.name
        item['category'] = self.category.name
        item['quantity'] = 1
        item['total_product'] = 0
        return item

    def update_buying_prices(self, buying_prices):
        # Update buying prices for existing products
        for product, buying_price in zip(Product.objects.all(), buying_prices):
            product.buying_price = buying_price
            product.save()

    
    def deduct_quantity(self, quantity):
        self.quantity = F('quantity') - quantity
        self.save(update_fields=['quantity'])