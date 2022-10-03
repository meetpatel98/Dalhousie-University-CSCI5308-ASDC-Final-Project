import datetime

from django.db import models


# Create your models here.
class RegisterModel(models.Model):
    first_name = models.CharField(max_length=50)  # Required Field
    last_name = models.CharField(max_length=50)  # Required Field
    date_of_birth = models.DateField()  # Required Field
    email = models.EmailField(max_length=50, unique=True)  # Required Field
    country_code = models.CharField(max_length=5, default="+1")  # Optional Field
    phone = models.CharField(max_length=15, unique=True)  # Required Field
    user_password = models.CharField(max_length=200)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    attempts_left = models.IntegerField(default=10)
    lock = models.DateTimeField(default=datetime.datetime.now())
    account_status = models.CharField(max_length=100, default="inactive")
    is_farmer = models.BooleanField(default=False)


class VendorManager(models.Model):
    user = models.ForeignKey(RegisterModel, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    market_name = models.CharField(max_length=100)
    address = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


class VendorProduct(models.Model):
    user_id = models.ForeignKey(RegisterModel, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=15, decimal_places=10)
    image = models.ImageField(upload_to="static/Images/product")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


class VendorInventory(models.Model):
    user_id = models.ForeignKey(RegisterModel, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=15, decimal_places=10)
    unit = models.CharField(max_length=10)


class ProductViews(models.Model):
    product = models.ForeignKey(VendorProduct, on_delete=models.CASCADE)
    views = models.IntegerField(default=0)


class VendorBlogs(models.Model):
    vendor = models.ForeignKey(RegisterModel, on_delete=models.CASCADE)
    title = models.CharField(max_length=300, default="")
    content = models.TextField(default="")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


class CostManager(models.Model):
    vendor = models.ForeignKey(RegisterModel, on_delete=models.CASCADE)
    category = models.CharField(max_length=100)
    coster = models.CharField(max_length=200)
    expense = models.DecimalField(max_digits=15, decimal_places=10)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
