import random

from config import (
    ZKLEND_DEPOSIT_PERCENT,
    ROUND_TO,
    ATTEMPTS_COUNT,
    WARMUP_WITH_GAS_THRESHOLD_ETH_VALUE,
    OKX_WITHDRAW_DEVIATION
)
from sdk.database.data_item import DataItem
from sdk.database.database import Database
from sdk.events.base_event import BaseEvent
from sdk.helpers.aggregator import Aggregator
from sdk.helpers.decorators import starknet_retry
from sdk.helpers.logger import logger
from sdk.helpers.okx import volume_mode_withdraw
from sdk.helpers.utils import get_starknet_token_balance
from sdk.models.dapp import Dapp
from sdk.models.event import Event


class WarmupEvent(BaseEvent):
    def __init__(self, database, data_item, data_item_index):
        super().__init__(database, data_item, data_item_index)

    @starknet_retry(attempts=ATTEMPTS_COUNT)
    async def run_warmup(self, data_item: DataItem, aggregator: Aggregator):
        try:
            event = aggregator.get_random_warmup_event()
            tx_status = False

            if event == Event.SWAPS:
                tx_status, data_item = await self.swap(data_item, aggregator)

            if event == Event.NFTS:
                tx_status, data_item = await self.nft(data_item, aggregator)

            if event == Event.DMAIL:
                tx_status, data_item = await self.dmail(data_item)

            if event == Event.ZKLEND:
                tx_status, data_item = await self.zklend(data_item)

        except Exception as e:
            logger.error(f"Client failed with error: {str(e)}")
            tx_status = False

        return tx_status, data_item

    async def swap(self, data_item: DataItem, aggregator: Aggregator):
        func = None

        if aggregator.dex_for_swap == Dapp.MYSWAP.value:
            func = self.starknet_write_client.myswap_swap

        if aggregator.dex_for_swap == Dapp.JEDISWAP.value:
            func = self.starknet_write_client.jediswap_swap

        if aggregator.dex_for_swap == Dapp.TENKSWAP.value:
            func = self.starknet_write_client.tenkswap_swap

        if aggregator.dex_for_swap == Dapp.SITHSWAP.value:
            func = self.starknet_write_client.sithswap_swap

        if aggregator.dex_for_swap == Dapp.AVNU.value:
            func = self.starknet_write_client.avnu_swap

        if func is None:
            raise Exception("Dex for swap was not found")

        tx_status = await func(
            token_in_addr=aggregator.token_in_for_swap,
            token_out_addr=aggregator.token_out_for_swap,
            amount_in=aggregator.amount_in_for_swap
        )

        if tx_status:
            if aggregator.dex_for_swap == Dapp.MYSWAP.value:
                data_item.myswap_swap_tx_count -= 1

            if aggregator.dex_for_swap == Dapp.JEDISWAP.value:
                data_item.jediswap_swap_tx_count -= 1

            if aggregator.dex_for_swap == Dapp.TENKSWAP.value:
                data_item.tenkswap_swap_tx_count -= 1

            if aggregator.dex_for_swap == Dapp.SITHSWAP.value:
                data_item.sithswap_swap_tx_count -= 1

            if aggregator.dex_for_swap == Dapp.AVNU.value:
                data_item.avnu_swap_tx_count -= 1

        return tx_status, data_item

    async def nft(self, data_item: DataItem, aggregator: Aggregator):
        random.shuffle(aggregator.suitable_nfts)
        event = random.choice(aggregator.suitable_nfts)

        tx_status = False

        if event == Dapp.MY_IDENTITY:
            tx_status = await self.starknet_write_client.my_identity_mint()

        if event == Dapp.STARKVERSE:
            tx_status = await self.starknet_write_client.starkverse_mint()

        if event == Dapp.NFT_ALLOWANCE:
            tx_status = await self.starknet_write_client.nft_marketplace_allowance(aggregator.nft_allowance_amount)

        if tx_status:
            if event == Dapp.MY_IDENTITY:
                data_item.my_identity_mint_tx_count -= 1

            if event == Dapp.STARKVERSE:
                data_item.starkverse_mint_tx_count -= 1

            if event == Dapp.NFT_ALLOWANCE:
                data_item.nft_marketplace_allowance_tx_count -= 1

        return tx_status, data_item

    async def dmail(self, data_item: DataItem):
        tx_status = await self.starknet_write_client.dmail_send_mail()

        if tx_status:
            data_item.dmail_tx_count -= 1

        return tx_status, data_item

    async def zklend(self, data_item: DataItem):
        if data_item.zklend_deposit_tx_count < data_item.zklend_withdraw_tx_count:
            tx_status = await self.starknet_write_client.zklend_withdraw()

            if tx_status:
                data_item.zklend_withdraw_tx_count -= 1
        else:
            balance = await get_starknet_token_balance(self.starknet_read_client)
            deposit_percent = round(random.uniform(*ZKLEND_DEPOSIT_PERCENT), ROUND_TO)
            deposit_amount = round(balance * deposit_percent, ROUND_TO)
            tx_status = await self.starknet_write_client.zklend_deposit(deposit_amount)

            if tx_status:
                data_item.zklend_deposit_tx_count -= 1

        return tx_status, data_item

    async def warmup_with_gas_withdraw(self):
        balance = await get_starknet_token_balance(self.starknet_read_client)

        if balance < WARMUP_WITH_GAS_THRESHOLD_ETH_VALUE:
            logger.info("Start warmup with gas withdraw", send_to_tg=False)
            amount_to_withdraw = round(random.uniform(*OKX_WITHDRAW_DEVIATION), ROUND_TO)
            await volume_mode_withdraw(
                starknet_client=self.starknet_read_client,
                evm_client=None,
                withdrawal_address=self.starknet_address,
                amount_to_withdraw=amount_to_withdraw
            )

    async def warmup_low_bank_withdraw(self):
        logger.info("Start warmup low bank withdraw", send_to_tg=False)
        amount_to_withdraw = round(random.uniform(*OKX_WITHDRAW_DEVIATION), ROUND_TO)

        await volume_mode_withdraw(
            starknet_client=self.starknet_read_client,
            evm_client=None,
            withdrawal_address=self.starknet_address,
            amount_to_withdraw=amount_to_withdraw
        )

        self.data_item.is_okx_withdraw_completed = True
        self.database = Database.update_database(self.database, self.data_item, self.data_item_index)
        Database.save_database(self.database)
