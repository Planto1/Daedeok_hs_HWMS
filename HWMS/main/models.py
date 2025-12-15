from django.db import models
import requests
import pandas as pd
from datetime import datetime

# Create your models here.

MAP_KEY = '5872ff30914a691ad9aa8eaf6e5410a7'

area_url = 'https://firms.modaps.eosdis.nasa.gov/api/area/csv/' + MAP_KEY + '/VIIRS_NOAA20_NRT/125,33,130,38.5/10/2025-11-21'
df_area = pd.read_csv(area_url)



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
    
    @classmethod
    def save_from_dataframe(cls, df):
        FireDetection.save_from_dataframe(df_area)
        fire_list = []
        
        for idx, row in df.iterrows():
            # 날짜 변환
            if isinstance(row['acq_date'], str):
                acq_date = datetime.strptime(row['acq_date'], '%Y-%m-%d').date()
            else:
                acq_date = row['acq_date']
            
            # 시간을 4자리 문자열로
            acq_time = str(row['acq_time']).zfill(4)
            
            fire_obj = cls(
                latitude=row['latitude'],
                longitude=row['longitude'],
                bright_ti4=row['bright_ti4'],
                scan=row['scan'],
                track=row['track'],
                acq_date=acq_date,
                acq_time=acq_time,
                satellite=row['satellite'],
                instrument=row['instrument'],
                confidence=row['confidence'],
                version=row['version'],
                bright_ti5=row['bright_ti5'],
                frp=row['frp'],
                daynight=row['daynight']
            )
            
            fire_list.append(fire_obj)
        
        # 한번에 저장
        cls.objects.bulk_create(fire_list, batch_size=1000)
        
        print(f"{len(fire_list)}개 데이터 저장 완료!")
        return len(fire_list)