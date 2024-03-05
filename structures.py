import dataclasses
from typing import List, Optional

from selenium.webdriver.remote.webelement import WebElement


@dataclasses.dataclass
class Order:
    _DELEMITER = '(dele=miter)'
    _DELEMITER2 = '(dele2=miter2)'

    order_number: str
    save_code: str
    country_id: int
    description: str

    def __str__(self):
        # Create a string representation of the Order object
        return (
            f'Order('
            f'order_number{self._DELEMITER}{self.order_number}'
            f'{self._DELEMITER2}save_code{self._DELEMITER}{self.save_code}'
            f'{self._DELEMITER2}country_id{self._DELEMITER}{self.country_id}'
            f'{self._DELEMITER2}description{self._DELEMITER}{self.description}'
            f')'
        )

    @classmethod
    def from_str(cls, order_str):
        # Assuming the string format is the same as __str__ output
        # Remove the 'Order(' prefix and the closing ')', then split by ', '
        parts = order_str[len('Order('):-1].split(cls._DELEMITER2)
        # Parse each part into a key-value pair
        kwargs = {}
        for part in parts:
            key, value = part.split(cls._DELEMITER)

            if key == 'country_id':
                value = int(value)

            kwargs[key] = value
        # Create a new Order instance with the parsed values
        return cls(**kwargs)


@dataclasses.dataclass
class Orders:
    _DELEMITER = 'SuPeRd123ElMIteR'

    orders: List['Order']

    def __str__(self):
        # Join the string representations of all Order objects in the list
        return self._DELEMITER.join(str(order) for order in self.orders)

    @classmethod
    def from_str(cls, orders_str: str) -> Optional['Orders']:
        if (
            not orders_str
            or orders_str == '[]'
        ):
            return None

        order_strs = orders_str.strip().split(cls._DELEMITER)
        return cls(orders=[
            Order.from_str(order_str)
            for order_str in order_strs
        ])

    @classmethod
    def from_str_array(cls, orders_str: str) -> List[Order]:
        if (
            not orders_str
            or orders_str == '[]'
        ):
            return []

        order_strs = orders_str.strip().split(cls._DELEMITER)
        return [
            Order.from_str(order_str)
            for order_str in order_strs
        ]


@dataclasses.dataclass(frozen=True)
class Country:
    name: str
    url: str


@dataclasses.dataclass(frozen=True)
class TableData:
    current_month: WebElement
    button_back: WebElement
    button_forward: WebElement
    day_1: WebElement
    day_2: WebElement
    day_3: WebElement
    day_4: WebElement
    day_5: WebElement
    day_6: WebElement
    day_7: WebElement
    day_8: WebElement
    day_9: WebElement
    day_10: WebElement
    day_11: WebElement
    day_12: WebElement
    day_13: WebElement
    day_14: WebElement
    day_15: WebElement
    day_16: WebElement
    day_17: WebElement
    day_18: WebElement
    day_19: WebElement
    day_20: WebElement
    day_21: WebElement
    day_22: WebElement
    day_23: WebElement
    day_24: WebElement
    day_25: WebElement
    day_26: WebElement
    day_27: WebElement
    day_28: WebElement
    day_29: WebElement
    day_30: WebElement
    day_31: WebElement
    day_32: WebElement
    day_33: WebElement
    day_34: WebElement
    day_35: WebElement
    day_36: WebElement
    day_37: WebElement
    day_38: WebElement
    day_39: WebElement

    @classmethod
    def from_elements(
        cls,
        elements: List[WebElement],
    ) -> 'TableData':
        return TableData(
            current_month=elements[2],
            button_back=elements[1],
            button_forward=elements[3],
            day_1=elements[4],
            day_2=elements[5],
            day_3=elements[6],
            day_4=elements[7],
            day_5=elements[8],
            day_6=elements[9],
            day_7=elements[10],
            day_8=elements[11],
            day_9=elements[12],
            day_10=elements[13],
            day_11=elements[14],
            day_12=elements[15],
            day_13=elements[16],
            day_14=elements[17],
            day_15=elements[18],
            day_16=elements[19],
            day_17=elements[20],
            day_18=elements[21],
            day_19=elements[22],
            day_20=elements[23],
            day_21=elements[24],
            day_22=elements[25],
            day_23=elements[26],
            day_24=elements[27],
            day_25=elements[28],
            day_26=elements[29],
            day_27=elements[30],
            day_28=elements[31],
            day_29=elements[32],
            day_30=elements[33],
            day_31=elements[34],
            day_32=elements[35],
            day_33=elements[36],
            day_34=elements[37],
            day_35=elements[38],
            day_36=elements[39],
            day_37=elements[40],
            day_38=elements[41],
            day_39=elements[42],
        )

    @property
    def active_days(self) -> List[WebElement]:
        return [
            day
            for day in self.all_days
            if not day.get_attribute('disabled')
        ]

    @property
    def all_days(self) -> List[WebElement]:
        return [
            self.day_1,
            self.day_2,
            self.day_3,
            self.day_4,
            self.day_5,
            self.day_6,
            self.day_7,
            self.day_9,
            self.day_10,
            self.day_11,
            self.day_12,
            self.day_13,
            self.day_14,
            self.day_15,
            self.day_16,
            self.day_17,
            self.day_18,
            self.day_19,
            self.day_20,
            self.day_21,
            self.day_22,
            self.day_23,
            self.day_24,
            self.day_25,
            self.day_26,
            self.day_27,
            self.day_28,
            self.day_29,
            self.day_30,
            self.day_31,
            self.day_32,
            self.day_33,
            self.day_34,
            self.day_35,
            self.day_36,
            self.day_37,
            self.day_39,
        ]
