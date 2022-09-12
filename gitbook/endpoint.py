from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Generic, TypeVar

import aiohttp

if TYPE_CHECKING:
    from gitbook.abc.model import Model
    from gitbook.client import Client


_RETURN = TypeVar("_RETURN", bound="Model")
_LOGGER = logging.getLogger("gitbook")


class Endpoint(Generic[_RETURN]):
    API_VERSION = "v1"

    def __init__(self, method: str, path: str, model: type[_RETURN]) -> None:
        self.method = method
        self.path = f"/{self.API_VERSION}/{path}"
        self.model = model
        self.ratelimit = Ratelimit(self)

    async def execute(self, client: Client) -> _RETURN:
        await self.ratelimit.acquire()
        response = await client._session.request(self.method, self.path)
        self.ratelimit.parse_ratelimit(response)
        return await self.model._from_response(response)

    def __str__(self) -> str:
        return f"Endpoint({self.method}, {self.path})"

    def __repr__(self) -> str:
        return str(self)


class Ratelimit:
    def __init__(self, endpoint: Endpoint[_RETURN]) -> None:
        self.endpoint = endpoint

        self.ratelimit_limit: int | None = None
        self.ratelimit_remaining: int = 0

        self.waiting: list[asyncio.Future[None]] = []
        self.reset_task: asyncio.TimerHandle | None = None

    def _reset_ratelimit(self) -> None:
        self.reset_task = None
        _LOGGER.debug(f"{self.endpoint}: resetting ratelimit.")

        assert self.ratelimit_limit is not None
        self.ratelimit_remaining = self.ratelimit_limit

        for x, fut in enumerate(
            self.waiting.copy()[: self.ratelimit_remaining]
        ):
            fut.set_result(None)
            self.waiting.pop(x)

    async def acquire(self) -> None:
        if self.ratelimit_limit is None:
            _LOGGER.debug(f"{self.endpoint}: skipping ratelimit acquire.")
            return

        while self.ratelimit_remaining <= 0:
            _LOGGER.debug(f"{self.endpoint}: bucket empty, waiting...")
            fut: asyncio.Future[None] = asyncio.Future()
            self.waiting.append(fut)
            await fut

        self.ratelimit_remaining -= 1

    def parse_ratelimit(self, response: aiohttp.ClientResponse) -> None:
        if "X-Ratelimit-Limit" not in response.headers:
            _LOGGER.debug(f"{self.endpoint}: no ratelimit headers.")
            return

        self.ratelimit_limit = int(response.headers["X-Ratelimit-Limit"])
        self.ratelimit_remaining = int(
            response.headers["X-Ratelimit-Remaining"]
        )

        if self.reset_task is None:
            ratelimit_reset = float(response.headers["X-Ratelimit-Reset"])
            seconds_until_reset = time.time() - ratelimit_reset
            self.reset_task = asyncio.get_running_loop().call_later(
                seconds_until_reset, self._reset_ratelimit
            )
            _LOGGER.debug(
                f"{self.endpoint}: setting reset task to trigger in "
                f"{seconds_until_reset}s."
            )
        else:
            _LOGGER.debug(f"{self.endpoint}: ratelimit reset task exists.")
