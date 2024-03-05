from sqlite_helpers.sql_master import SqlMaster
from utils import open_connection

with open_connection() as conn:
    sql_master = SqlMaster(conn)
    sql_master.create_orders_table()
