from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import time
import datetime
from datetime import datetime
from django.db.models import Sum





class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return self.name
    

class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(null=True, blank=True)  # No time for absentees
    status = models.CharField(
        max_length=10,
        choices=[('Morning', 'Present'), ('Late', 'Late'), ('Absent', 'Absent')],
        default='Present'
    )

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.status}"

    def save(self, *args, **kwargs):
        # Ensure time is saved as timezone-aware
        self.time = now().astimezone().time()  # Save the current local time
        super().save(*args, **kwargs)
    

#for add attendace wedding
class Province(models.Model):
    name = models.CharField(max_length=100)
    kh_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=100)
    kh_name = models.CharField(max_length=100, blank=True, null=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Commune(models.Model):
    name = models.CharField(max_length=100)
    kh_name = models.CharField(max_length=100, blank=True, null=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Village(models.Model):
    name = models.CharField(max_length=100)
    kh_name = models.CharField(max_length=100, blank=True, null=True)
    commune = models.ForeignKey(Commune, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Person(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    price_khr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    gender = models.CharField(max_length=6, choices=[('Male', 'Male'), ('Female', 'Female')])
    relationship = models.CharField(max_length=10, choices=[('Wife', 'Wife'), ('Husband', 'Husband')])

    # Location fields (ForeignKey to each location model)
    province = models.ForeignKey('Province', on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True, blank=True)
    commune = models.ForeignKey('Commune', on_delete=models.SET_NULL, null=True, blank=True)
    village = models.ForeignKey('Village', on_delete=models.SET_NULL, null=True, blank=True)
    

    @classmethod
    def total_prices(cls):
        totals = cls.objects.aggregate(
            total_price_usd=Sum('price_usd'),
            total_price_khr=Sum('price_khr')
        )
        return {
            'total_price_usd': totals['total_price_usd'] or 0,
            'total_price_khr': totals['total_price_khr'] or 0,
            'grand_total': (totals['total_price_usd'] or 0) + (totals['total_price_khr'] or 0),
        }