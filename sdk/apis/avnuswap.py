from config import SLIPPAGE
from constants import (
    AVNU_SWAP_BUILD_URL,
    AVNU_SWAP_QUOTES_URL
)

from sdk.apis.base_api import BaseAPI


class AvnuSwapAPI(BaseAPI):
    def __init__(self, proxy: str) -> None:
        super().__init__(proxy, use_aiohttp=True)

    async def get_avnu_swap_quote_id(self, from_token: str, to_token: str, amount: int):
        params = {
            "sellTokenAddress": from_token,
            "buyTokenAddress": to_token,
            "sellAmount": hex(amount),
            "excludeSources": "Ekubo"
        }

        response = await self.session.get(url=AVNU_SWAP_QUOTES_URL, params=params)
        response_data = await response.json()
        quote_id = response_data[0]["quoteId"]

        return quote_id

    async def get_build_avnu_swap_tx(self, quote_id: str, recipient: int):
        data = {
            "quoteId": quote_id,
            "takerAddress": hex(recipient),
            "slippage": float(SLIPPAGE / 100),
        }

        response = await self.session.post(url=AVNU_SWAP_BUILD_URL, json=data)
        response_data = await response.json()

        return response_data
