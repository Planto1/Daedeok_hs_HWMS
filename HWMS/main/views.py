# views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import FireDetection
from .api import save_fire_data

def fire_map_view(request):
    """화재 지도 페이지 - 자동으로 데이터 저장"""
    try:
        # DB가 비어있으면 데이터 저장
        if FireDetection.objects.count() == 0:
            save_fire_data()
            print("데이터 자동 저장 완료!")
    except Exception as e:
        print(f"데이터 저장 중 오류: {e}")
    
    return render(request, 'fire_map.html')

def fire_data_api(request):
    """화재 데이터를 JSON으로 반환"""
    fires = FireDetection.objects.all().values(
        'latitude', 
        'longitude', 
        'frp', 
        'bright_ti4',
        'acq_date',
        'acq_time',
        'satellite',
        'confidence'
    )
    
    fire_list = list(fires)
    for fire in fire_list:
        fire['acq_date'] = str(fire['acq_date'])
    
    return JsonResponse(fire_list, safe=False)

def load_and_save_fire_data(request):
    """수동으로 데이터 새로고침"""
    try:
        # 기존 데이터 삭제
        FireDetection.objects.all().delete()
        # 새 데이터 저장
        count = save_fire_data()
        return JsonResponse({'status': 'success', 'message': f'{count}개 데이터 저장 완료'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})