import random

from config import ATTEMPTS_COUNT, BRIDGE_ETH_KEEP_AMOUNT, ROUND_TO
from sdk.events.base_event import BaseEvent
from sdk.helpers.decorators import evm_retry, starknet_retry
from sdk.models.chain import arbitrum, optimism


class BridgeEvent(BaseEvent):
    def __init__(self, database, data_item, data_item_index):
        super().__init__(database, data_item, data_item_index)

    @starknet_retry(attempts=ATTEMPTS_COUNT)
    async def starkgate_bridge_from_starknet(self, evm_address: str, amount: float):
        return await self.starknet_write_client.starkgate_bridge(amount, evm_address)

    @starknet_retry(attempts=ATTEMPTS_COUNT)
    async def orbiter_bridge_from_starknet(self, evm_address: str, amount: float):
        return await self.starknet_write_client.orbiter_bridge(amount, evm_address, arbitrum)

    @starknet_retry(attempts=ATTEMPTS_COUNT)
    async def layerswap_bridge_from_starknet(self, evm_address: str, amount: float):
        return await self.starknet_write_client.layerswap_bridge(amount, evm_address, optimism)

    @evm_retry(attempts=ATTEMPTS_COUNT)
    async def starkgate_bridge_from_evm(self, starknet_address: str, amount: float):
        return self.ethereum_client.starkgate_bridge(amount, starknet_address)

    @evm_retry(attempts=ATTEMPTS_COUNT)
    async def orbiter_bridge_from_evm(self, starknet_address: str, amount: float):
        return self.arbitrum_client.orbiter_bridge(amount, starknet_address)

    @evm_retry(attempts=ATTEMPTS_COUNT)
    async def layerswap_bridge_from_evm(self, starknet_address: str, amount: float):
        return self.optimism_client.layerswap_bridge(amount, starknet_address)

    @staticmethod
    def get_amount_to_bridge(balance: float):
        keep_amount = random.uniform(*BRIDGE_ETH_KEEP_AMOUNT)
        amount_to_bridge = round(balance - keep_amount, ROUND_TO)

        if amount_to_bridge < 0:
            raise Exception(f"Amount to bridge less than 0. Balance: {balance}, keep amount: {keep_amount}")

        return amount_to_bridge
