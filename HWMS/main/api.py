import requests
import pandas as pd


class Firms():
    pass


MAP_KEY = '5872ff30914a691ad9aa8eaf6e5410a7'


'''
da_url = 'https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/' + MAP_KEY + '/all'
df = pd.read_csv(da_url)
print(df)
'''

area_url = 'https://firms.modaps.eosdis.nasa.gov/api/area/csv/' + MAP_KEY + '/VIIRS_NOAA20_NRT/world/1'
df_area = pd.read_csv(area_url)

print(df_area)

