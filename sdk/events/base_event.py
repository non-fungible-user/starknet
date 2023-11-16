from sdk.database.database import Database
from sdk.evm.client import EvmClient
from sdk.helpers.utils import get_starknet_read_client, get_starknet_write_client
from sdk.models.chain import ethereum, arbitrum, optimism
from sdk.starknet.client import StarknetClient


class BaseEvent:
    def __init__(self, database, data_item, data_item_index):
        self.database = database
        self.data_item = data_item
        self.data_item_index = data_item_index

        self.database_tx_count = Database.get_database_tx_count(database["data"])
        self.data_item_tx_count = Database.get_data_item_tx_count(data_item)
        self.accounts_remaining = database['accounts_remaining']

        self.starknet_read_client = StarknetClient(
            private_key=data_item.starknet_private_key,
            salt=data_item.starknet_wallet_salt,
            proxy=data_item.proxy,
            rpc=get_starknet_read_client(data_item.proxy)
        )

        self.starknet_write_client = StarknetClient(
            private_key=data_item.starknet_private_key,
            salt=data_item.starknet_wallet_salt,
            proxy=data_item.proxy,
            rpc=get_starknet_write_client(data_item.proxy)
        )

        self.ethereum_client = EvmClient(
            private_key=data_item.evm_private_key,
            chain=ethereum,
            proxy=data_item.proxy
        )

        self.arbitrum_client = EvmClient(
            private_key=data_item.evm_private_key,
            chain=arbitrum,
            proxy=data_item.proxy
        )

        self.optimism_client = EvmClient(
            private_key=data_item.evm_private_key,
            chain=optimism,
            proxy=data_item.proxy
        )

        self.starknet_address = hex(self.starknet_read_client.address)
        self.evm_address = self.ethereum_client.address
