import json
import random
from typing import Any

from config import (
    USE_PROXY,
    DMAIL_TX_COUNT,
    NFT_MARKETPLACE_ALLOWANCE_TX_COUNT,
    MYSWAP_SWAP_TX_COUNT,
    JEDISWAP_SWAP_TX_COUNT,
    TENKSWAP_SWAP_TX_COUNT,
    SITHSWAP_SWAP_TX_COUNT,
    AVNU_SWAP_TX_COUNT,
    MY_IDENTITY_MINT_TX_COUNT,
    ZKLEND_TX_COUNT,
    WITHDRAWAL_FROM_ZKLEND,
    WALLET_APPLICATION,
    STARKVERSE_MINT_TX_COUNT
)
from constants import (
    EVM_PRIVATE_KEYS_PATH,
    STARKNET_PRIVATE_KEYS_PATH,
    PROXIES_PATH,
    WITHDRAWAL_ADDRESSES_PATH,
    DATABASE_PATH,
    DATABASE_DATA_EXCEL_PATH,
    DATABASE_ERRORS_EXCEL_PATH,
    SALTS_PATH
)
from sdk.database.data_item import DataItem
from sdk.helpers.cryptography_manager import CryptographyManager, CryptographyMode
from sdk.helpers.logger import logger
from sdk.helpers.utils import export_json


