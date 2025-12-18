# main/api.py
import pandas as pd
import requests
from datetime import datetime, timedelta
from .models import FireDetection

MAP_KEY = '5872ff30914a691ad9aa8eaf6e5410a7'
SOUTH_KOREA_BBOX = '33,124,38.5,130'

def save_fire_data_by_date_range(start_date, end_date):
    """
    특정 날짜 범위의 FIRMS 데이터를 가져와 DB에 저장
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD 문자열)
        end_date: 종료 날짜 (YYYY-MM-DD 문자열)
    
    Returns:
        int: 저장된 데이터 개수
    """
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        days_diff = (end - start).days + 1
        
        print(f"\n{'='*60}")
        print(f"📡 FIRMS API 데이터 수집 시작")
        print(f"📅 기간: {start_date} ~ {end_date} ({days_diff}일)")
        print(f"{'='*60}\n")
        
        all_fires = []
        
        # FIRMS API는 최대 10일씩만 조회 가능
        current_date = start
        batch_count = 0
        
        while current_date <= end:
            batch_count += 1
            # 현재 날짜부터 10일 또는 종료일까지
            batch_end = min(current_date + timedelta(days=9), end)
            batch_days = (batch_end - current_date).days + 1
            
            print(f"🔄 배치 {batch_count}: {current_date} ~ {batch_end} ({batch_days}일)")
            
            # Area API URL 구성
            area_url = f'https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/VIIRS_NOAA20_NRT/{SOUTH_KOREA_BBOX}/{batch_days}/{current_date.strftime("%Y-%m-%d")}'
            
            try:
                # 데이터 불러오기
                df_batch = pd.read_csv(area_url)
                
                if not df_batch.empty:
                    print(f"   ✅ {len(df_batch)}개 데이터 수신")
                    
                    for idx, row in df_batch.iterrows():
                        # 날짜 변환
                        if isinstance(row['acq_date'], str):
                            acq_date = datetime.strptime(row['acq_date'], '%Y-%m-%d').date()
                        else:
                            acq_date = row['acq_date']
                        
                        # 요청한 날짜 범위 내의 데이터만 필터링
                        if start <= acq_date <= end:
                            fire_data = {
                                'latitude': row['latitude'],
                                'longitude': row['longitude'],
                                'bright_ti4': row['bright_ti4'],
                                'scan': row['scan'],
                                'track': row['track'],
                                'acq_date': acq_date,
                                'acq_time': str(row['acq_time']).zfill(4),
                                'satellite': row['satellite'],
                                'instrument': row['instrument'],
                                'confidence': row['confidence'],
                                'version': row['version'],
                                'bright_ti5': row['bright_ti5'],
                                'frp': row['frp'],
                                'daynight': row['daynight']
                            }
                            all_fires.append(fire_data)
                else:
                    print(f"   ⚠️  데이터 없음")
                    
            except Exception as e:
                print(f"   ❌ 배치 처리 실패: {e}")
            
            # 다음 배치로 이동
            current_date = batch_end + timedelta(days=1)
        
        if not all_fires:
            print(f"\n⚠️  해당 기간에 화재 데이터가 없습니다.\n")
            return 0
        
        print(f"\n{'='*60}")
        print(f"💾 데이터베이스 저장 시작 (총 {len(all_fires)}개)")
        print(f"{'='*60}\n")
        
        # 해당 기간의 기존 데이터 삭제
        deleted_count = FireDetection.objects.filter(
            acq_date__gte=start_date,
            acq_date__lte=end_date
        ).delete()[0]
        
        if deleted_count > 0:
            print(f"🗑️  기존 데이터 {deleted_count}개 삭제")
        
        # 새 데이터 저장
        fire_objects = []
        for fire_data in all_fires:
            fire_objects.append(FireDetection(**fire_data))
        
        # Bulk Create (배치 저장)
        FireDetection.objects.bulk_create(fire_objects, batch_size=1000, ignore_conflicts=True)
        
        print(f"✅ {len(fire_objects)}개 데이터 저장 완료!\n")
        
        # 저장된 데이터 확인
        saved_count = FireDetection.objects.filter(
            acq_date__gte=start_date,
            acq_date__lte=end_date
        ).count()
        
        print(f"{'='*60}")
        print(f"📊 최종 결과")
        print(f"{'='*60}")
        print(f"   총 수집: {len(all_fires)}개")
        print(f"   DB 저장: {saved_count}개")
        print(f"   기간: {start_date} ~ {end_date}")
        print(f"{'='*60}\n")
        
        return saved_count
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}\n")
        import traceback
        traceback.print_exc()
        return 0

def save_fire_data(days=10):
    """
    최근 N일의 데이터 저장 (기존 호환성 유지)
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    return save_fire_data_by_date_range(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )

if __name__ == '__main__':
    # 테스트: 최근 7일 데이터 저장
    save_fire_data(days=7)