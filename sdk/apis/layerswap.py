import uuid
from typing import Optional

from fake_useragent import UserAgent

from constants import (
    LAYERSWAP_TRANSFER_TO_ADDRESS_ENDPOINT,
    LAYERSWAP_SWAPS_ENDPOINT,
    LAYERSWAP_IDENTITY_ENDPOINT,
    LAYERSWAP_DEFAULT_API_HEADERS
)
from sdk.apis.base_api import BaseAPI
from sdk.helpers.logger import logger
from sdk.models.layerswap_swap_config import LayerswapDataItem


class LayerSwapAPI(BaseAPI):
    def __init__(self, proxy: str):
        super().__init__(proxy)

        self.user_agent = UserAgent().random
        self.access_token = self.get_identity_tokens()["access_token"]

    def construct_request_headers(
            self,
            accept: Optional[str] = None,
            accept_language: Optional[str] = None,
            x_ls_correlation_id: Optional[str] = None,
            content_type: Optional[str] = None,
            include_access_token: bool = True
    ):
        headers = LAYERSWAP_DEFAULT_API_HEADERS.copy()
        headers['User-Agent'] = self.user_agent

        if accept:
            headers['accept'] = accept
        if accept_language:
            headers['accept-language'] = accept_language
        if x_ls_correlation_id:
            headers['x-ls-correlation-id'] = x_ls_correlation_id
        if content_type:
            headers['content-type'] = content_type
        if include_access_token:
            headers['authorization'] = f"Bearer {self.access_token}"

        return headers

    def get_swap(self, swap_id: str):
        try:
            headers = self.construct_request_headers()
            url = f"{LAYERSWAP_SWAPS_ENDPOINT}/{swap_id}"
            response = self.session.get(url=url, headers=headers)

            return response.json()['data']

        except Exception as e:
            logger.error(f"Error while get swap with id {swap_id}: {e}")

    def create_swap(self, data_item: LayerswapDataItem):
        try:
            x_ls_correlation_id = str(uuid.uuid4())

            headers = self.construct_request_headers(
                accept="application/json, text/plain, */*",
                accept_language="en-US,en;q=0.9",
                content_type="application/json",
                x_ls_correlation_id=x_ls_correlation_id
            )
            response = self.session.post(
                url=LAYERSWAP_SWAPS_ENDPOINT,
                data=data_item.to_json(),
                headers=headers
            )

            return response.json()['data']

        except Exception as e:
            logger.error(f"Error while create swap: {e}")

    def get_deposit_address(self, grab_url):
        try:
            headers = self.construct_request_headers()
            response = self.session.post(
                url=f"{LAYERSWAP_TRANSFER_TO_ADDRESS_ENDPOINT}/{grab_url}",
                headers=headers
            )

            return response.json()['data']

        except Exception as e:
            logger.error(f"Error while getting deposit address: {e}")

    def get_identity_tokens(self):
        try:
            response = self.session.post(
                url=LAYERSWAP_IDENTITY_ENDPOINT,
                data={
                    "client_id": "layerswap_bridge_ui",
                    "grant_type": "credentialless"
                },
                headers=LAYERSWAP_DEFAULT_API_HEADERS
            )

            return response.json()

        except Exception as e:
            logger.error(f"Error while getting identity tokens: {e}")
