from config import (
    ROUND_TO,
    MINIMUM_COLLECTED_USD_VALUE,
    USE_AVNU_FOR_COLLECTOR,
    ATTEMPTS_COUNT
)
from constants import (
    STARKNET_COLLECTOR_TOKENS,
    STARKNET_TOKEN_NAMES,
    STARKNET_ETH_TOKEN_ADDRESS,
    STARKNET_COLLECTOR_COINGECKO_TOKEN_IDS
)
from sdk.database.database import Database
from sdk.events.base_event import BaseEvent
from sdk.helpers.decorators import starknet_retry
from sdk.helpers.logger import logger
from sdk.helpers.utils import get_starknet_token_balance
from sdk.starknet.utils import get_cg_tokens_price_usd


class CollectorEvent(BaseEvent):
    def __init__(self, database, data_item, data_item_index):
        super().__init__(database, data_item, data_item_index)

    async def collector(self):
        usd_token_prices = get_cg_tokens_price_usd(STARKNET_COLLECTOR_COINGECKO_TOKEN_IDS)
        tx_count = 0

        for token_address in STARKNET_COLLECTOR_TOKENS:
            tx_status = await self.token_collector(token_address, usd_token_prices)
            if tx_status:
                tx_count += 1

        if tx_count != len(STARKNET_COLLECTOR_TOKENS):
            logger.warning(f"Not all tokens were swapped on this account")
            self.database = Database.move_item_to_errors(self.database, self.data_item, self.data_item_index)
        else:
            self.database = Database.remove_item_from_data(self.database, self.data_item_index)

        Database.save_database(self.database)

    async def token_collector(self, token_address: str, token_prices_usd: list) -> bool:
        try:
            token_balance = await get_starknet_token_balance(self.starknet_read_client, token_addr=token_address)
            token_balance_usd = token_balance * token_prices_usd[STARKNET_COLLECTOR_TOKENS.index(token_address)]
            logger.info(f"Account balance in {STARKNET_TOKEN_NAMES[token_address]} token: {token_balance_usd} USD")

            amount_in = int(token_balance * 10 ** ROUND_TO) / 10 ** ROUND_TO

            if token_balance_usd > MINIMUM_COLLECTED_USD_VALUE:
                return await self.swap(token_address, amount_in)
            else:
                logger.info(f"Token balance is below the minimum for a swap")
                return True

        except Exception as e:
            logger.error(f"Collector event error: {str(e)}")
            return False

    @starknet_retry(attempts=ATTEMPTS_COUNT)
    async def swap(self, token_in_address: str, amount_in: float) -> bool:
        if USE_AVNU_FOR_COLLECTOR:
            return await self.starknet_write_client.avnu_swap(
                token_in_addr=token_in_address,
                token_out_addr=STARKNET_ETH_TOKEN_ADDRESS,
                amount_in=amount_in
            )
        else:
            return await self.starknet_write_client.myswap_swap(
                token_in_addr=token_in_address,
                token_out_addr=STARKNET_ETH_TOKEN_ADDRESS,
                amount_in=amount_in
            )
