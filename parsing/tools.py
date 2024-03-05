import base64
import datetime
import io
from typing import List, Any

import requests
from PIL import Image

from constants import DISABLE_LOG


def log(
    text: str,
    items: List[Any] = None,
    force: bool = False,
) -> None:
    if DISABLE_LOG and not force:
        return

    items = items or []

    print(f'[{datetime.datetime.now().isoformat()}] LOG: {text}')

    for item in items:
        print(f'Item: {item}')


def cut_image(
    image_bytes: bytes,
    x1: int = 200,
    y1: int = 0,
    x2: int = 400,
    y2: int = 177,
) -> Image:
    captcha = Image.open(io.BytesIO(image_bytes))
    return captcha.crop(box=(x1, y1, x2, y2))


def image_to_base64(
    pil_image: Image,
    image_format='PNG',
) -> str:
    """
    Convert a PIL Image to a base64-encoded string.

    :param pil_image: PIL Image object to be converted
    :param image_format: String specifying the format of the source image ('JPEG', 'PNG', etc.)
    :return: Base64-encoded string of the image
    """
    # Create a BytesIO buffer to hold the bytes
    buffer = io.BytesIO()

    # Save the image to the buffer using the specified format
    pil_image.save(buffer, format=image_format)

    # Get the byte data from the buffer
    img_bytes = buffer.getvalue()

    # Encode the bytes in base64
    img_base64 = base64.b64encode(img_bytes)

    # Convert the base64 bytes to string and return
    return img_base64.decode('utf-8')


def download_image_by_link(
    self,
    image_link: str,
) -> None:
    image_data = requests.get(image_link).content
    with open(self.CAPTCHA_FILENAME, 'wb') as handler:
        handler.write(image_data)
