import dataclasses
import datetime
import os
import time
from random import randint
from typing import List, Optional

from PIL.Image import Image
from selenium import webdriver
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select

from constants import COUNTRIES, CountryIds
from parsing.captcha_resolver import CaptchaResolver, CaptchaResolverError
from parsing.tools import log, cut_image, image_to_base64
from structures import TableData
from functools import wraps


def retry_on_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        for _ in range(10):
            try:
                return func(*args, **kwargs)

            except (CaptchaResolverError, LoginAuthError):
                pass

            except OrderBlocked as e:
                args[0].quit_browser()  # args[0] is assumed to be 'self'
                raise e

            except Exception as e:
                # Assuming self._save_page() is a method of the class
                args[0]._save_page()  # args[0] is assumed to be 'self'
                args[0].quit_browser()  # args[0] is assumed to be 'self'
                raise e

    return wrapper


class LoginAuthError(Exception):
    ...


class OrderBlocked(Exception):
    ...


@dataclasses.dataclass(frozen=True)
class ParserInput:
    domain: str
    order_id: str
    save_code: str


@dataclasses.dataclass(frozen=True)
class ParseOutput:
    main_content: str
    central_panel: str
    active_days: List[str]


@dataclasses.dataclass(frozen=True)
class CreateOrderOutput:
    central_panel: str


