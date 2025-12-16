import pandas as pd
from datetime import datetime
from .models import FireDetection

MAP_KEY = '5872ff30914a691ad9aa8eaf6e5410a7'
area_url = f'https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/VIIRS_NOAA20_NRT/125,33,130,38.5/10/2025-11-21'

# 데이터 불러오기
df_area = pd.read_csv(area_url)

# DB에 저장
def save_fire_data():
    fire_list = []
    
    for idx, row in df_area.iterrows():
        # 날짜 변환
        if isinstance(row['acq_date'], str):
            acq_date = datetime.strptime(row['acq_date'], '%Y-%m-%d').date()
        else:
            acq_date = row['acq_date']
        
        # 시간을 4자리 문자열로
        acq_time = str(row['acq_time']).zfill(4)
        
        fire_obj = FireDetection(
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
    FireDetection.objects.bulk_create(fire_list, batch_size=1000)
    
    print(f"{len(fire_list)}개 데이터 저장 완료!")
    return len(fire_list)

# 실행
if __name__ == '__main__':
    save_fire_data()