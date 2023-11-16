import requests
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

from config import USE_PROXY


class BaseAPI:
    def __init__(self, proxy: str, use_aiohttp: bool = False) -> None:
        self.session = requests.Session()
        proxy_url = f"http://{proxy}"

        if not use_aiohttp:
            if USE_PROXY:
                self.session.proxies = {"https": proxy_url}

        if use_aiohttp:
            if USE_PROXY:    
                self.session = ClientSession(connector=ProxyConnector.from_url(proxy_url))
            else:
                self.session = ClientSession()

    async def close_session(self):
        await self.session.close()
    
    def close_session_sync(self):
        self.session.close()