class Database:
    def __init__(self, data):
        self.data = data
        self.errors = []
        self.accounts_remaining = len(data)

    def to_json(self):
        try:
            return json.dumps(self, default=lambda o: o.__dict__, indent=4)
        except Exception as e:
            raise Exception(f"Database to json object error: {str(e)}")

    @staticmethod
    def not_empty(database) -> bool:
        return not database["accounts_remaining"] == 0

    @staticmethod
    def move_item_to_errors(database, data_item: DataItem, data_item_index: int):
        try:
            if data_item is None or data_item_index is None:
                raise Exception("Data item or data_item_index is None")

            database["errors"].append(data_item)
            database["data"].pop(data_item_index)

        except Exception as e:
            logger.error(f"Move data item error: {str(e)}")

    @staticmethod
    def create_data_item(
            starknet_private_key: str,
            starknet_wallet_salt: str,
            evm_private_key: str,
            proxy: str,
            withdrawal_address: str,
            zklend_deposit_tx_count: int,

    ):
        return DataItem(
            starknet_private_key=starknet_private_key,
            starknet_wallet_salt=starknet_wallet_salt,
            evm_private_key=evm_private_key,
            proxy=proxy,
            withdrawal_address=withdrawal_address,
            dmail_tx_count=random.randint(*DMAIL_TX_COUNT),
            nft_marketplace_allowance_tx_count=random.randint(*NFT_MARKETPLACE_ALLOWANCE_TX_COUNT),
            myswap_swap_tx_count=random.randint(*MYSWAP_SWAP_TX_COUNT),
            jediswap_swap_tx_count=random.randint(*JEDISWAP_SWAP_TX_COUNT),
            tenkswap_swap_tx_count=random.randint(*TENKSWAP_SWAP_TX_COUNT),
            sithswap_swap_tx_count=random.randint(*SITHSWAP_SWAP_TX_COUNT),
            avnu_swap_tx_count=random.randint(*AVNU_SWAP_TX_COUNT),
            my_identity_mint_tx_count=random.randint(*MY_IDENTITY_MINT_TX_COUNT),
            starkverse_mint_tx_count=random.randint(*STARKVERSE_MINT_TX_COUNT),
            zklend_deposit_tx_count=zklend_deposit_tx_count,
            zklend_withdraw_tx_count=Database.get_zklend_withdraw_tx_count(zklend_deposit_tx_count),
            cryptography_mode=CryptographyMode.ENCRYPT,
            is_okx_withdraw_completed=False,
            is_bridge_completed=False,
            volume_amount=0
        )

    @staticmethod
    def create_database():
        try:
            data = []
            starknet_private_keys = Database.read_from_txt(STARKNET_PRIVATE_KEYS_PATH)
            evm_private_keys = Database.read_from_txt(EVM_PRIVATE_KEYS_PATH)
            proxies = Database.read_from_txt(PROXIES_PATH)
            withdrawal_addresses = Database.read_from_txt(WITHDRAWAL_ADDRESSES_PATH)
            starknet_wallet_salts = Database.read_from_txt(SALTS_PATH)

            if len(withdrawal_addresses) != len(starknet_private_keys) and len(withdrawal_addresses) != 0:
                logger.error(f"Withdrawal addresses length less than needed. Run exit()")
                exit()

            if len(evm_private_keys) != len(starknet_private_keys) and len(evm_private_keys) != 0:
                logger.error(f"EVM private keys length less than needed. Run exit()")
                exit()

            if USE_PROXY and len(starknet_private_keys) != len(proxies):
                logger.error(f"Proxies length less than needed. Run exit()")
                exit()

            if WALLET_APPLICATION == 'salts' and len(starknet_wallet_salts) != len(starknet_private_keys):
                logger.error(f"Salts length less than needed. Run exit()")
                exit()

            try:
                for starknet_private_key in starknet_private_keys:
                    starknet_private_key_index = starknet_private_keys.index(starknet_private_key)
                    starknet_wallet_salt = starknet_wallet_salts[starknet_private_key_index] \
                        if WALLET_APPLICATION == 'salts' else None
                    proxy = proxies[starknet_private_key_index] if USE_PROXY else None

                    if len(withdrawal_addresses) == len(starknet_private_keys):
                        withdrawal_address = withdrawal_addresses[starknet_private_key_index]
                    else:
                        withdrawal_address = None

                    if len(evm_private_keys) == len(starknet_private_keys):
                        evm_private_key = evm_private_keys[starknet_private_key_index]
                    else:
                        evm_private_key = None

                    zklend_deposit_tx_count = random.randint(*ZKLEND_TX_COUNT)

                    while True:
                        data_item = Database.create_data_item(
                            starknet_private_key,
                            starknet_wallet_salt,
                            evm_private_key,
                            proxy,
                            withdrawal_address,
                            zklend_deposit_tx_count
                        )

                        tx_count = Database.get_data_item_tx_count(data_item)
                        if tx_count != 0:
                            data.append(data_item)
                            break

            except IndexError as e:
                raise Exception(f"Problems with the proxy when creating a database: {str(e)}")

            except Exception as e:
                raise Exception(f"Problems with data items when creating a database: {str(e)}")

            Database.save_database(Database(data).to_json())
            logger.success(f"Database was been created", send_to_tg=False)

        except Exception as e:
            raise Exception(f"Database creation error: {str(e)}")

    @staticmethod
    def get_zklend_withdraw_tx_count(zklend_tx_count):
        return zklend_tx_count if WITHDRAWAL_FROM_ZKLEND else 0

    @staticmethod
    def update_database(database, data_item, data_item_index) -> Any:
        tx_count = Database.get_data_item_tx_count(data_item)

        if tx_count == 0:
            return Database.remove_item_from_data(database, data_item_index)

        database["data"][data_item_index]["starknet_private_key"] = CryptographyManager.encrypt(
            data_item.starknet_private_key)
        database["data"][data_item_index]["starknet_wallet_salt"] = CryptographyManager.encrypt(
            data_item.starknet_wallet_salt)
        database["data"][data_item_index]["evm_private_key"] = CryptographyManager.encrypt(
            data_item.evm_private_key)
        database["data"][data_item_index]["proxy"] = CryptographyManager.encrypt(data_item.proxy)
        database["data"][data_item_index]["withdrawal_address"] = data_item.withdrawal_address
        database["data"][data_item_index]["dmail_tx_count"] = data_item.dmail_tx_count
        database["data"][data_item_index]["nft_marketplace_allowance_tx_count"] = \
            data_item.nft_marketplace_allowance_tx_count
        database["data"][data_item_index]["myswap_swap_tx_count"] = data_item.myswap_swap_tx_count
        database["data"][data_item_index]["jediswap_swap_tx_count"] = data_item.jediswap_swap_tx_count
        database["data"][data_item_index]["tenkswap_swap_tx_count"] = data_item.tenkswap_swap_tx_count
        database["data"][data_item_index]["sithswap_swap_tx_count"] = data_item.sithswap_swap_tx_count
        database["data"][data_item_index]["avnu_swap_tx_count"] = data_item.avnu_swap_tx_count
        database["data"][data_item_index]["my_identity_mint_tx_count"] = data_item.my_identity_mint_tx_count
        database["data"][data_item_index]["starkverse_mint_tx_count"] = data_item.starkverse_mint_tx_count
        database["data"][data_item_index]["zklend_deposit_tx_count"] = data_item.zklend_deposit_tx_count
        database["data"][data_item_index]["zklend_withdraw_tx_count"] = data_item.zklend_withdraw_tx_count
        database["data"][data_item_index]["is_okx_withdraw_completed"] = data_item.is_okx_withdraw_completed
        database["data"][data_item_index]["is_bridge_completed"] = data_item.is_bridge_completed
        database["data"][data_item_index]["volume_amount"] = data_item.volume_amount

        return database

    @staticmethod
    def remove_item_from_data(database, data_item_index: int):
        database["data"].pop(data_item_index)
        database["accounts_remaining"] -= 1

        return database

    @staticmethod
    def get_first_data_item(data):
        try:
            data_len = len(data)

            if data_len == 0:
                logger.debug("All accounts are finished. Run exit()")
                exit()

            data_item_index = 0
            data_item_json = data[data_item_index]

            if data_len > 0:
                data_item = DataItem(
                    data_item_json["starknet_private_key"],
                    data_item_json["starknet_wallet_salt"],
                    data_item_json["evm_private_key"],
                    data_item_json["proxy"],
                    data_item_json["withdrawal_address"],
                    data_item_json["dmail_tx_count"],
                    data_item_json["nft_marketplace_allowance_tx_count"],
                    data_item_json["myswap_swap_tx_count"],
                    data_item_json["jediswap_swap_tx_count"],
                    data_item_json["tenkswap_swap_tx_count"],
                    data_item_json["sithswap_swap_tx_count"],
                    data_item_json["avnu_swap_tx_count"],
                    data_item_json["my_identity_mint_tx_count"],
                    data_item_json["starkverse_mint_tx_count"],
                    data_item_json["zklend_deposit_tx_count"],
                    data_item_json["zklend_withdraw_tx_count"],
                    data_item_json["is_okx_withdraw_completed"],
                    data_item_json["is_bridge_completed"],
                    data_item_json["volume_amount"],
                    CryptographyMode.DECRYPT
                )
                return data_item, data_item_index
            else:
                raise Exception("Empty range for randrange")

        except Exception as e:
            if "Empty range for randrange" in str(e):
                logger.debug("All accounts are finished. Run exit()")
                exit()
            else:
                raise Exception(f"Get random data item from database error: {str(e)}")

    @staticmethod
    def get_random_data_item(data):
        try:
            data_len = len(data)

            if data_len == 0:
                logger.debug("All accounts are finished. Run exit()")
                exit()
            elif data_len == 1:
                data_item_index = 0
            else:
                data_item_index = random.randint(0, data_len - 1)

            data_item_json = data[data_item_index]

            if data_len > 0:
                data_item = DataItem(
                    data_item_json["starknet_private_key"],
                    data_item_json["starknet_wallet_salt"],
                    data_item_json["evm_private_key"],
                    data_item_json["proxy"],
                    data_item_json["withdrawal_address"],
                    data_item_json["dmail_tx_count"],
                    data_item_json["nft_marketplace_allowance_tx_count"],
                    data_item_json["myswap_swap_tx_count"],
                    data_item_json["jediswap_swap_tx_count"],
                    data_item_json["tenkswap_swap_tx_count"],
                    data_item_json["sithswap_swap_tx_count"],
                    data_item_json["avnu_swap_tx_count"],
                    data_item_json["my_identity_mint_tx_count"],
                    data_item_json["starkverse_mint_tx_count"],
                    data_item_json["zklend_deposit_tx_count"],
                    data_item_json["zklend_withdraw_tx_count"],
                    data_item_json["is_okx_withdraw_completed"],
                    data_item_json["is_bridge_completed"],
                    data_item_json["volume_amount"],
                    CryptographyMode.DECRYPT
                )
                return data_item, data_item_index
            else:
                raise Exception("Empty range for randrange")

        except Exception as e:
            if "Empty range for randrange" in str(e):
                logger.debug("All accounts are finished. Run exit()")
                exit()
            else:
                raise Exception(f"Get random data item from database error: {str(e)}")

    @staticmethod
    def read_database() -> Any:
        try:
            with open(DATABASE_PATH) as json_file:
                return json.load(json_file)
        except Exception as e:
            raise Exception(f"Error while read database: {str(e)}")

    @staticmethod
    def save_database(database) -> None:
        try:
            if type(database) is dict:
                database = json.dumps(database, indent=4)

            with open(DATABASE_PATH, 'w') as json_file:
                json_file.write(database)

            export_json(database, "data", DATABASE_DATA_EXCEL_PATH)
            export_json(database, "errors", DATABASE_ERRORS_EXCEL_PATH)

        except Exception as e:
            raise Exception(f"Error while save database: {str(e)}")

    @staticmethod
    def read_from_txt(file_path) -> Any:
        try:
            with open(file_path, "r") as file:
                return [line.strip() for line in file]
        except Exception as e:
            raise Exception(f"Encountered an error while reading a txt file '{file_path}': {str(e)}")

    @staticmethod
    def get_data_item_tx_count(data_item: DataItem):
        total_tx_count = sum([
            data_item.dmail_tx_count,
            data_item.nft_marketplace_allowance_tx_count,
            data_item.myswap_swap_tx_count,
            data_item.jediswap_swap_tx_count,
            data_item.tenkswap_swap_tx_count,
            data_item.sithswap_swap_tx_count,
            data_item.avnu_swap_tx_count,
            data_item.my_identity_mint_tx_count,
            data_item.starkverse_mint_tx_count,
            data_item.zklend_deposit_tx_count,
            data_item.zklend_withdraw_tx_count
        ])

        return total_tx_count

    @staticmethod
    def get_database_tx_count(data):
        tx_count = 0

        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if key.endswith("_tx_count"):
                        tx_count += value

        return tx_count
