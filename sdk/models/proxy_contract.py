from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client import Client
from starknet_py.net.client_models import Call
from starknet_py.net.models import Address
from starknet_py.proxy.proxy_check import ProxyCheck


class CustomProxyCheck(ProxyCheck):
    async def implementation_address(self, address: Address, client: Client):
        return None

    async def implementation_hash(self, address: Address, client: Client):
        call = Call(
            to_addr=address,
            selector=get_selector_from_name("implementation"),
            calldata=[],
        )

        (implementation_hash,) = await client.call_contract(call=call)

        return implementation_hash
