from django.db import models


class Lottery(models.Model):
    LOTTERY_TYPE = (
        ('LOT', 'Lotto'),
        ('PL', 'Pension_Lottery'),
    )
    selection_number = models.CharField(max_length=100)
    winning_number = models.CharField(max_length=100)
    date = models.DateField()
    type = models.CharField(max_length=5, choices=LOTTERY_TYPE)
    is_win = models.BooleanField(default=False)