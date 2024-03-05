import os
from sqlite3 import Connection, IntegrityError
from typing import Tuple, List


class OrderNotFound(Exception):
    pass


ORDER_TUPLE = Tuple[int, str, int, str, int]


class SqlMaster:
    DB_NAME = os.path.expanduser('~/tg_bot.db')
    ORDERS_TABLE_NAME = 'orders'

    def __init__(
        self,
        conn: Connection,
    ) -> None:
        self._conn = conn

    def create_orders_table(self) -> None:
        self._conn.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {self.ORDERS_TABLE_NAME} (
                order_number INTEGER PRIMARY KEY,
                save_code TEXT NOT NULL,
                country_id INTEGER NOT NULL,
                time_for_visit TEXT,
                if_accepted INTEGER DEFAULT 0
            )
        '''
        )
        self._conn.commit()

    def add_order(
        self,
        order_number: int,
        save_code: str,
        country_id: int,
        time_for_visit: str = None,
        if_accepted: int = 0,
    ) -> bool:
        try:
            self._conn.execute(
                f'''
                INSERT INTO {self.ORDERS_TABLE_NAME} (
                order_number,
                save_code,
                country_id,
                time_for_visit,
                if_accepted
                ) VALUES (?, ?, ?, ?, ?)
            ''', (order_number, save_code, country_id, time_for_visit, if_accepted)
            )

        except IntegrityError:
            print(f'order with id {order_number} already exist')
            return False

        self._conn.commit()
        return True

    def get_all_orders(self) -> List[ORDER_TUPLE]:
        orders = self._conn.execute(
            f'SELECT * FROM {self.ORDERS_TABLE_NAME}',
        ).fetchall()

        return orders

    def get_all_orders_by_country(self, country_id: int) -> List[ORDER_TUPLE]:
        orders = self._conn.execute(
            f'SELECT * FROM {self.ORDERS_TABLE_NAME} WHERE country_id = ?', (country_id, )
        ).fetchall()

        return orders

    def get_confirmed_orders_by_country(self, country_id: int) -> List[ORDER_TUPLE]:
        orders = self._conn.execute(
            f"SELECT * FROM {self.ORDERS_TABLE_NAME} WHERE country_id = ? and time_for_visit != ''",
            (country_id, )
        ).fetchall()

        return orders

    def get_order(
        self,
        order_number: int,
    ) -> Tuple:
        order = self._conn.execute(
            f'SELECT * FROM {self.ORDERS_TABLE_NAME} WHERE order_number = ?',
            (order_number,)
        ).fetchone()

        if order is None:
            raise OrderNotFound(f'order with id {order_number} not found')

        return order

    def get_order_save_code(self, order_number: int) -> str:
        return self.get_order(order_number)[1]

    def get_order_country_id(self, order_number: int) -> int:
        return self.get_order(order_number)[2]

    def get_order_time_for_visit(self, order_number: int) -> str:
        return self.get_order(order_number)[3]

    def get_order_if_accepted(self, order_number: int) -> str:
        return self.get_order(order_number)[4]

    def check_order(
        self,
        order_number: int,
    ) -> bool:
        try:
            self.get_order(order_number)
        except OrderNotFound:
            return False

        return True

    def update_order_time_for_visit(self, order_number: int, time_for_visit: str) -> None:
        self._conn.execute(
            f'''
            UPDATE {self.ORDERS_TABLE_NAME}
            SET time_for_visit = ?
            WHERE order_number = ?
        ''', (time_for_visit, order_number)
        )
        self._conn.commit()

    def update_if_accepted(self, order_number: int, if_accepted: int) -> None:
        self._conn.execute(
            f'''
            UPDATE {self.ORDERS_TABLE_NAME}
            SET if_accepted = ?
            WHERE order_number = ?
        ''', (if_accepted, order_number)
        )
        self._conn.commit()

    def delete_order(self, order_number: int) -> None:
        self._conn.execute(
            f'''
            DELETE FROM {self.ORDERS_TABLE_NAME}
            WHERE order_number = ?
        ''', (order_number,)
        )
        self._conn.commit()
