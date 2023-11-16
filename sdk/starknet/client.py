from datetime import datetime, timezone

from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.account.account import Account
from starknet_py.net.client_models import Call
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair

from config import (
    GAS_DELAY_RANGE,
    STARKNET_GAS_THRESHOLD,
    TX_DELAY_RANGE,
    STARKNET_ETH_MIN_BALANCE
)
from constants import (
    STARKNET_MYSWAP_CONTRACT_ADDRESS,
    STARKNET_ETH_TOKEN_ADDRESS,
    STARKNET_NFT_MARKETPLACE,
    STARKNET_DMAIL_CONTRACT_ADDRESS,
    STARKNET_JEDISWAP_CONTRACT_ADDRESS,
    STARKNET_TENKSWAP_CONTRACT_ADDRESS,
    STARKNET_SITHSWAP_CONTRACT_ADDRESS,
    STARKNET_AVNU_CONTRACT_ADDRESS,
    STARKNET_STARKGATE_CONTRACT_ADDRESS,
    STARKNET_ORBITER_CONTRACT_ADDRESS,
    STARKNET_LAYERSWAP_CONTRACT_ADDRESS,
    STARKNET_LAYERSWAP_WATCHDOG_ADDRESS,
    STARKNET_FIBROUS_CONTRACT_ADDRESS,
    STARKNET_MY_IDENTITY_CONTRACT_ADDRESS,
    STARKNET_ZKLEND_CONTRACT_ADDRESS,
    STARKNET_TOKEN_NAMES,
    STARKNET_ESTIMATED_FEE_MULTIPLIER,
    STARKNET_STARKVERSE_CONTRACT_ADDRESS
)
from sdk.apis.avnuswap import AvnuSwapAPI
from sdk.apis.dmail import DmailAPI
from sdk.helpers.decorators import (
    prepare_calling_functions,
    check_balance_starknet,
    wait_async,
    starknet_gas_delay
)
from sdk.helpers.logger import logger
from sdk.models.chain import Chain
from sdk.starknet.utils import (
    get_address,
    get_min_amount_out,
    get_pool_id,
    get_proxy_contract,
    float_to_wei,
    send_tx,
    get_contract,
    get_token_contract,
    get_orbiter_total_value,
    get_orbiter_destination_address,
    get_layerswap_watch_id,
    get_starknet_id,
    generate_random_evm_address
)


