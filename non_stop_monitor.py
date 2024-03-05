from constants import COUNTRIES, CountryIds
from parsing.parser import ConsulParser
from parsing.tools import log
from sqlite_helpers.sql_master import SqlMaster
from utils import open_connection


country_id = CountryIds.MADRID
order_number = ...
save_code = '...'

parser = ConsulParser()

country_prefix = COUNTRIES[country_id].url

log('Non stop checking started')
while True:
    out = parser.create_yearly_visit(
        url=f'{country_prefix}/queue/orderinfo.aspx',
        order_number=order_number,
        save_code=save_code,
    )

    if out.central_panel:
        text = out.central_panel.lower()
        if (
            'нет свободного времени' in text
            or 'выбранное вами консульское действие востребовано' in text
        ):
            log('no windows for visit')
            continue

        else:
            log('updating time for visit')
            with open_connection() as conn:
                sql_master = SqlMaster(conn)
                sql_master.update_order_time_for_visit(order_number, out.central_panel)

            break


log('check result')
