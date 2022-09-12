from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp

from gitbook import endpoints
from gitbook.models import space, user

if TYPE_CHECKING:
    from gitbook.endpoint import Paginator


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

    async def get_user(self, id: str | None = None) -> user.User:
        if id is None:
            return await endpoints.CURRENT_USER.execute(self)
        else:
            return await endpoints.USER.execute(self, id=id)

    def get_spaces(self) -> Paginator[space.Space]:
        return endpoints.SPACES.execute(self)

    @property
    def _session(self) -> aiohttp.ClientSession:
        if self.__session is None:
            raise AttributeError("Client not initialized.")
        return self.__session
