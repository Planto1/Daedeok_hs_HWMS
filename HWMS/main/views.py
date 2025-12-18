# main/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import FireDetection
from .api import save_fire_data_by_date_range
from datetime import datetime, timedelta

def fire_map_view(request):
    """화재 지도 페이지"""
    try:
        # DB가 비어있으면 최근 7일 데이터 자동 저장
        if FireDetection.objects.count() == 0:
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            count = save_fire_data_by_date_range(
                start_date=week_ago.strftime('%Y-%m-%d'),
                end_date=today.strftime('%Y-%m-%d')
            )
            print(f"✅ 초기 데이터 자동 저장 완료: {count}개")
    except Exception as e:
        print(f"❌ 데이터 저장 중 오류: {e}")
    
    return render(request, 'fire_map.html')

def fire_data_api(request):
    """
    화재 데이터를 JSON으로 반환 (날짜 필터링 지원)
    
    Query Parameters:
        - start_date: 시작 날짜 (YYYY-MM-DD)
        - end_date: 종료 날짜 (YYYY-MM-DD)
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    fires = FireDetection.objects.all()
    
    # 날짜 필터링
    if start_date:
        fires = fires.filter(acq_date__gte=start_date)
    if end_date:
        fires = fires.filter(acq_date__lte=end_date)
    
    fires = fires.values(
        'id',
        'latitude', 
        'longitude', 
        'frp', 
        'bright_ti4',
        'acq_date',
        'acq_time',
        'satellite',
        'confidence'
    ).order_by('-acq_date', '-acq_time')
    
    fire_list = list(fires)
    for fire in fire_list:
        fire['acq_date'] = str(fire['acq_date'])
    
    return JsonResponse(fire_list, safe=False)

@require_http_methods(["POST"])
def fetch_and_save_fire_data(request):
    """
    특정 날짜 범위의 FIRMS 데이터를 가져와서 DB에 저장
    
    POST Body:
        - start_date: 시작 날짜 (YYYY-MM-DD)
        - end_date: 종료 날짜 (YYYY-MM-DD)
    """
    import json
    
    try:
        data = json.loads(request.body)
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not start_date or not end_date:
            return JsonResponse({
                'status': 'error',
                'message': '시작 날짜와 종료 날짜를 모두 입력해주세요.'
            }, status=400)
        
        # 날짜 유효성 검사
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if start > end:
                return JsonResponse({
                    'status': 'error',
                    'message': '시작 날짜가 종료 날짜보다 늦을 수 없습니다.'
                }, status=400)
            
            # 최대 30일 제한
            if (end - start).days > 30:
                return JsonResponse({
                    'status': 'error',
                    'message': '최대 30일까지만 조회 가능합니다.'
                }, status=400)
                
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': '날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)'
            }, status=400)
        
        # FIRMS API에서 데이터 가져와서 저장
        count = save_fire_data_by_date_range(start_date, end_date)
        
        return JsonResponse({
            'status': 'success',
            'message': f'{count}개 데이터 저장 완료',
            'count': count,
            'start_date': start_date,
            'end_date': end_date
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def load_and_save_fire_data(request):
    """수동으로 최근 데이터 새로고침 (기존 호환성 유지)"""
    try:
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        count = save_fire_data_by_date_range(
            start_date=week_ago.strftime('%Y-%m-%d'),
            end_date=today.strftime('%Y-%m-%d')
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'{count}개 데이터 저장 완료'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

def fire_stats_api(request):
    """화재 통계 API"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    fires = FireDetection.objects.all()
    
    if start_date:
        fires = fires.filter(acq_date__gte=start_date)
    if end_date:
        fires = fires.filter(acq_date__lte=end_date)
    
    total = fires.count()
    high = fires.filter(confidence='h').count()
    nominal = fires.filter(confidence='n').count()
    low = fires.filter(confidence='l').count()
    
    # 날짜별 분포
    date_distribution = {}
    for fire in fires.values('acq_date').annotate(count=models.Count('id')):
        date_distribution[str(fire['acq_date'])] = fire['count']
    
    return JsonResponse({
        'total': total,
        'high_confidence': high,
        'nominal_confidence': nominal,
        'low_confidence': low,
        'date_distribution': date_distribution
    })