class ConsulParser:
    COUNTRIES_WITH_BLACK_CAPTCHA = (
        CountryIds.MADRID,
        CountryIds.BARCELONA,
        CountryIds.ARMENIA,
    )

    def __init__(
        self,
    ) -> None:
        self._driver: webdriver.Chrome = None

    def start_browser(
        self,
        url: str,
    ) -> None:
        self._driver = webdriver.Chrome()
        self._driver.implicitly_wait(1)
        self._driver.maximize_window()
        self._driver.get(url)

    def _resolve_captcha(
        self,
    ) -> None:
        if self._if_black_captcha:
            captcha_image = self._driver.find_element(
                by=By.ID,
                value='ctl00_MainContent_imgSecNum',
            ).screenshot_as_png

            new_img: Image = cut_image(
                image_bytes=captcha_image,
            )
            captcha_image = image_to_base64(new_img)

        else:
            captcha_image = self._driver.find_element(
                by=By.ID,
                value='ctl00_MainContent_imgSecNum',
            ).screenshot_as_base64

        code = None
        for i in range(3):
            try:
                code = CaptchaResolver().resolve_captcha(captcha_image)
                break

            except CaptchaResolverError:
                time.sleep(5)

        if code is None:
            self.quit_browser()
            raise CaptchaResolverError('Troubles with captcha resolver')

        self._fill_box(
            text=code,
            box_id='ctl00_MainContent_txtCode',
        )

    def _fill_box(
        self,
        text: str,
        box_id: str,
    ) -> None:
        self._driver.find_element(
            by=By.ID,
            value=box_id,
        ).send_keys(text)

    def _select_box(
        self,
        value_of_item: str,
        select_id: str,
    ) -> None:
        element = self._driver.find_element(
            by=By.ID,
            value=select_id,
        )

        select = Select(element)
        select.select_by_value(value_of_item)

    def _click_by_id(
        self,
        id_: str,
    ) -> bool:
        try:
            self._driver.find_element(
                by=By.ID,
                value=id_,
            ).click()
            return True
        except NoSuchElementException:
            return False

    def _fetch_text(
        self,
        content_id: str,
    ) -> str:
        return self._driver.find_element(
            by=By.ID,
            value=content_id,
        ).text

    def _fetch_dates_table(
        self,
        xpath: str,
    ) -> TableData:
        table = self._driver.find_element(
            by=By.XPATH,
            value=xpath,
        )

        td_elements = table.find_elements(
            by=By.TAG_NAME,
            value='td',
        )

        output = TableData.from_elements(td_elements)
        return output

    def quit_browser(self) -> None:
        self._driver.delete_all_cookies()
        self._driver.quit()

    @retry_on_login
    def accept_by_url(self, url: str) -> None:
        self.start_browser(url)

        self._resolve_captcha()

        self._click_by_id(
            id_='ctl00_MainContent_ButtonA',
        )
        if not self._if_login_success:
            self.quit_browser()
            raise LoginAuthError(
                'Login failed'
            )

        self.quit_browser()

    @retry_on_login
    def create_order(
        self,
        url: str,
        surname: str,
        name: str,
        last_name: str,
        phone: str,
        email: str,
        day_of_bd: int,
        month_of_bd: int,
        year_of_bd: str,
        gender: str,
    ) -> Optional[CreateOrderOutput]:
        self.start_browser(url)

        self._click_by_id(
            id_='Checkbox'
        )

        # sometimes need to click the second CheckBox
        try:
            self._click_by_id(
                id_='Checkbox2'
            )

        except NoSuchElementException:
            pass

        self._click_by_id(
            id_='ButtonNext'
        )

        time.sleep(2)

        if_previsitor = False
        if 'previsitor.aspx' in self._driver.current_url.lower():
            if_previsitor = True

            create_order_10_years = self._find_needed_option()
            create_order_10_years.click()

            time.sleep(1)
            self._click_by_id('Checkbox')
            self._click_by_id('ButtonNext')

        if 'visitor.aspx' not in self._driver.current_url.lower():
            print('SOmehinc dab')
            raise Exception('Bad place')

        self._fill_box(
            text=surname,
            box_id='ctl00_MainContent_txtFam',
        )

        self._fill_box(
            text=name,
            box_id='ctl00_MainContent_txtIm',
        )

        self._fill_box(
            text=last_name,
            box_id='ctl00_MainContent_txtOt',
        )

        self._fill_box(
            text=phone,
            box_id='ctl00_MainContent_txtTel',
        )

        self._fill_box(
            text=email,
            box_id='ctl00_MainContent_txtEmail',
        )

        day_value = f'0{day_of_bd}' if day_of_bd < 10 else str(day_of_bd)
        self._select_box(
            value_of_item=day_value,
            select_id='ctl00_MainContent_DDL_Day',
        )

        month_value = f'0{month_of_bd}' if month_of_bd < 10 else str(month_of_bd)
        self._select_box(
            value_of_item=month_value,
            select_id='ctl00_MainContent_DDL_Month',
        )

        self._fill_box(
            text=year_of_bd,
            box_id='ctl00_MainContent_TextBox_Year',
        )

        self._select_box(
            value_of_item=gender,
            select_id='ctl00_MainContent_DDL_Mr',
        )

        self._driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(1)
        self._driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        self._resolve_captcha()

        self._click_by_id(
            id_='ctl00_MainContent_ButtonA'
        )

        self._click_by_id('ctl00_MainContent_HyperLinkNext')

        if not if_previsitor:
            create_order_10_years = self._find_needed_option()

            href = create_order_10_years.find_element(
                by=By.TAG_NAME,
                value='a',
            ).get_attribute('href')
            self._driver.get(href)

        # иногда нужно нажать галочку
        self._click_by_id('ctl00_MainContent_CheckBoxID')
        # иногда нужно выбрать: паспорт или паспорт ребенку, затем стандартное флоу
        self._click_by_id('ctl00_MainContent_ButtonA')

        self._click_by_id('ctl00_MainContent_CheckBoxID')
        self._click_by_id('ctl00_MainContent_ButtonA')

        self._click_by_id('ctl00_MainContent_CheckBoxList1_0')
        self._click_by_id('ctl00_MainContent_ButtonQueue')

        central_panel = self._driver.find_element(
            by=By.ID,
            value='center-panel',
        )

        ps = central_panel.find_elements(
            by=By.TAG_NAME,
            value='p',
        )

        # for p in ps:
        #     if 'зарегистрироваться в списке ожидания' in p.text.lower():
        #         p.click()

        text = ps[0].text

        return CreateOrderOutput(
            central_panel=text,
        )

    @retry_on_login
    def create_yearly_visit(
        self,
        url: str,
        order_number: int,
        save_code: str,
    ) -> ParseOutput:
        self._login(url, order_number, save_code)

        try:
            main_content = self._fetch_text(
                content_id='ctl00_MainContent_Content',
            )

        except Exception as error:
            log(f'Got parser error: {error}')
            raise LoginAuthError('Login failed')

        # Going to the next page
        if_button_exist = self._click_by_id(
            id_='ctl00_MainContent_ButtonB',
        )

        if not if_button_exist:
            log('Bad Place 1. Something error occurs')
            self.quit_browser()
            return ParseOutput(
                main_content=main_content,
                active_days=[],
                central_panel='',
            )

        if self._if_consul_502:
            log('Consul 502')
            self.quit_browser()
            return ParseOutput(
                main_content=main_content,
                active_days=[],
                central_panel='',
            )

        if self._if_order_blocked:
            raise OrderBlocked(f'Blocked: {order_number}\t{save_code}')

        for _ in range(3):
            dates_table = self._fetch_dates_table(
                xpath='//*[@id="ctl00_MainContent_Calendar"]',
            )

            active_days = [
                day
                for day in dates_table.active_days
            ]

            selected_month = dates_table.current_month.text
            active_days_text = [day.text for day in active_days]

            if active_days_text:
                log(
                    text=f'Active days in {selected_month}: {active_days_text}',
                )

            if len(active_days) > 0:
                try:
                    day_link_js = active_days[0].find_element(
                        by=By.TAG_NAME,
                        value='a',
                    ).get_attribute('href')
                    self._driver.execute_script(day_link_js)
                    break

                except StaleElementReferenceException:
                    print('WTFFF')

                except Exception as error:
                    self._save_page('NOT_confirmed')
                    log('EBAT')
                    raise error

            try:
                month_link_js = dates_table.button_forward.find_element(
                    by=By.TAG_NAME,
                    value='a',
                ).get_attribute('href')
            except NoSuchElementException:
                log('no free dates')

                central_panel = self._fetch_text(
                    content_id='center-panel'
                )
                return ParseOutput(
                    main_content=main_content,
                    active_days=[],
                    central_panel=central_panel,
                )

            log('go to next month')
            self._driver.execute_script(month_link_js)

        self._try_to_click_to_confirm()

        log(f'Visit confirmed: {order_number}\t{save_code}')

        self._save_page('confirm_')

        central_panel = self._fetch_text(
            content_id='center-panel'
        )

        self.quit_browser()

        return ParseOutput(
            central_panel=central_panel,
            active_days=active_days_text,
            main_content=main_content,
        )

    def _login(
        self,
        url: str,
        order_number: int,
        save_code: str,
    ) -> None:
        self.start_browser(url)

        self._fill_box(
            text=str(order_number),
            box_id='ctl00_MainContent_txtID',
        )
        self._fill_box(
            text=save_code,
            box_id='ctl00_MainContent_txtUniqueID',
        )

        self._resolve_captcha()

        self._click_by_id(
            id_='ctl00_MainContent_ButtonA',
        )

    def _try_to_click_to_confirm(self) -> bool:
        try:
            radio_button_list = self._driver.find_element(
                by=By.ID,
                value='ctl00_MainContent_RadioButtonList1',
            )

        except NoSuchElementException:
            print('FUCK YUU')
            return False

        visiting_windows = radio_button_list.find_elements(
            by=By.TAG_NAME,
            value='td',
        )

        for window in visiting_windows:
            text = window.text
            log(f'Parsed free window text: {text}')

        visiting_windows[0].find_element(
            by=By.TAG_NAME,
            value='input',
        ).click()

        # confirm visit
        return self._click_by_id(
            id_='ctl00_MainContent_Button1',
        )

    def _find_needed_option(self) -> WebElement:
        reasons = self._driver.find_element(
            by=By.ID,
            value='reasons',
        )
        elements = reasons.find_elements(
            by=By.TAG_NAME,
            value='dd',
        )

        return elements[self._number_of_element_for_create_order]

    def _save_page(
        self,
        prefix: str = '',
    ) -> None:
        page_source = self._driver.page_source

        if page_source is None:
            log('Page source is None. Cannot save page')
            return

        now_str = datetime.datetime.now().isoformat()
        page_path = os.path.expanduser(f'~/saved_pages/{prefix}saved_page{now_str}.html')
        with open(page_path, mode='w') as file:
            file.write(page_source)

    @property
    def _if_login_success(self) -> bool:
        check_list = [
            'ctl00_MainContent_lblCodeErr',
            'ctl00_MainContent_Label_Message',
        ]

        for check_id in check_list:
            try:
                element = self._driver.find_element(
                    by=By.ID,
                    value=check_id,
                )

                if element:
                    return False

            except NoSuchElementException:
                continue

        return True

    @property
    def _if_consul_502(self) -> bool:
        body = self._driver.find_element(
            by=By.TAG_NAME,
            value='body'
        )

        if '502 - Bad Gateway .' in body.text:
            log('Got 502')
            return True

        return False

    @property
    def _if_order_blocked(self) -> bool:
        try:
            text = self._fetch_text('ctl00_MainContent_Label_Message')

        except NoSuchElementException:
            return False

        if 'ваша заявка заблокирована' in text.lower():
            return True

        try:
            text = self._fetch_text('center-panel')

        except NoSuchElementException:
            return False

        if 'заблокирована' in text.lower():
            return True

        return False

    @property
    def _if_black_captcha(self) -> bool:
        for country_id in self.COUNTRIES_WITH_BLACK_CAPTCHA:
            country_url = COUNTRIES[country_id].url

            if country_url in self._driver.current_url:
                return True

        return False

    @property
    def _number_of_element_for_create_order(self) -> int:
        n = 1

        if any(
            city in self._driver.current_url
            for city in [
                'telaviv',
                'hanoi',
                'yerevan',
                'budapest',
            ]
        ):
            n = 2

        elif any(
            city in self._driver.current_url
            for city in [
                'beijing',
                'amman.kdm',
            ]
        ):
            n = 5

        elif any(
            city in self._driver.current_url
            for city in [
                'argentina',
            ]
        ):
            n = 0  # zagran
            # n = ...  # notariat

        elif any(
            city in self._driver.current_url
            for city in [
                'brussels',
            ]
        ):
            n = 4  # zagran
            # n = 2  # notariat

        elif any(
            city in self._driver.current_url
            for city in [
                'sarajevo',
                'dk.kdmid',
                'roma.kd',
            ]
        ):
            n = 1  # zagran
            # n = ...

        elif any(
            city in self._driver.current_url
            for city in [
                'vilnius',
                'luxembourg',
            ]
        ):
            n = 6  # zagran
            # n = ...

        elif any(
            city in self._driver.current_url
            for city in [
                'dublin',
            ]
        ):
            n = 7  # zagran
            # n = ...

        elif any(
            city in self._driver.current_url
            for city in [
                'barcelona',
            ]
        ):

            n = 8 if randint(0, 10) % 2 == 1 else 9

        return n
