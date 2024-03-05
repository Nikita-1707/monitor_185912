from constants import CountryIds
from utils import create_fake_order

country_ids = [
    CountryIds.BARCELONA
]

n = 100
for country_id in country_ids:
    for i in range(n):
        try:
            create_fake_order(country_id)
            print(f'[{i}/{n}] Created order')
        except Exception as e:
            print('Got error')
            print(e)
            print(f'[{i}/{n}] NOT Created order')
