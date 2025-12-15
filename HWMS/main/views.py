from django.shortcuts import render
from django.http import JsonResponse
from .models import FireDetection


# Create your views here.
def index(request):
    return render(request,'main/index.html')

'''
def fire_map_view(request):
    """지도 페이지"""
    return render(request, 'fire_map.html')
'''

def fire_data_api(request):
    """화재 데이터를 JSON으로 반환"""
    fires = FireDetection.objects.all().values(
        'latitude', 
        'longitude', 
        'frp', 
        'bright_ti4',
        'acq_date',
        'acq_time',
        'satellite'
    )
    
    fire_list = []
    for fire in fires:
        fire_list.append({
            'latitude': fire['latitude'],
            'longitude': fire['longitude'],
            'frp': fire['frp'],
            'bright_ti4': fire['bright_ti4'],
            'acq_date': str(fire['acq_date']),
            'acq_time': fire['acq_time'],
            'satellite': fire['satellite']
        })
    
    return JsonResponse(fire_list, safe=False)