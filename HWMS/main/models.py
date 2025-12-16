from django.db import models
import requests
import pandas as pd

class FireDetection(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    bright_ti4 = models.FloatField()
    scan = models.FloatField()
    track = models.FloatField()
    acq_date = models.DateField()
    acq_time = models.CharField(max_length=4)
    satellite = models.CharField(max_length=10)
    instrument = models.CharField(max_length=10)
    confidence = models.CharField(max_length=1)
    version = models.CharField(max_length=10)
    bright_ti5 = models.FloatField()
    frp = models.FloatField()
    daynight = models.CharField(max_length=1)
    
    class Meta:
        db_table = 'fire_detection'
    
    def __str__(self):
        return f"Fire at ({self.latitude}, {self.longitude}) on {self.acq_date}"