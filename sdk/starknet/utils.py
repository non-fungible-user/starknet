import random

from eth_keys import keys
from pycoingecko import CoinGeckoAPI
from starknet_py.contract import Contract
from starknet_py.hash.address import compute_address
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.proxy.contract_abi_resolver import ProxyConfig

from config import (
    WALLET_APPLICATION,
    SLIPPAGE, CAIRO_VERSION,
    IS_WALLET_CREATED_AFTER_CAIRO_1_RELEASED
)
from constants import (
    BRAAVOS_PROXY_CLASS_HASH,
    CAIRO_0_ARGENTX_PROXY_CLASS_HASH,
    BRAAVOS_IMPLEMENTATION_CLASS_HASH,
    ARGENTX_IMPLEMENTATION_CLASS_HASH,
    STARKNET_MYSWAP_POOL_IDS,
    COINGECKO_TOKEN_IDS,
    STARKNET_DECIMALS,
    STARKNET_ETH_TOKEN_ADDRESS,
    STARKNET_DAI_TOKEN_ADDRESS,
    STARKNET_ORBITER_WITHHOLDING_FEE,
    ORBITER_CHAIN_IDS,
    STARKNET_ORBITER_BRIDGE_ADDRESSES,
    LAYERSWAP_BRIDGE_ADDRESSES,
    CAIRO_1_ARGENTX_PROXY_CLASS_HASH
)
from sdk.apis.layerswap import LayerSwapAPI
from sdk.helpers.logger import logger
from sdk.models.chain import Chain
from sdk.models.layerswap_swap_config import LayerswapDataItem
from sdk.models.proxy_contract import CustomProxyCheck


def get_starknet_explorer_link(tx_hash: str) -> str:
    return f"https://starkscan.co/tx//{tx_hash}"


async def get_contract(self, contract_address):
    return await Contract.from_address(address=contract_address, provider=self)


async def get_proxy_contract(self, contract_address):
    return await Contract.from_address(address=contract_address, provider=self, proxy_config=True)


async def get_custom_proxy_contract(self, contract_address, proxy_config):
    return await Contract.from_address(address=contract_address, provider=self, proxy_config=proxy_config)


def get_orbiter_total_value(amount: int, evm_chain: Chain) -> int:
    destination_chain_id = ORBITER_CHAIN_IDS[evm_chain.chain_id]
    total_value = amount + STARKNET_ORBITER_WITHHOLDING_FEE + destination_chain_id

    return total_value


def get_orbiter_destination_address(evm_chain: Chain) -> str:
    return STARKNET_ORBITER_BRIDGE_ADDRESSES[evm_chain.chain_id]


def get_layerswap_watch_id(amount: float, evm_address: str, destination_chain: Chain, proxy: str):
    api = LayerSwapAPI(proxy=proxy)

    layerswap_config = LayerswapDataItem(
        amount=amount,
        destination=LAYERSWAP_BRIDGE_ADDRESSES[destination_chain.chain_id],
        source="STARKNET_MAINNET",
        destination_address=evm_address,
        source_address=evm_address,
    )

    swap_id = api.create_swap(layerswap_config)['swap_id']
    watch_id = api.get_swap(swap_id)['sequence_number']
    api.close_session_sync()

    return watch_id


def generate_random_evm_address() -> str:
    private_key_bytes = bytes([random.randint(0, 255) for _ in range(32)])
    private_key = keys.PrivateKey(private_key_bytes)
    public_address = private_key.public_key.to_checksum_address()

    return public_address


async def get_token_contract(self, contract_addr):
    if contract_addr == int(STARKNET_ETH_TOKEN_ADDRESS, 16):
        return await get_proxy_contract(self, contract_addr)
    elif contract_addr == int(STARKNET_DAI_TOKEN_ADDRESS, 16):
        return await get_contract(self, contract_addr)
    else:
        proxy_config = ProxyConfig(proxy_checks=[CustomProxyCheck()])
        return await get_custom_proxy_contract(self, contract_addr, proxy_config)


async def send_tx(self, calls):
    tx = None

    try:
        tx = await self.execute(calls=calls, auto_estimate=True, cairo_version=CAIRO_VERSION)
        if await self.client.wait_for_tx(tx_hash=tx.transaction_hash, check_interval=20, retries=10000):
            logger.success(f"Transaction was successful: {get_starknet_explorer_link(hex(tx.transaction_hash))}")
            return True

    except Exception as e:
        if tx is not None and 'L2toL1Message.__init__()' in str(e):
            logger.success(
                f"Transaction was successful (L2toL1Message): {get_starknet_explorer_link(hex(tx.transaction_hash))}"
            )
            return True
        else:
            logger.error(f"Send tx error: {str(e)}")
            return False


def get_starknet_id():
    # len(starknet_id) always 12
    return random.randint(10 ** 11, 10 ** 12 - 1)


