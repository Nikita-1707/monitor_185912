from constants import CountryIds
from utils import start_monitor

start_monitor(
    country_ids=[
        CountryIds.MADRID,
    ],
    max_orders_per_hour=60,
)
