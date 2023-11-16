from sdk.database.database import Database
from sdk.events.collector_event import CollectorEvent
from sdk.helpers.logger import logger
from sdk.helpers.utils import change_mobile_ip, close_starknet_session


async def batch_collector():
    database = Database.read_database()
    collector_event = data_item = data_item_index = None

    while Database.not_empty(database):
        try:
            change_mobile_ip()

            data_item, data_item_index = Database.get_random_data_item(database["data"])
            collector_event = CollectorEvent(database, data_item, data_item_index)

            logger.info(f"Accounts remaining count: {collector_event.accounts_remaining}", send_to_tg=False)
            logger.debug(f"Starknet wallet address: {collector_event.starknet_address}")

            await collector_event.collector()
            database = collector_event.database

        except Exception as e:
            if "Balance is below minimum" in str(e):
                Database.move_item_to_errors(database, data_item, data_item_index)
                continue

            logger.exception(f"Error while execute warmup module: {str(e)}")

        finally:
            if collector_event is not None:
                await close_starknet_session(
                    collector_event.starknet_read_client,
                    collector_event.starknet_write_client
                )

    logger.debug("All accounts are finished. Run exit()")
    exit()
