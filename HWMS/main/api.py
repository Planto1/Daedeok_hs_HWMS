# main/api.py
import pandas as pd
from datetime import datetime
from .models import FireDetection

MAP_KEY = '5872ff30914a691ad9aa8eaf6e5410a7'

# Area 방식으로 변경 (남한 전체: 남,서,북,동)
SOUTH_KOREA_BBOX = '33,124,38.5,130'
area_url = f'https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/VIIRS_NOAA20_NRT/{SOUTH_KOREA_BBOX}/1'

def save_fire_data():
    """FIRMS API에서 데이터를 가져와 DB에 저장"""
    try:
        # 데이터 불러오기
        df_area = pd.read_csv(area_url)
        
        if df_area.empty:
            print("⚠️ 최근 화재 데이터가 없습니다.")
            return 0
        
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
        
        # 기존 데이터 삭제 후 저장 (중복 방지)
        FireDetection.objects.all().delete()
        
        # 한번에 저장
        FireDetection.objects.bulk_create(fire_list, batch_size=1000)
        
        print(f"✅ {len(fire_list)}개 데이터 저장 완료!")
        return len(fire_list)
        
    except Exception as e:
        print(f"❌ 데이터 저장 실패: {e}")
        return 0

if __name__ == '__main__':
    save_fire_data()