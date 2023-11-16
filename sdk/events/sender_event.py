import random

from config import (
    ATTEMPTS_COUNT,
    ROUND_TO,
    STARKNET_TRANSFER_ETH_KEEP_AMOUNT
)
from constants import STARKNET_ETH_TOKEN_ADDRESS
from sdk.events.base_event import BaseEvent
from sdk.helpers.decorators import starknet_retry
from sdk.helpers.utils import get_starknet_token_balance


class SenderEvent(BaseEvent):
    def __init__(self, database, data_item, data_item_index):
        super().__init__(database, data_item, data_item_index)

    async def transfer(self):
        balance = await get_starknet_token_balance(self.starknet_read_client)
        transfer_keep_amount = round(random.uniform(*STARKNET_TRANSFER_ETH_KEEP_AMOUNT), ROUND_TO)

        if transfer_keep_amount > balance:
            raise Exception(f"Transfer eth keep amount more than ETH balance: {transfer_keep_amount} > {balance}")

        transfer_amount = round(balance - transfer_keep_amount, ROUND_TO)
        tx_status = await self.token_transfer(transfer_amount)

        return tx_status

    @starknet_retry(attempts=ATTEMPTS_COUNT)
    async def token_transfer(self, transfer_amount):
        return await self.starknet_write_client.transfer(
            token_in_addr=STARKNET_ETH_TOKEN_ADDRESS,
            amount_in=transfer_amount,
            recipient=self.data_item.withdrawal_address
        )
