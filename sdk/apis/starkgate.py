import json

from constants import (
    EVM_STARKGATE_BRIDGE_CONTRACT_ADDRESS,
    STARKNET_ESTIMATE_MESSAGE_FEE_ENDPOINT,
    L1_ENTRY_POINT_SELECTOR,
    EVM_STARKGATE_ETH_BRIDGE_CONTRACT_ADDRESS_PAYLOAD
)
from sdk.apis.base_api import BaseAPI
from sdk.helpers.logger import logger
from sdk.models.token_amount import TokenAmount


class StarkgateAPI(BaseAPI):
    def __init__(self, proxy: str) -> None:
        super().__init__(proxy)

    def get_message_fee(self, amount: TokenAmount, starknet_address: str):
        try:
            headers = {"Content-Type": "application/json"}

            data = {
                "entry_point_selector": L1_ENTRY_POINT_SELECTOR,
                "from_address": int(EVM_STARKGATE_BRIDGE_CONTRACT_ADDRESS, 16),
                "to_address": EVM_STARKGATE_ETH_BRIDGE_CONTRACT_ADDRESS_PAYLOAD,
                "payload": [
                    starknet_address.lower(),
                    hex(amount.wei),
                    "0x0"
                ]
            }

            response = self.session.post(
                url=STARKNET_ESTIMATE_MESSAGE_FEE_ENDPOINT,
                data=json.dumps(data),
                headers=headers
            )

            return response.json()['overall_fee']

        except Exception as e:
            logger.error(f"Error while getting message fee. {e}")
            return False
