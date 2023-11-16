from enum import Enum

from sdk.database.database import Database
from sdk.events.bridge_event import BridgeEvent
from sdk.helpers.logger import logger
from sdk.helpers.utils import (
    change_mobile_ip,
    close_starknet_session,
    get_starknet_token_balance
)
from sdk.models.token_amount import TokenAmount


class BridgeModes(Enum):
    STARKGATE = "starkgate"
    ORBITER = "orbiter"
    LAYERSWAP = "layerswap"


async def batch_bridge_from_starknet(mode):
    database = Database.read_database()
    bridge_event = data_item = data_item_index = None
    tx_status = False

    while Database.not_empty(database):
        try:
            change_mobile_ip()

            data_item, data_item_index = Database.get_random_data_item(database["data"])
            bridge_event = BridgeEvent(database, data_item, data_item_index)

            logger.info(f"Accounts remaining count: {bridge_event.accounts_remaining}", send_to_tg=False)
            logger.debug(f"Starknet wallet address: {bridge_event.starknet_address}")

            balance = await get_starknet_token_balance(bridge_event.starknet_read_client)
            amount = bridge_event.get_amount_to_bridge(balance)

            if mode == BridgeModes.STARKGATE:
                tx_status = await bridge_event.starkgate_bridge_from_starknet(bridge_event.evm_address, amount)

            if mode == BridgeModes.ORBITER:
                tx_status = await bridge_event.orbiter_bridge_from_starknet(bridge_event.evm_address, amount)

            if mode == BridgeModes.LAYERSWAP:
                tx_status = await bridge_event.layerswap_bridge_from_starknet(bridge_event.evm_address, amount)

            if tx_status:
                database = Database.remove_item_from_data(database, data_item_index)
                Database.save_database(database)

        except Exception as e:
            if "Balance is below minimum" in str(e) or "Amount to bridge less than 0" in str(e):
                Database.move_item_to_errors(database, data_item, data_item_index)
                continue

            logger.exception(f"Error while execute warmup module: {str(e)}")

        finally:
            if bridge_event is not None:
                await close_starknet_session(bridge_event.starknet_read_client, bridge_event.starknet_write_client)

    logger.debug("All accounts are finished. Run exit()")
    exit()


async def batch_bridge_from_evm(mode):
    database = Database.read_database()
    bridge_event = data_item = data_item_index = client = None
    tx_status = False

    while Database.not_empty(database):
        try:
            change_mobile_ip()

            data_item, data_item_index = Database.get_random_data_item(database["data"])
            bridge_event = BridgeEvent(database, data_item, data_item_index)

            logger.info(f"Accounts remaining count: {bridge_event.accounts_remaining}", send_to_tg=False)
            logger.debug(f"Starknet wallet address: {bridge_event.starknet_address}")

            if mode == BridgeModes.STARKGATE:
                client = bridge_event.ethereum_client

            if mode == BridgeModes.ORBITER:
                client = bridge_event.arbitrum_client

            if mode == BridgeModes.LAYERSWAP:
                client = bridge_event.optimism_client

            balance = TokenAmount(amount=client.w3.eth.get_balance(client.public_key), wei=True)
            amount = bridge_event.get_amount_to_bridge(float(balance.ether))

            if mode == BridgeModes.STARKGATE:
                tx_status = await bridge_event.starkgate_bridge_from_evm(bridge_event.starknet_address, amount)

            if mode == BridgeModes.ORBITER:
                tx_status = await bridge_event.orbiter_bridge_from_evm(bridge_event.starknet_address, amount)

            if mode == BridgeModes.LAYERSWAP:
                tx_status = await bridge_event.layerswap_bridge_from_evm(bridge_event.starknet_address, amount)

            if tx_status:
                database = Database.remove_item_from_data(database, data_item_index)
                Database.save_database(database)

        except Exception as e:
            if "Balance is below minimum" in str(e) or "Amount to bridge less than 0" in str(e):
                Database.move_item_to_errors(database, data_item, data_item_index)
                continue

            logger.exception(f"Error while execute warmup module: {str(e)}")

        finally:
            if bridge_event is not None:
                await close_starknet_session(bridge_event.starknet_read_client, bridge_event.starknet_write_client)

    logger.debug("All accounts are finished. Run exit()")
    exit()
