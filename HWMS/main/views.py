# main/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import FireDetection
from .api import save_fire_data_by_date_range
from datetime import datetime, timedelta
import json
import traceback

def fire_map_view(request):
    """화재 지도 페이지"""
    try:
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
    """화재 데이터를 JSON으로 반환"""
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        fires = FireDetection.objects.all()
        
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
    except Exception as e:
        print(f"❌ API 오류: {e}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def fetch_and_save_fire_data(request):
    """특정 날짜 범위의 FIRMS 데이터를 가져와서 DB에 저장"""
    try:
        print(f"\n{'='*60}")
        print(f"📥 fetch_and_save_fire_data 호출됨")
        print(f"   Method: {request.method}")
        print(f"   Content-Type: {request.content_type}")
        print(f"{'='*60}\n")
        
        body = request.body.decode('utf-8')
        print(f"📄 요청 본문: {body}")
        
        data = json.loads(body)
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        print(f"📅 날짜: {start_date} ~ {end_date}")
        
        if not start_date or not end_date:
            return JsonResponse({
                'status': 'error',
                'message': '시작 날짜와 종료 날짜를 모두 입력해주세요.'
            }, status=400)
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if start > end:
                return JsonResponse({
                    'status': 'error',
                    'message': '시작 날짜가 종료 날짜보다 늦을 수 없습니다.'
                }, status=400)
            
            if (end - start).days > 30:
                return JsonResponse({
                    'status': 'error',
                    'message': '최대 30일까지만 조회 가능합니다.'
                }, status=400)
                
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'날짜 형식이 올바르지 않습니다: {str(e)}'
            }, status=400)
        
        print(f"🚀 save_fire_data_by_date_range 호출 시작...")
        count = save_fire_data_by_date_range(start_date, end_date)
        print(f"✅ save_fire_data_by_date_range 완료: {count}개")
        
        return JsonResponse({
            'status': 'success',
            'message': f'{count}개 데이터 저장 완료',
            'count': count,
            'start_date': start_date,
            'end_date': end_date
        })
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': f'요청 데이터 형식 오류: {str(e)}'
        }, status=400)
    except Exception as e:
        print(f"❌ 서버 오류: {e}")
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }, status=500)

def load_and_save_fire_data(request):
    """수동으로 최근 데이터 새로고침"""
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
        print(f"❌ 새로고침 오류: {e}")
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })