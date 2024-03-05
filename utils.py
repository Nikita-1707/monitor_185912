import contextlib
import datetime
import random
import re
import sqlite3
import string
import time
from random import randint
from typing import ContextManager, Tuple, List

import requests

from constants import (
    CREATE_ORDER,
    Genders,
    FakeMans,
    FakeWomans,
    COUNTRIES,
    CURRENT_EMAIL,
)
from google_api.google_master import GoogleMaster
from parsing.parser import ConsulParser, OrderBlocked
from parsing.tools import log
from sqlite_helpers.sql_master import SqlMaster


def random_string(length):
    # Define the characters that can be used in the string
    characters = string.ascii_letters
    # Use random.choices to pick characters at random
    return ''.join(random.choices(characters, k=length))


@contextlib.contextmanager
def open_connection() -> ContextManager[sqlite3.Connection]:
    conn = sqlite3.connect(SqlMaster.DB_NAME, check_same_thread=False)

    try:
        yield conn
    finally:
        conn.close()


def create_fake_order(
    country_id: int,
) -> None:
    parser = ConsulParser()

    gender = Genders.MAN if randint(0, 10) % 2 == 1 else Genders.WOMAN
    humans = FakeMans if gender == Genders.MAN else FakeWomans

    full_name = random.choice(humans)
    surname, name, last_name = full_name.split(' ')
    fake_phone = '+7(' + str(randint(100, 999)) + ')' + str(randint(1212222, 8989999))

    email_parts = CURRENT_EMAIL.split('@')
    email = email_parts[0] + '+' + random_string(5) + '@' + email_parts[1]

    url = f'{COUNTRIES[country_id].url}{CREATE_ORDER}'

    for _ in range(3):
        output = parser.create_order(
            url=url,
            surname=surname,
            name=name,
            last_name=last_name,
            phone=fake_phone,
            email=email,
            day_of_bd=randint(1, 27),
            month_of_bd=randint(1, 12),
            year_of_bd=str(randint(1965, 2001)),
            gender=gender,
        )

        if output:
            break

    if output is None:
        log('no output when creating order. BUG')
        return

    order_number, save_code = __extract_order_number_and_save_code(output.central_panel)

    with open_connection() as conn:
        sql_master = SqlMaster(conn)
        sql_master.add_order(
            order_number=order_number,
            save_code=save_code,
            country_id=country_id,
        )


def __extract_order_number_and_save_code(
    text: str,
) -> Tuple[int, str]:
    # Regular expression for the order number
    order_number_regex = r'Номер заявки\s+-\s+(\d+)'
    order_number_match = re.search(order_number_regex, text)
    if order_number_match:
        order_number = order_number_match.group(1)
    else:
        print('!!! Order number not found')
        return

    # Regular expression for the save code
    save_code_regex = r'Защитный код\s+-\s+([A-Z0-9]+)'
    save_code_match = re.search(save_code_regex, text)
    if save_code_match:
        save_code = save_code_match.group(1)
    else:
        print('!!! Save code not found')
        return

    return int(order_number), save_code


def accept_orders() -> None:
    print('accepting orders')

    google_master = GoogleMaster()
    parser = ConsulParser()

    messages = google_master.search_messages(
        # кверю не чекал
        query='newer_than:6h',
    )

    mes_len = len(messages)

    if mes_len == 0:
        return

    messages = messages
    for i, message in enumerate(messages):
        accepting_mail_text = google_master.read_accepting_email(message)

        try:
            url = fetch_first_href(accepting_mail_text)
        except IndexError:
            log('bad email', [accepting_mail_text])
            continue

        order_number, _, _ = fetch_id_cd_ems(url)
        parser.accept_by_url(url)

        with open_connection() as conn:
            SqlMaster(conn).update_if_accepted(order_number, 1)

        log(
            text=f'[{i}/{mes_len}] Order accepted',
            items=[url],
        )

    print('end' * 15)


def fetch_first_href(
    text: str,
) -> str:
    pattern = re.compile(r'href="([^"]+)"')
    matches = pattern.findall(text)
    return matches[0]


def fetch_id_cd_ems(
    url: str,
) -> Tuple[int, str, str]:
    id_match = re.search(r'id=([^&]+)', url)
    cd_match = re.search(r'cd=([^&]+)', url)
    ems_match = re.search(r'ems=([^&]+)', url)

    id_value = id_match.group(1) if id_match else None
    cd_value = cd_match.group(1) if cd_match else None
    ems_value = ems_match.group(1) if ems_match else None

    if any(
        value is None
        for value in (
            id_value,
            cd_value,
            ems_value,
        )
    ):
        log('FUCKin SHit')

    return int(id_value), cd_value, ems_value


def _get_orders_for_monitor(
    country_ids: List[int],
) -> List[Tuple[int, str, int, str, int]]:
    result = []
    with open_connection() as conn:
        sql_master = SqlMaster(conn)

        for country_id_ in country_ids:
            result.extend(sql_master.get_all_orders_by_country(country_id_))

    return result


def start_monitor(
    country_ids: List[int],
    max_orders_per_hour: int = 200,
) -> None:
    while True:
        orders = _get_orders_for_monitor(country_ids)
        orders_len = len(orders)

        if orders_len > max_orders_per_hour:
            orders = orders[:max_orders_per_hour]
            orders_len = len(orders)

        time_for_sleep = 3600 / orders_len
        random.shuffle(orders)

        log(f'orders len: {orders_len}, time for sleep: {time_for_sleep}')

        for order_number, save_code, country_id, time_for_visit, if_accepted in orders:
            if if_accepted == 0:
                log(f'Need to activate {order_number}\t{save_code}')
                continue

            if time_for_visit:
                log(f'Order {order_number} already confirmed')
                continue

            country_prefix = COUNTRIES[country_id].url

            start_time = datetime.datetime.now()

            try_to_create_visit_retry(
                url=f'{country_prefix}/queue/orderinfo.aspx',
                order_number=order_number,
                save_code=save_code,
            )

            runtime_seconds = (datetime.datetime.now() - start_time).seconds
            shifted_time_for_sleep = time_for_sleep - runtime_seconds

            if shifted_time_for_sleep > 0:
                time.sleep(shifted_time_for_sleep)


def try_to_create_visit_retry(
    url: str,
    order_number: int,
    save_code: str,
) -> None:
    for i in range(3):
        try:
            return try_to_create_visit(
                url, order_number, save_code,
            )

        except Exception as e:
            log(
                f'Error on creating visit for {order_number}. Attempt {i}. Error: {str(e)}',
            )


def try_to_create_visit(
    url: str,
    order_number: int,
    save_code: str,
) -> None:
    log(f'Try to create visit: {order_number}')
    parser = ConsulParser()

    try:
        out = parser.create_yearly_visit(
            url=url,
            order_number=order_number,
            save_code=save_code,
        )
    except OrderBlocked as error:
        log(str(error))
        with open_connection() as conn:
            sql_master = SqlMaster(conn)
            sql_master.delete_order(order_number)
            log(f'Order {order_number} deleted')

        return

    if out.central_panel:
        text = out.central_panel.lower()
        if (
            'нет свободного времени' in text
            or 'выбранное вами консульское действие востребовано' in text
        ):
            log('no windows for visit')
            return

        else:
            log('updating time for visit')
            with open_connection() as conn:
                sql_master = SqlMaster(conn)
                sql_master.update_order_time_for_visit(order_number, out.central_panel)

    else:
        log('NEED TO ACTIVATE', [url, order_number, save_code])


# def switch_visit_time(
#     order_number_1: str,
#     save_code_1: str,
#     order_number_2: str,
#     save_code_2: str,
# ) -> None:
#     parser = ConsulParser()
#     # parser.remove_visit(order_number_1, save_code_1)
#
#     url = ''
#     out = parser.create_yearly_visit(
#         order_number=order_number_2,
#         save_code=save_code_2,
#         url=url,
#         # non_stop=True, not releazed
#     )
#     log(
#         text='\n\n\n !!! Visit confirmed !!!',
#         items=[
#             out, f'''old: {order_number_1}\t{save_code_1}\nnew: {order_number_2}\t{save_code_2}'''
#         ]
#     )


def get_proxies() -> None:
    response = requests.get(
        'https://proxy.webshare.io/api/proxy/list/',
        headers={'Authorization': f'Token 87de6b5a1ac6283362101bb35952b526390c994e'},
        timeout=60,
    ).json()

    for proxies in response['results']:
        login = proxies['username']
        password = proxies['password']
        address = proxies['proxy_address']

        http_port = proxies['ports']['http']
        socks5_port = proxies['ports']['socks5']

        print(
            f'http://{login}:{password}@{address}:{http_port}'
            f'\nsocks5://{login}:{password}@{address}:{socks5_port}'
        )


def build_status_checker(
    url: str,
    order_number: int,
    save_code: str,
    n: int = 0,
) -> str:
    rand_time = 120 + randint(0, 5)
    return f"""
    try_to_create_visit_retry(
        url='{url}',
        order_number={order_number},
        save_code='{save_code}',
    )
    time.sleep({rand_time})"""


def get_code(country_id: int) -> None:
    with open_connection() as conn:
        sql_master = SqlMaster(conn)
        orders = sql_master.get_all_orders_by_country(country_id)

    for order in orders:
        order_number, save_code, country_id, time_for_visit = order

        if time_for_visit:
            log(f'Order {order_number} already visiting')
            continue

        country_url = COUNTRIES[country_id].url

        a = build_status_checker(
            url=f'{country_url}/queue/orderinfo.aspx',
            order_number=order_number,
            save_code=save_code,
        )

        print(a)


# get_code(41)
