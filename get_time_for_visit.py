import re

from constants import CountryIds
from sqlite_helpers.sql_master import SqlMaster
from utils import open_connection


country = CountryIds.BARCELONA

date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
time_pattern = r'(\d{2}:\d{2})'


with open_connection() as conn:
    sql_master = SqlMaster(conn)

    orders = sql_master.get_confirmed_orders_by_country(country)

    print('...')
    for order_number, save_code, _, time_for_visit, _ in orders:
        # Search for the pattern in the text
        date_match = re.search(date_pattern, time_for_visit)
        time_match = re.search(time_pattern, time_for_visit)

        date = date_match.group(1)
        time = time_match.group(1)

        print(f'{order_number}\t{save_code}\t{date} {time}')
