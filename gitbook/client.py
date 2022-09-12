from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp

from gitbook import endpoints
from gitbook.models import space, user

if TYPE_CHECKING:
    from gitbook.endpoint import Paginated


class Client:
    def __init__(
        self, token: str, *, base_url: str = "https://api.gitbook.com/"
    ) -> None:
        self.base_url = base_url
        self.token = token

        self.__session: aiohttp.ClientSession | None = None

    async def connect(self) -> None:
        headers: dict[str, str] = {"Authorization": f"Bearer {self.token}"}

        self.__session = aiohttp.ClientSession(self.base_url, headers=headers)

    async def cleanup(self) -> None:
        await self._session.close()

    async def get_user(self) -> user.User:
        return await endpoints.USER.execute(self)

    def get_spaces(self) -> Paginated[space.Space]:
        return endpoints.SPACES.execute(self)

    @property
    def _session(self) -> aiohttp.ClientSession:
        if self.__session is None:
            raise AttributeError("Client not initialized.")
        return self.__session