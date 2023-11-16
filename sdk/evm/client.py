from web3 import Web3

from config import (
    EVM_ETH_MIN_BALANCE,
    TX_DELAY_RANGE,
    EVM_GAS_THRESHOLD,
    GAS_DELAY_RANGE
)
from constants import (
    EVM_ORBITER_BRIGDE_ADDRESSES
)
from sdk.apis.starkgate import StarkgateAPI
from sdk.evm.utils import (
    get_layerswap_deposit_address,
    get_orbiter_total_value,
    init_web3,
    send_transaction,
    verify_tx
)
from sdk.helpers.decorators import (
    prepare_calling_functions,
    wait,
    evm_gas_delay,
    check_balance_evm
)
from sdk.helpers.logger import logger
from sdk.models.chain import Chain
from sdk.models.evm_contract import (
    ORBITER_BRIDGE_CONTRACT,
    STARKGATE_BRIDGE_CONTRACT
)
from sdk.models.token_amount import TokenAmount


@prepare_calling_functions(
    check_balance_evm(min_balance=EVM_ETH_MIN_BALANCE),
    evm_gas_delay(gas_threshold=EVM_GAS_THRESHOLD, delay_range=GAS_DELAY_RANGE),
    wait(delay_range=TX_DELAY_RANGE)
)
class EvmClient:
    def __init__(self, private_key: str, chain: Chain, proxy: str = None):
        self.private_key = private_key
        self.chain = chain
        self.proxy = proxy
        self.w3 = init_web3(self)
        self.public_key = Web3.to_checksum_address(self.w3.eth.account.from_key(private_key=private_key).address)
        self.address = Web3.to_checksum_address(self.w3.eth.account.from_key(private_key=private_key).address)

    def starkgate_bridge(self, amount: float, starknet_address: str):
        logger.info(f"[STARKGATE] Bridge {amount} to {starknet_address}")
        amount = TokenAmount(amount=amount, wei=False)

        bridge_contract = self.w3.eth.contract(
            abi=STARKGATE_BRIDGE_CONTRACT.abi,
            address=Web3.to_checksum_address(STARKGATE_BRIDGE_CONTRACT.address)
        )

        data = bridge_contract.encodeABI(
            'deposit',
            args=(
                amount.wei,
                int(starknet_address, 16)
            )
        )

        api = StarkgateAPI(proxy=self.proxy)
        message_fee = api.get_message_fee(amount, starknet_address)
        api.close_session_sync()

        if not message_fee:
            return False

        total_value = amount.wei + message_fee

        tx_hash = send_transaction(
            self,
            to_addr=Web3.to_checksum_address(STARKGATE_BRIDGE_CONTRACT.address),
            data=data,
            value=total_value
        )

        return verify_tx(self, tx_hash=tx_hash)

    def orbiter_bridge(self, amount: float, starknet_address: str):
        # Orbiter max digits after the decimal point is 6(six).
        # Doing more can lead to incorrect dest network id concatenate
        # Orbiter _ext item at payload has 03 prefix(Checked only on ARB)

        logger.info(f"[ORBITER] Bridge {amount} to {starknet_address}")
        amount = TokenAmount(
            amount=round(amount, 6),
            wei=False
        )

        swap_contract = self.w3.eth.contract(
            abi=ORBITER_BRIDGE_CONTRACT.abi,
            address=Web3.to_checksum_address(ORBITER_BRIDGE_CONTRACT.address)
        )

        destination_address = starknet_address[2:]
        destination_bytes_prefix = bytes.fromhex("03")
        destination_address_bytes = destination_bytes_prefix + bytes.fromhex(
            destination_address.zfill(
                len(destination_address) + len(destination_address) % 2)
        )

        data = swap_contract.encodeABI(
            'transfer',
            args=(
                EVM_ORBITER_BRIGDE_ADDRESSES[self.chain.chain_id],
                destination_address_bytes
            )
        )

        total_value = get_orbiter_total_value(amount)
        logger.info(f"Total value: {total_value}")

        tx_hash = send_transaction(
            self,
            to_addr=Web3.to_checksum_address(ORBITER_BRIDGE_CONTRACT.address),
            data=data,
            value=total_value
        )

        return verify_tx(self, tx_hash=tx_hash)

    def layerswap_bridge(self, amount: float, starknet_address: str):
        logger.info(f"[LAYERSWAP] Bridge {amount} to {starknet_address}")
        amount = TokenAmount(amount=amount, wei=False)

        deposit_address = get_layerswap_deposit_address(amount.ether, starknet_address, self.chain, self.proxy)

        tx_hash = send_transaction(
            self,
            to_addr=self.w3.to_checksum_address(deposit_address),
            value=amount.wei,
            gas_additional=False
        )

        return verify_tx(self, tx_hash=tx_hash)