def float_to_wei(amount: float, token_addr: str) -> int:
    try:
        decimals = get_decimals(token_addr)
        return int(amount * 10 ** decimals)
    except Exception as e:
        logger.error(f"Error while get wei from float: {str(e)}")


def wei_to_float(amount: int, token_addr: str) -> float:
    try:
        decimals = get_decimals(token_addr)
        return float(amount / 10 ** decimals)
    except Exception as e:
        logger.error(f"Error while get float from wei: {str(e)}")


def get_decimals(token_addr: str) -> int:
    return STARKNET_DECIMALS[token_addr]


def get_amount_out_wei(min_amount_out: int, token_out_addr: str) -> int:
    min_amount_out_float = wei_to_float(min_amount_out, token_out_addr)
    amount_out = min_amount_out_float / ((100 - SLIPPAGE) / 100)
    amount_out_wei = float_to_wei(amount_out, token_out_addr)

    return amount_out_wei


def get_address(key_pair, salt: int = None) -> int:
    if WALLET_APPLICATION == "braavos":
        return get_braavos_address(key_pair=key_pair)
    elif WALLET_APPLICATION == "argentx":
        return get_argentx_address(key_pair=key_pair)
    elif WALLET_APPLICATION == "salts":
        if salt is None:
            raise Exception('Salt should not be empty')
        return get_address_with_salt(key_pair=key_pair, salt=salt)
    else:
        raise Exception("Get address error")


def get_min_amount_out(amount_in, token_in_addr, token_out_addr):
    amount_out = get_amount_out(amount_in, get_token_id(token_in_addr), get_token_id(token_out_addr))
    return amount_out * (100.0 - SLIPPAGE) / 100


def get_token_id(token_addr):
    return COINGECKO_TOKEN_IDS[token_addr] if token_addr in COINGECKO_TOKEN_IDS.keys() else None


def get_pool_id(token_in, token_out):
    for pool_id, addresses in STARKNET_MYSWAP_POOL_IDS.items():
        if token_in in addresses and token_out in addresses:
            return pool_id
    return None


def get_braavos_address(key_pair) -> int:
    proxy_class_hash = BRAAVOS_PROXY_CLASS_HASH
    implementation_class_hash = BRAAVOS_IMPLEMENTATION_CLASS_HASH

    selector = get_selector_from_name("initializer")
    call_data = [key_pair.public_key]

    return compute_address(
        class_hash=proxy_class_hash,
        constructor_calldata=[implementation_class_hash, selector, len(call_data), *call_data],
        salt=key_pair.public_key
    )


def get_argentx_address(key_pair) -> int:
    implementation_class_hash = ARGENTX_IMPLEMENTATION_CLASS_HASH
    selector = get_selector_from_name("initialize")
    call_data = [key_pair.public_key, 0]

    if IS_WALLET_CREATED_AFTER_CAIRO_1_RELEASED:
        proxy_class_hash = CAIRO_1_ARGENTX_PROXY_CLASS_HASH
        constructor_calldata = call_data
    else:
        proxy_class_hash = CAIRO_0_ARGENTX_PROXY_CLASS_HASH
        constructor_calldata = [implementation_class_hash, selector, len(call_data), *call_data]

    return compute_address(
        class_hash=proxy_class_hash,
        constructor_calldata=constructor_calldata,
        salt=key_pair.public_key
    )


def get_address_with_salt(key_pair, salt) -> int:
    calldata = [
        int(hex(ARGENTX_IMPLEMENTATION_CLASS_HASH), 16),
        int("0x79dc0da7c54b95f10aa182ad0a46400db63156920adb65eca2654c0945a463", 16),
        int("0x2", 16), int(hex(key_pair.public_key), 16), int("0x0", 16)
    ]

    return compute_address(
        class_hash=int(CAIRO_0_ARGENTX_PROXY_CLASS_HASH),
        constructor_calldata=calldata,
        salt=int(salt),
        deployer_address=0
    )


def get_cg_tokens_price_usd(ids: dict):
    try:
        ids = list(ids.values())
        res = CoinGeckoAPI().get_price(ids=ids, vs_currencies='usd')
        usd_prices = [res[token_id]["usd"] for token_id in ids]

        return usd_prices

    except Exception as e:
        raise Exception(f"fail to get coin price in usd by coingecko. Error: {str(e)}")


def get_coin_price_usd(token_in_id, token_out_id):
    try:
        res = CoinGeckoAPI().get_price(ids=[token_in_id, token_out_id], vs_currencies='usd')
        token_in_price = res[token_in_id]["usd"]
        token_out_price = res[token_out_id]["usd"]

        return token_in_price, token_out_price

    except Exception as e:
        raise Exception(f"fail to get coin price in usd by coingecko. Error: {str(e)}")


def get_amount_out(amount_in, token_in_id, token_out_id):
    try:
        token_in_price, token_out_price = get_coin_price_usd(token_in_id, token_out_id)
        amount_out = amount_in * token_in_price / token_out_price

        return amount_out

    except Exception as e:
        raise Exception(f"fail to get amount out. Error: {str(e)}")
