from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp

from gitbook import endpoints
from gitbook.models import organization, space, user

if TYPE_CHECKING:
    from gitbook.endpoint import Paginator


class Client:
    def __init__(
        self, token: str, *, base_url: str = "https://api.gitbook.com/"
    ) -> None:
        self.base_url = base_url
        self.token = token

        self.__session: aiohttp.ClientSession | None = None

    async def cleanup(self) -> None:
        if self.__session and not self.__session.closed:
            await self.__session.close()

    async def get_user(self, id: str | None = None) -> user.User:
        if id is None:
            return await endpoints.CURRENT_USER.execute(self)
        else:
            return await endpoints.USER.execute(self, id=id)

    def get_spaces(self) -> Paginator[space.Space]:
        return endpoints.SPACES.execute(self)

    def get_organizations(self) -> Paginator[organization.Organization]:
        return endpoints.ORGANIZATIONS.execute(self)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.__session is None or self.__session.closed:
            headers: dict[str, str] = {"Authorization": f"Bearer {self.token}"}
            self.__session = aiohttp.ClientSession(
                self.base_url, headers=headers
            )

        return self.__session
