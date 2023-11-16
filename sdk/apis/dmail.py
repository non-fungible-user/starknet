from sdk.apis.base_api import BaseAPI
from constants import DMAIL_THEME_API_URL


class DmailAPI(BaseAPI):
    def __init__(self, proxy: str) -> None:
        super().__init__(proxy, use_aiohttp=True)

    async def get_random_theme(self):
        response = await self.session.get(url=DMAIL_THEME_API_URL)
        return await response.json()
