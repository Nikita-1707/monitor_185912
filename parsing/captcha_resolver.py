from typing import Optional

import requests

from parsing.tools import log


class Non200Error(Exception):
    ...


class CaptchaResolverError(Non200Error):
    ...


class CaptchaResolver:
    RESOLVE_CAPTCHA_URL = 'https://api.apitruecaptcha.org/one/gettext'

    def resolve_captcha(self, image_base64: str) -> Optional[str]:
        response = self._call_resolve(image_base64)

        result = self._handle_response(response)
        if result:
            return result

        return None

    def _handle_response(
        self,
        response: requests.Response,
    ) -> Optional[str]:
        if response.status_code == 503:
            raise CaptchaResolverError

        if response.status_code == 200:
            try:
                return response.json()['result']

            except Exception as e:
                log(
                    text='Error in TrueCaptchaResolver',
                    items=[response, e]
                )

        log('Unhandled true captcha response status code', [response, response.status_code, response.content])
        raise Non200Error('true captcha service error')

    def _call_resolve(
        self,
        image_base64: str
    ) -> requests.Response:
        data = {
            'userid': 'user285938',
            'apikey': 'NN3OXgM5TdsGVoPGZaPf',
            'data': image_base64,
            'tag': 'conl',
            'numeric': True,
            'mode': 'human',
            'len_str': 6,
        }
        return requests.post(url=self.RESOLVE_CAPTCHA_URL, json=data, timeout=60)
