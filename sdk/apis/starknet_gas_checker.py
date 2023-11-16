import time

from constants import STARKNET_GET_LAST_BLOCK_ENDPOINT
from sdk.apis.base_api import BaseAPI
from sdk.helpers.logger import logger


class GasAPI(BaseAPI):
    def __init__(self, proxy: str) -> None:
        super().__init__(proxy, use_aiohttp=False)

    def get_last_block_gas_price(self):
        while True:
            try:
                response = self.session.get(url=STARKNET_GET_LAST_BLOCK_ENDPOINT)
                gas_price_hex = response.json()["gas_price"]
                return int(gas_price_hex, 16)
            except Exception as e:
                logger.warning(f"Starknet gas price fetch error: {str(e)}. Retrying in 30 sec")
                time.sleep(30)
