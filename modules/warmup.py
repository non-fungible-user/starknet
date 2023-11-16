from sdk.database.database import Database
from sdk.events.collector_event import CollectorEvent
from sdk.events.sender_event import SenderEvent
from sdk.events.warmup_event import WarmupEvent
from sdk.helpers.aggregator import Aggregator
from sdk.helpers.logger import logger
from sdk.helpers.utils import (
    change_mobile_ip,
    get_starknet_max_balance_token,
    close_starknet_session
)


async def warmup():
    database = Database.read_database()
    warmup_event = data_item = data_item_index = None

    while Database.not_empty(database):
        try:
            change_mobile_ip()

            data_item, data_item_index = Database.get_random_data_item(database["data"])
            warmup_event = WarmupEvent(database, data_item, data_item_index)

            logger.info(f"Database tx count: {warmup_event.database_tx_count}", send_to_tg=False)
            logger.debug(f"Starknet wallet address: {warmup_event.starknet_address}")

            token_in, amount_in = await get_starknet_max_balance_token(warmup_event.starknet_read_client)
            aggregator = Aggregator(data_item, token_in, amount_in)

            tx_status, data_item = await warmup_event.run_warmup(data_item, aggregator)

            if tx_status:
                database = Database.update_database(database, data_item, data_item_index)
                Database.save_database(database)

        except Exception as e:
            if "Balance is below minimum" in str(e):
                Database.move_item_to_errors(database, data_item, data_item_index)
                continue

            logger.exception(f"Error while execute warmup module: {str(e)}")

        finally:
            if warmup_event is not None:
                await close_starknet_session(warmup_event.starknet_read_client, warmup_event.starknet_write_client)

    logger.debug("All accounts are finished. Run exit()")
    exit()


async def warmup_with_gas():
    database = Database.read_database()
    warmup_event = data_item = data_item_index = None

    while Database.not_empty(database):
        try:
            change_mobile_ip()

            data_item, data_item_index = Database.get_random_data_item(database["data"])
            warmup_event = WarmupEvent(database, data_item, data_item_index)

            logger.info(f"Database tx count: {warmup_event.database_tx_count}", send_to_tg=False)
            logger.debug(f"Starknet wallet address: {warmup_event.starknet_address}")

            await warmup_event.warmup_with_gas_withdraw()

            token_in, amount_in = await get_starknet_max_balance_token(warmup_event.starknet_read_client)
            aggregator = Aggregator(data_item, token_in, amount_in)

            tx_status, data_item = await warmup_event.run_warmup(data_item, aggregator)

            if tx_status:
                database = Database.update_database(database, data_item, data_item_index)
                Database.save_database(database)

        except Exception as e:
            if "Balance is below minimum" in str(e):
                Database.move_item_to_errors(database, data_item, data_item_index)
                continue

            logger.exception(f"Error while execute warmup with gas module: {str(e)}")

        finally:
            if warmup_event is not None:
                await close_starknet_session(warmup_event.starknet_read_client, warmup_event.starknet_write_client)

    logger.debug("All accounts are finished. Run exit()")
    exit()


async def warmup_low_bank():
    database = Database.read_database()
    warmup_event = data_item = data_item_index = None

    while Database.not_empty(database):
        try:
            change_mobile_ip()

            data_item, data_item_index = Database.get_first_data_item(database["data"])
            warmup_event = WarmupEvent(database, data_item, data_item_index)

            logger.info(f"Database tx count: {warmup_event.database_tx_count}", send_to_tg=False)
            logger.debug(f"Starknet wallet address: {warmup_event.starknet_address}")

            if not warmup_event.data_item.is_okx_withdraw_completed:
                await warmup_event.warmup_low_bank_withdraw()

                warmup_event.data_item.is_okx_withdraw_completed = True

                warmup_event.database = Database.update_database(
                    warmup_event.database,
                    warmup_event.data_item,
                    warmup_event.data_item_index
                )
                Database.save_database(warmup_event.database)
                database = warmup_event.database

            while True:
                logger.info(f"Wallet tx count: {warmup_event.data_item_tx_count}", send_to_tg=False)
                token_in, amount_in = await get_starknet_max_balance_token(warmup_event.starknet_read_client)
                aggregator = Aggregator(warmup_event.data_item, token_in, amount_in)

                tx_status, data_item = await warmup_event.run_warmup(data_item, aggregator)

                if tx_status:
                    warmup_event.data_item_tx_count = Database.get_data_item_tx_count(warmup_event.data_item)
                    if warmup_event.data_item_tx_count != 0:
                        warmup_event.database = Database.update_database(
                            warmup_event.database,
                            warmup_event.data_item,
                            warmup_event.data_item_index
                        )
                        Database.save_database(warmup_event.database)
                        database = warmup_event.database

                if warmup_event.data_item_tx_count == 0:
                    break

            logger.info("Start collector")

            collector_event = CollectorEvent(
                warmup_event.database,
                warmup_event.data_item,
                warmup_event.data_item_index
            )
            await collector_event.collector()

            logger.info("Start sender")

            sender_event = SenderEvent(
                collector_event.database,
                collector_event.data_item,
                collector_event.data_item_index
            )
            tx_status = await sender_event.transfer()

            if not tx_status:
                logger.error("Transfer to OKX error. Run exit()")
                exit()

        except Exception as e:
            if "Balance is below minimum" in str(e):
                Database.move_item_to_errors(database, data_item, data_item_index)
                continue

            logger.exception(f"Error while execute warmup low bank module: {str(e)}")

        finally:
            if warmup_event is not None:
                await close_starknet_session(warmup_event.starknet_read_client, warmup_event.starknet_write_client)

    logger.debug("All accounts are finished. Run exit()")
    exit()