@prepare_calling_functions(
    check_balance_starknet(min_balance=STARKNET_ETH_MIN_BALANCE),
    starknet_gas_delay(gas_threshold=STARKNET_GAS_THRESHOLD, delay_range=GAS_DELAY_RANGE),
    wait_async(delay_range=TX_DELAY_RANGE)
)
class StarknetClient(Account):
    def __init__(
            self,
            private_key: str,
            salt: str = None,
            proxy: str = None,
            rpc=GatewayClient(net="mainnet")
    ):
        self.private_key = int(private_key, 0)
        self.proxy = proxy
        self.key_pair = KeyPair.from_private_key(self.private_key)
        self.ESTIMATED_FEE_MULTIPLIER = STARKNET_ESTIMATED_FEE_MULTIPLIER
        self.rpc = rpc

        super().__init__(
            address=get_address(self.key_pair, salt),
            client=rpc,
            signer=None,
            key_pair=self.key_pair,
            chain=StarknetChainId.MAINNET
        )

    async def approve(self, token_in_addr: str, amount_in: float, contract_addr: str) -> bool:
        logger.info(f"[APPROVE] {amount_in} {STARKNET_TOKEN_NAMES[token_in_addr]} to"
                    f"{contract_addr}")

        amount_in = float_to_wei(amount_in, token_in_addr)
        token_in_addr = int(token_in_addr, 16)
        contract_addr = int(contract_addr, 16)

        token_contract = await get_token_contract(self, token_in_addr)
        approve_call = token_contract.functions["approve"].prepare(
            spender=contract_addr,
            amount=amount_in
        )

        return await send_tx(self, approve_call)

    async def transfer(self, token_in_addr: str, amount_in: float, recipient: str) -> bool:
        logger.info(f"[TRANSFER] {amount_in} {STARKNET_TOKEN_NAMES[token_in_addr]} to"
                    f"{recipient}")

        amount_in = float_to_wei(amount_in, token_in_addr)
        recipient = int(recipient, 16)
        token_in_addr = int(token_in_addr, 16)

        token_contract = await get_token_contract(self, token_in_addr)
        transfer_call = token_contract.functions["transfer"].prepare(
            recipient=recipient,
            amount=amount_in
        )

        return await send_tx(self, transfer_call)

    async def dmail_send_mail(self) -> bool:
        logger.info(f"[DMAIL] Try to send mail")

        random_evm_address = generate_random_evm_address()
        to = int(random_evm_address, 16)

        api = DmailAPI(proxy=self.proxy)
        theme = (await api.get_random_theme())[0]
        await api.close_session()

        dmail_contract = await get_contract(self, STARKNET_DMAIL_CONTRACT_ADDRESS)
        call = dmail_contract.functions["transaction"].prepare(to=to, theme=theme)

        return await send_tx(self, call)

    async def nft_marketplace_allowance(self, allowance_amount: int) -> bool:
        logger.info(f"[NFT MARKETPLACE] Try to get allowance")

        eth_token_contract = await get_token_contract(self, int(STARKNET_ETH_TOKEN_ADDRESS, 16))
        call = eth_token_contract.functions["increaseAllowance"].prepare(
            spender=int(STARKNET_NFT_MARKETPLACE, 16),
            added_value=float_to_wei(allowance_amount, STARKNET_ETH_TOKEN_ADDRESS)
        )

        return await send_tx(self, call)

    async def myswap_swap(self, token_in_addr: str, token_out_addr: str, amount_in: float) -> bool:
        logger.info(f"[MYSWAP] Try to swap {amount_in} {STARKNET_TOKEN_NAMES[token_in_addr]} "
                    f"to {STARKNET_TOKEN_NAMES[token_out_addr]}")

        min_amount_out = float_to_wei(
            amount=get_min_amount_out(amount_in, token_in_addr, token_out_addr),
            token_addr=token_out_addr
        )

        pool_id = get_pool_id(token_in_addr, token_out_addr)
        amount_in = float_to_wei(amount_in, token_in_addr)
        token_in_addr = int(token_in_addr, 16)
        myswap_address = int(STARKNET_MYSWAP_CONTRACT_ADDRESS, 16)

        token_contract = await get_token_contract(self, token_in_addr)
        approve_call = token_contract.functions["approve"].prepare(
            spender=myswap_address,
            amount=amount_in
        )

        myswap_contract = await get_proxy_contract(self, myswap_address)
        swap_call = myswap_contract.functions["swap"].prepare(
            pool_id=pool_id,
            token_from_addr=token_in_addr,
            amount_from=amount_in,
            amount_to_min=min_amount_out
        )

        return await send_tx(self, [approve_call, swap_call])

    async def jediswap_swap(self, token_in_addr: str, token_out_addr: str, amount_in: float) -> bool:
        logger.info(f"[JEDISWAP] Try to swap {amount_in} {STARKNET_TOKEN_NAMES[token_in_addr]} "
                    f"to {STARKNET_TOKEN_NAMES[token_out_addr]}")

        min_amount_out = float_to_wei(
            amount=get_min_amount_out(amount_in, token_in_addr, token_out_addr),
            token_addr=token_out_addr
        )

        amount_in = float_to_wei(amount_in, token_in_addr)
        token_in_addr = int(token_in_addr, 16)
        token_out_addr = int(token_out_addr, 16)
        jediswap_address = int(STARKNET_JEDISWAP_CONTRACT_ADDRESS, 16)

        token_contract = await get_token_contract(self, token_in_addr)
        approve_call = token_contract.functions["approve"].prepare(
            spender=jediswap_address,
            amount=amount_in
        )

        jediswap_contract = await get_proxy_contract(self, jediswap_address)
        swap_call = jediswap_contract.functions["swap_exact_tokens_for_tokens"].prepare(
            amountIn=amount_in,
            amountOutMin=min_amount_out,
            path=[token_in_addr, token_out_addr],
            to=self.address,
            deadline=int(datetime.now(timezone.utc).timestamp()) + 3600
        )

        return await send_tx(self, [approve_call, swap_call])

    async def tenkswap_swap(self, token_in_addr: str, token_out_addr: str, amount_in: float) -> bool:
        logger.info(f"[10KSWAP] Try to swap {amount_in} {STARKNET_TOKEN_NAMES[token_in_addr]} "
                    f"to {STARKNET_TOKEN_NAMES[token_out_addr]}")

        min_amount_out = float_to_wei(
            amount=get_min_amount_out(amount_in, token_in_addr, token_out_addr),
            token_addr=token_out_addr
        )

        amount_in = float_to_wei(amount_in, token_in_addr)
        token_in_addr = int(token_in_addr, 16)
        token_out_addr = int(token_out_addr, 16)
        tenkswap_address = int(STARKNET_TENKSWAP_CONTRACT_ADDRESS, 16)

        token_contract = await get_token_contract(self, token_in_addr)
        approve_call = token_contract.functions["approve"].prepare(
            spender=tenkswap_address,
            amount=amount_in
        )

        tenkswap_contract = await get_contract(self, tenkswap_address)
        swap_call = tenkswap_contract.functions["swapExactTokensForTokens"].prepare(
            amountIn=amount_in,
            amountOutMin=min_amount_out,
            path=[token_in_addr, token_out_addr],
            to=self.address,
            deadline=int(datetime.now(timezone.utc).timestamp()) + 3600
        )

        return await send_tx(self, [approve_call, swap_call])

    async def sithswap_swap(self, token_in_addr: str, token_out_addr: str, amount_in: float) -> bool:
        logger.info(f"[SITHSWAP] Try to swap {amount_in} {STARKNET_TOKEN_NAMES[token_in_addr]} "
                    f"to {STARKNET_TOKEN_NAMES[token_out_addr]}")

        min_amount_out = float_to_wei(
            amount=get_min_amount_out(amount_in, token_in_addr, token_out_addr),
            token_addr=token_out_addr
        )

        amount_in = float_to_wei(amount_in, token_in_addr)
        token_in_addr = int(token_in_addr, 16)
        token_out_addr = int(token_out_addr, 16)
        sithswap_address = int(STARKNET_SITHSWAP_CONTRACT_ADDRESS, 16)

        token_contract = await get_token_contract(self, token_in_addr)
        approve_call = token_contract.functions["approve"].prepare(
            spender=sithswap_address,
            amount=amount_in
        )

        sithswap_contract = await get_contract(self, sithswap_address)
        swap_call = sithswap_contract.functions["swapExactTokensForTokensSupportingFeeOnTransferTokens"].prepare(
            amount_in=amount_in,
            amount_out_min=min_amount_out,
            routes=[{
                "from_address": token_in_addr,
                "to_address": token_out_addr,
                "stable": 0
            }],
            to=self.address,
            deadline=int(datetime.now(timezone.utc).timestamp()) + 3600
        )

        return await send_tx(self, [approve_call, swap_call])

    async def avnu_swap(self, token_in_addr: str, token_out_addr: str, amount_in: float) -> bool:
        logger.info(f"[AVNU] Try to swap {amount_in} {STARKNET_TOKEN_NAMES[token_in_addr]} "
                    f"to {STARKNET_TOKEN_NAMES[token_out_addr]}")

        amount_in = float_to_wei(amount_in, token_in_addr)

        token_contract = await get_token_contract(self, int(token_in_addr, 16))
        approve_call = token_contract.functions["approve"].prepare(
            spender=int(STARKNET_AVNU_CONTRACT_ADDRESS, 16),
            amount=amount_in
        )

        api = AvnuSwapAPI(proxy=self.proxy)
        quote_id = await api.get_avnu_swap_quote_id(token_in_addr, token_out_addr, amount_in)
        build_tx = await api.get_build_avnu_swap_tx(quote_id, self.address)
        await api.close_session()

        calldata = [int(item, 16) for item in build_tx["calldata"]]

        swap_call = Call(
            to_addr=int(STARKNET_AVNU_CONTRACT_ADDRESS, 16),
            selector=get_selector_from_name(build_tx["entrypoint"]),
            calldata=calldata,
        )

        return await send_tx(self, [approve_call, swap_call])

    async def fibrous_swap(self, token_in_addr: str, token_out_addr: str, amount_in: float) -> bool:
        logger.info(f"[FIBROUS] Try to swap {amount_in} {STARKNET_TOKEN_NAMES[token_in_addr]} "
                    f"to {STARKNET_TOKEN_NAMES[token_out_addr]}")

        min_amount_out = float_to_wei(
            amount=get_min_amount_out(amount_in, token_in_addr, token_out_addr),
            token_addr=token_out_addr
        )
        amount_in = float_to_wei(amount_in, token_in_addr)
        token_in_addr = int(token_in_addr, 16)
        token_out_addr = int(token_out_addr, 16)
        fibrous_address = int(STARKNET_FIBROUS_CONTRACT_ADDRESS, 16)

        token_contract = await get_token_contract(self, token_in_addr)
        approve_call = token_contract.functions["approve"].prepare(
            spender=fibrous_address,
            amount=amount_in
        )

        fibrous_contract = await get_proxy_contract(self, fibrous_address)
        swap_call = fibrous_contract.functions["swap"].prepare(
            swaps=[{
                "token_in": token_in_addr,
                "token_out": token_out_addr,
                "rate": 1000000,
                "protocol": 2,
                "pool_address": ""
            }],
            params=[{
                "token_in": token_in_addr,
                "token_out": token_out_addr,
                "amount": amount_in,
                "min_received": min_amount_out,
                "destination": self.address
            }]
        )

        return await send_tx(self, [approve_call, swap_call])

    async def my_identity_mint(self) -> bool:
        logger.info(f"[MYIDENTITY] Try to mint NFT")

        contract_address = int(STARKNET_MY_IDENTITY_CONTRACT_ADDRESS, 16)
        contract = await get_proxy_contract(self, contract_address)
        call = contract.functions["mint"].prepare(starknet_id=get_starknet_id())

        return await send_tx(self, call)

    async def starkverse_mint(self) -> bool:
        logger.info(f"[STARKVERSE] Try to mint NFT")

        contract_address = int(STARKNET_STARKVERSE_CONTRACT_ADDRESS, 16)
        contract = await get_contract(self, contract_address)
        call = contract.functions["publicMint"].prepare(to=self.address)

        return await send_tx(self, call)

    async def zklend_deposit(self, amount_in: float) -> bool:
        logger.info(f"[ZKLEND] Try to deposit {amount_in} ETH")

        amount_in = float_to_wei(amount_in, STARKNET_ETH_TOKEN_ADDRESS)
        token_addr = int(STARKNET_ETH_TOKEN_ADDRESS, 16)
        zklend_address = int(STARKNET_ZKLEND_CONTRACT_ADDRESS, 16)

        token_contract = await get_token_contract(self, token_addr)
        approve_call = token_contract.functions["approve"].prepare(
            spender=zklend_address,
            amount=amount_in
        )

        zklend_contract = await get_contract(self, zklend_address)
        deposit_call = zklend_contract.functions["deposit"].prepare(
            token=token_addr,
            amount=amount_in
        )

        enable_collateral_call = zklend_contract.functions["enable_collateral"].prepare(token=token_addr)

        return await send_tx(self, [approve_call, deposit_call, enable_collateral_call])

    async def zklend_withdraw(self) -> bool:
        logger.info(f"[ZKLEND] Try to withdraw ETH")

        token_addr = int(STARKNET_ETH_TOKEN_ADDRESS, 16)
        zklend_address = int(STARKNET_ZKLEND_CONTRACT_ADDRESS, 16)

        zklend_contract = await get_contract(self, zklend_address)
        withdraw_all_call = zklend_contract.functions["withdraw_all"].prepare(token=token_addr)

        return await send_tx(self, withdraw_all_call)

    async def starkgate_bridge(self, amount: float, evm_address: str):
        logger.info(f"[STARKGATE] Bridge {amount} to {evm_address}")

        contract_address = int(STARKNET_STARKGATE_CONTRACT_ADDRESS, 16)
        contract = await get_proxy_contract(self, contract_address)
        bridge_call = contract.functions["initiate_withdraw"].prepare(
            l1_recipient=int(evm_address, 16),
            amount=float_to_wei(amount, STARKNET_ETH_TOKEN_ADDRESS)
        )

        return await send_tx(self, bridge_call)

    async def orbiter_bridge(self, amount: float, evm_address: str, destination_chain: Chain):
        logger.info(f"[ORBITER] Bridge {amount} to {evm_address}")

        amount = float_to_wei(amount, STARKNET_ETH_TOKEN_ADDRESS)
        total_value = get_orbiter_total_value(amount, destination_chain)
        destination_address = get_orbiter_destination_address(destination_chain)
        orbiter_address = int(STARKNET_ORBITER_CONTRACT_ADDRESS, 16)

        token_contract = await get_token_contract(self, int(STARKNET_ETH_TOKEN_ADDRESS, 16))
        approve_call = token_contract.functions["approve"].prepare(
            spender=orbiter_address,
            amount=total_value
        )

        orbiter_contract = await get_contract(self, orbiter_address)
        bridge_call = orbiter_contract.functions["transferERC20"].prepare(
            _token=STARKNET_ETH_TOKEN_ADDRESS,
            _to=destination_address,
            _amount=total_value,
            _ext=int(evm_address, 16)
        )

        return await send_tx(self, [approve_call, bridge_call])

    async def layerswap_bridge(self, amount: float, evm_address: str, destination_chain: Chain):
        logger.info(f"[LAYERSWAP] Bridge {amount} to {evm_address}")

        token_address = int(STARKNET_ETH_TOKEN_ADDRESS, 16)
        layerswap_address = int(STARKNET_LAYERSWAP_CONTRACT_ADDRESS, 16)
        layerswap_watchdog_address = int(STARKNET_LAYERSWAP_WATCHDOG_ADDRESS, 16)

        watch_id = get_layerswap_watch_id(amount, evm_address, destination_chain, self.proxy)

        layerswap_watchdog_contract = await get_contract(self, layerswap_watchdog_address)
        watch_call = layerswap_watchdog_contract.functions["watch"].prepare(_Id=watch_id)

        token_contract = await get_token_contract(self, token_address)
        transfer_call = token_contract.functions["transfer"].prepare(
            recipient=layerswap_address,
            amount=float_to_wei(amount, hex(token_address))
        )

        return await send_tx(self, [watch_call, transfer_call])
