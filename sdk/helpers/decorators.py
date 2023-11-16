import random
import time
from functools import wraps

from starknet_py.net.client_errors import ClientError
from tqdm import tqdm
from web3 import Web3

from constants import STARKNET_ETH_TOKEN_ADDRESS
from sdk.apis.starknet_gas_checker import GasAPI
from sdk.helpers.logger import logger
from sdk.models.chain import ethereum
from sdk.models.token_amount import TokenAmount


def prepare_calling_functions(*decorators):
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)):
                setattr(cls, attr, apply_decorators(getattr(cls, attr), decorators))
        return cls

    return decorate


def apply_decorators(func, decorators):
    if func.__name__ == "__init__":
        return func

    for decorator in decorators:
        func = decorator(func)
    return func


def wait(delay_range: list):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            random_delay = random.randint(*delay_range)
            with tqdm(total=random_delay, desc="Waiting", unit="s", dynamic_ncols=True, colour="blue") as pbar:
                for _ in range(random_delay):
                    time.sleep(1)
                    pbar.update(1)
            return result

        return wrapper

    return decorator


def wait_async(delay_range: list):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            random_delay = random.randint(*delay_range)
            with tqdm(total=random_delay, desc="Waiting", unit="s", dynamic_ncols=True, colour="blue") as pbar:
                for _ in range(random_delay):
                    time.sleep(1)
                    pbar.update(1)
            return result

        return wrapper

    return decorator


def check_balance_evm(min_balance):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            balance = self.w3.eth.get_balance(self.public_key)
            logger.info(f"[EVM] Balance of {self.address} is {TokenAmount(amount=balance, wei=True).ether}ETH")
            if balance < Web3.to_wei(min_balance, "ether"):
                raise Exception(f"(EVM) Balance is below minimum at {self.address}")
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


def check_balance_starknet(min_balance):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            balance = await self.get_balance(token_address=STARKNET_ETH_TOKEN_ADDRESS)
            logger.info(f"[STARKNET] Balance of {hex(self.address)} is {TokenAmount(amount=balance, wei=True).ether}ETH")
            if balance < Web3.to_wei(min_balance, "ether"):
                raise Exception(f"(Starknet) Balance is below minimum at {hex(self.address)}")
            return await func(self, *args, **kwargs)

        return wrapper

    return decorator


def evm_gas_delay(gas_threshold: int, delay_range: list):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            w3 = Web3(Web3.HTTPProvider(ethereum.rpc))
            while True:
                current_eth_gas_price = w3.eth.gas_price
                threshold = Web3.to_wei(gas_threshold, "gwei")
                if current_eth_gas_price > threshold:
                    random_delay = random.randint(*delay_range)

                    logger.warning(
                        f"Current gas fee {round(Web3.from_wei(current_eth_gas_price, 'gwei'), 2)} GWEI > Gas"
                        f" threshold {Web3.from_wei(threshold, 'gwei')} GWEI. Waiting for {random_delay} seconds...")

                    with tqdm(total=random_delay, desc="Waiting", unit="s", dynamic_ncols=True, colour="blue") as pbar:
                        for _ in range(random_delay):
                            time.sleep(1)
                            pbar.update(1)
                else:
                    break

            return func(*args, **kwargs)

        return wrapper

    return decorator


def starknet_gas_delay(gas_threshold: int, delay_range: list):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            while True:
                gas_api = GasAPI(proxy=self.proxy)
                current_starknet_gas_price = gas_api.get_last_block_gas_price()
                threshold = Web3.to_wei(gas_threshold, "gwei")
                if current_starknet_gas_price > threshold:
                    random_delay = random.randint(*delay_range)

                    logger.warning(
                        f"Current gas fee {round(Web3.from_wei(current_starknet_gas_price, 'gwei'), 2)} GWEI > Gas"
                        f" threshold {Web3.from_wei(threshold, 'gwei')} GWEI. Waiting for {random_delay} seconds...")

                    with tqdm(total=random_delay, desc="Waiting", unit="s", dynamic_ncols=True, colour="blue") as pbar:
                        for _ in range(random_delay):
                            time.sleep(1)
                            pbar.update(1)
                else:
                    break

            return func(self, *args, **kwargs)

        return wrapper

    return decorator


def evm_retry(attempts=5):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for index in range(attempts):
                try:
                    result = await func(*args, **kwargs)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"Attempt {index + 1} failed: {str(e)}")

            raise Exception("Failed after multiple attempts")

        return wrapper

    return decorator


def starknet_retry(attempts=5):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for index in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except ClientError:
                    logger.warning(f"Attempt {index + 1} failed: rpc is down, retrying in 30 seconds")
                    time.sleep(30)

            raise Exception("Failed after multiple attempts")

        return wrapper

    return decorator
