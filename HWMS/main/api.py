# main/api.py
import pandas as pd
import requests
from datetime import datetime, timedelta
from .models import FireDetection

MAP_KEY = '5872ff30914a691ad9aa8eaf6e5410a7'
# BBOX 형식: min_lon,min_lat,max_lon,max_lat
# 한국: 경도 124~130°E, 위도 33~38.5°N
SOUTH_KOREA_BBOX = '124,33,130,38.5'

def save_fire_data_by_date_range(start_date, end_date, satellite='VIIRS_NOAA20_NRT'):
    """
    특정 날짜 범위의 FIRMS 데이터를 가져와 DB에 저장
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD 문자열)
        end_date: 종료 날짜 (YYYY-MM-DD 문자열)
        satellite: 위성 종류 (VIIRS_NOAA20_NRT, VIIRS_SNPP_NRT, MODIS_NRT)
    
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
        print(f"🛰️ 위성: {satellite}")
        print(f"🔑 API 키: {MAP_KEY}")
        print(f"📍 영역: {SOUTH_KOREA_BBOX}")
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
            # FIRMS API 형식: /api/area/csv/{MAP_KEY}/{source}/{area}/{dayRange}/{date}
            area_url = f'https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{satellite}/{SOUTH_KOREA_BBOX}/{batch_days}/{current_date.strftime("%Y-%m-%d")}'
            
            print(f"   📡 API URL: {area_url}")
            
            try:
                # HTTP 요청으로 직접 확인
                response = requests.get(area_url, timeout=30)
                print(f"   📊 HTTP 상태: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"   ❌ API 오류: {response.status_code}")
                    print(f"   📄 응답 내용: {response.text[:500]}")
                    current_date = batch_end + timedelta(days=1)
                    continue
                
                # 응답 내용 확인
                content = response.text
                print(f"   📄 응답 길이: {len(content)} 바이트")
                print(f"   📄 첫 200자: {content[:200]}")
                
                # CSV로 파싱
                from io import StringIO
                df_batch = pd.read_csv(StringIO(content))
                
                print(f"   📊 컬럼: {list(df_batch.columns)}")
                print(f"   📊 데이터 행 수: {len(df_batch)}")
                
                if not df_batch.empty:
                    print(f"   ✅ {len(df_batch)}개 데이터 수신")
                    print(f"   📊 샘플 데이터:")
                    print(df_batch.head(2))
                    
                    for idx, row in df_batch.iterrows():
                        try:
                            # 날짜 변환
                            if isinstance(row['acq_date'], str):
                                acq_date = datetime.strptime(row['acq_date'], '%Y-%m-%d').date()
                            else:
                                acq_date = row['acq_date']
                            
                            # 요청한 날짜 범위 내의 데이터만 필터링
                            if start <= acq_date <= end:
                                fire_data = {
                                    'latitude': float(row['latitude']),
                                    'longitude': float(row['longitude']),
                                    'bright_ti4': float(row['bright_ti4']),
                                    'scan': float(row['scan']),
                                    'track': float(row['track']),
                                    'acq_date': acq_date,
                                    'acq_time': str(row['acq_time']).zfill(4),
                                    'satellite': str(row['satellite']),
                                    'instrument': str(row['instrument']),
                                    'confidence': str(row['confidence']),
                                    'version': str(row['version']),
                                    'bright_ti5': float(row['bright_ti5']),
                                    'frp': float(row['frp']),
                                    'daynight': str(row['daynight'])
                                }
                                all_fires.append(fire_data)
                        except Exception as e:
                            print(f"   ⚠️  행 {idx} 처리 중 오류: {e}")
                            print(f"   데이터: {row}")
                            continue
                else:
                    print(f"   ⚠️  데이터 없음")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ HTTP 요청 실패: {e}")
            except pd.errors.EmptyDataError:
                print(f"   ⚠️  빈 CSV 데이터")
            except Exception as e:
                print(f"   ❌ 배치 처리 실패: {e}")
                import traceback
                traceback.print_exc()
            
            # 다음 배치로 이동
            current_date = batch_end + timedelta(days=1)
        
        if not all_fires:
            print(f"\n⚠️  해당 기간에 수집된 화재 데이터가 없습니다.")
            print(f"   - API 응답이 비어있거나")
            print(f"   - 해당 날짜에 실제로 화재가 없었을 수 있습니다.\n")
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
        
        print(f"💾 {len(fire_objects)}개 객체 생성 완료")
        
        # Bulk Create (배치 저장)
        created_objects = FireDetection.objects.bulk_create(
            fire_objects, 
            batch_size=1000
        )
        
        print(f"✅ {len(created_objects)}개 데이터 저장 완료!\n")
        
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

def save_fire_data(days=10, satellite='VIIRS_NOAA20_NRT'):
    """
    최근 N일의 데이터 저장 (기존 호환성 유지)
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    return save_fire_data_by_date_range(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d'),
        satellite
    )

if __name__ == '__main__':
    # 테스트: 최근 7일 데이터 저장
    save_fire_data(days=7, satellite='VIIRS_NOAA20_NRT')