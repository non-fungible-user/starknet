from decimal import Decimal
from typing import Union

from web3 import Web3
from web3.middleware import geth_poa_middleware

from constants import (
    LAYERSWAP_BRIDGE_ADDRESSES,
    ORBITER_STARKNET_IDENTIFICATION_CODE,
    ARBITRUM_ORBITER_WITHHOLDING_FEE,
    EVM_ESTIMATED_FEE_MULTIPLIER
)
from sdk.apis.layerswap import LayerSwapAPI
from sdk.helpers.logger import logger
from sdk.models.chain import Chain
from sdk.models.layerswap_swap_config import LayerswapDataItem
from sdk.models.token_amount import TokenAmount


def init_web3(self):
    if self.proxy:
        request_kwargs = {"proxies": {"https": f"http://{self.proxy}"}, "timeout": 60}
    else:
        request_kwargs = {}

    return Web3(Web3.HTTPProvider(endpoint_uri=self.chain.rpc, request_kwargs=request_kwargs))


def get_tx_params(
        self,
        to_addr: str,
        data: str = None,
        from_addr: str = None,
        value: int = None
) -> dict:
    if not from_addr:
        from_addr = self.address

    tx_params = {
        "chainId": self.w3.eth.chain_id,
        "nonce": self.w3.eth.get_transaction_count(self.address),
        "from": self.w3.to_checksum_address(from_addr),
        "to": self.w3.to_checksum_address(to_addr),
    }

    if data:
        tx_params["data"] = data

    if value:
        tx_params["value"] = value

    tx_params["gasPrice"] = self.w3.eth.gas_price

    return tx_params


def get_gas_estimate(self, tx_params: dict, gas_multiplier: float = EVM_ESTIMATED_FEE_MULTIPLIER):
    try:
        return int(self.w3.eth.estimate_gas(tx_params) * gas_multiplier)

    except Exception as e:
        raise Exception(f"Transaction estimate failed: {e}")


def get_native_balance(self):
    try:
        return self.w3.eth.get_balance(self.address)
    except Exception as e:
        raise Exception(f"Could not get balance of: {self.address}: {e}")


def send_transaction(
        self,
        to_addr: str,
        data: str = None,
        from_addr: str = None,
        gas_multiplier: Union[float, int] = EVM_ESTIMATED_FEE_MULTIPLIER,
        value: int = None,
        gas_additional: bool = True
):
    if not from_addr:
        from_addr = self.public_key

    tx_params = {
        "chainId": self.w3.eth.chain_id,
        "nonce": self.w3.eth.get_transaction_count(self.public_key),
        "from": Web3.to_checksum_address(from_addr),
        "to": Web3.to_checksum_address(to_addr)
    }

    if data:
        tx_params["data"] = data

    if value:
        tx_params["value"] = value

    if gas_additional:
        gas_params = get_eip1559_params(self, gas_multiplier)
        tx_params["maxPriorityFeePerGas"] = gas_params[0]
        tx_params["maxFeePerGas"] = gas_params[1]

    try:
        tx_params["gas"] = int(self.w3.eth.estimate_gas(tx_params) * gas_multiplier)
    except Exception as e:
        raise Exception(f"Transaction failed: {e}")

    if not gas_additional:
        tx_params["gasPrice"] = self.w3.eth.gas_price

    sign = self.w3.eth.account.sign_transaction(tx_params, self.private_key)
    tx_result = self.w3.eth.send_raw_transaction(sign.rawTransaction)

    return tx_result


def get_eip1559_params(self, gas_multiplier) -> tuple[int, int]:
    w3 = Web3(provider=Web3.HTTPProvider(endpoint_uri=self.chain.rpc))

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    last_block = w3.eth.get_block("latest")

    max_priority_fee_per_gas = get_max_priority_fee_per_gas(w3=w3, block=last_block)
    base_fee = int(last_block["baseFeePerGas"] * gas_multiplier)
    max_fee_per_gas = max(base_fee, base_fee + max_priority_fee_per_gas)

    return max_priority_fee_per_gas, max_fee_per_gas


def get_max_priority_fee_per_gas(w3: Web3, block: dict) -> int:
    block_number = block["number"]
    latest_block_transaction_count = w3.eth.get_block_transaction_count(block_number)
    max_priority_fee_per_gas_list = []

    for tx_index in range(latest_block_transaction_count):
        try:
            transaction = w3.eth.get_transaction_by_block(block_number, tx_index)
            if "maxPriorityFeePerGas" in transaction:
                max_priority_fee_per_gas_list.append(transaction["maxPriorityFeePerGas"])
        except Exception:
            continue

    if not max_priority_fee_per_gas_list:
        max_priority_fee_per_gas = w3.eth.max_priority_fee
    else:
        max_priority_fee_per_gas_list.sort()
        max_priority_fee_per_gas = max_priority_fee_per_gas_list[len(max_priority_fee_per_gas_list) // 2]

    return max_priority_fee_per_gas


def verify_tx(self, tx_hash) -> bool:
    try:
        data = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)

        if "status" in data and data["status"] == 1:
            logger.success(f"Transaction was successful: {self.chain.explorer}tx/{tx_hash.hex()}")
            return True
        else:
            logger.error(f'Transaction failed {data["transactionHash"].hex()}')
            return False

    except Exception as e:
        logger.error(f"Unexpected error in verify_tx function: {e}")
        return False


def get_layerswap_deposit_address(amount: Union[float, Decimal], evm_address: str, source_chain: Chain, proxy: str):
    api = LayerSwapAPI(proxy=proxy)

    layerswap_config = LayerswapDataItem(
        amount=amount,
        destination="STARKNET_MAINNET",
        source=LAYERSWAP_BRIDGE_ADDRESSES[source_chain.chain_id],
        destination_address=evm_address,
        source_address=evm_address,
    )

    swap_id = api.create_swap(layerswap_config)['swap_id']
    watch_id = api.get_swap(swap_id)['sequence_number']
    deposit_address = api.get_deposit_address(LAYERSWAP_BRIDGE_ADDRESSES[source_chain.chain_id])['address']
    api.close_session_sync()

    return deposit_address


def get_orbiter_total_value(amount: TokenAmount):
    return amount.wei + ARBITRUM_ORBITER_WITHHOLDING_FEE + ORBITER_STARKNET_IDENTIFICATION_CODE
