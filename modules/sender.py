import random

from config import OKX_WITHDRAW_DEVIATION, ROUND_TO
from sdk.database.database import Database
from sdk.events.sender_event import SenderEvent
from sdk.helpers.logger import logger
from sdk.helpers.okx import volume_mode_withdraw
from sdk.helpers.utils import change_mobile_ip, close_starknet_session


async def batch_sender():
    database = Database.read_database()
    sender_event = data_item = data_item_index = None

    while Database.not_empty(database):
        try:
            change_mobile_ip()

            data_item, data_item_index = Database.get_random_data_item(database["data"])
            sender_event = SenderEvent(database, data_item, data_item_index)

            logger.info(f"Accounts remaining count: {sender_event.accounts_remaining}", send_to_tg=False)
            logger.debug(f"Starknet wallet address: {sender_event.starknet_address}")

            tx_status = await sender_event.transfer()

            if not tx_status:
                sender_event.database = Database.move_item_to_errors(
                    sender_event.database,
                    sender_event.data_item,
                    sender_event.data_item_index
                )
            else:
                sender_event.database = Database.remove_item_from_data(
                    sender_event.database,
                    sender_event.data_item_index
                )

            Database.save_database(sender_event.database)
            database = sender_event.database

        except Exception as e:
            if "Balance is below minimum" in str(e):
                Database.move_item_to_errors(database, data_item, data_item_index)
                continue

            logger.exception(f"Error while execute warmup module: {str(e)}")

        finally:
            if sender_event is not None:
                await close_starknet_session(sender_event.starknet_read_client, sender_event.starknet_write_client)

    logger.debug("All accounts are finished. Run exit()")
    exit()


async def batch_withdrawal_to_starknet():
    database = Database.read_database()
    sender_event = data_item = data_item_index = None

    while Database.not_empty(database):
        try:
            change_mobile_ip()

            data_item, data_item_index = Database.get_random_data_item(database["data"])
            sender_event = SenderEvent(database, data_item, data_item_index)

            logger.info(f"Accounts remaining count: {sender_event.accounts_remaining}", send_to_tg=False)
            logger.debug(f"Starknet wallet address: {sender_event.starknet_address}")

            amount_to_withdraw = round(random.uniform(*OKX_WITHDRAW_DEVIATION), ROUND_TO)
            await volume_mode_withdraw(
                starknet_client=sender_event.starknet_read_client,
                evm_client=None,
                withdrawal_address=sender_event.starknet_address,
                amount_to_withdraw=amount_to_withdraw,
                disable_delivery_watch=True
            )

            sender_event.database = Database.remove_item_from_data(sender_event.database, sender_event.data_item_index)
            Database.save_database(sender_event.database)

            database = sender_event.database

        except Exception as e:
            if "Balance is below minimum" in str(e):
                Database.move_item_to_errors(database, data_item, data_item_index)
                continue

            logger.exception(f"Error while execute warmup module: {str(e)}")

        finally:
            if sender_event is not None:
                await close_starknet_session(sender_event.starknet_read_client, sender_event.starknet_write_client)

    logger.debug("All accounts are finished. Run exit()")
    exit()
