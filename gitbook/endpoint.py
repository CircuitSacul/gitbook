from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

import aiohttp
from pydantic import BaseModel

if TYPE_CHECKING:
    from gitbook.client import Client


_RETURN = TypeVar("_RETURN", bound="BaseModel")
_LOGGER = logging.getLogger("gitbook")


class BaseEndpoint(Generic[_RETURN]):
    API_VERSION = "v1"

    def __init__(
        self,
        method: str,
        path: str,
        model: type[_RETURN],
        params: tuple[str] | None = None,
    ) -> None:
        self.params = params or ()
        self.method = method
        self.path = f"/{self.API_VERSION}/{path}"
        self.model = model
        self.ratelimit = RateLimit(self)

    def _build_path(
        self, /, **params: object
    ) -> tuple[str, dict[str, object]]:
        query_params: dict[str, object] = {}
        for key in self.params:
            if value := params.pop(key):
                query_params[key] = value

        return self.path.format(**params), query_params

    def __str__(self) -> str:
        return f"Endpoint({self.method}, {self.path})"

    def __repr__(self) -> str:
        return str(self)


class SingleEndpoint(BaseEndpoint[_RETURN], Generic[_RETURN]):
    async def execute(self, client: Client, /, **params: object) -> _RETURN:
        await self.ratelimit.acquire()
        path, params = self._build_path(**params)
        response = await client._session.request(
            self.method, path, params=params
        )
        self.ratelimit.parse_ratelimit(response)
        response.raise_for_status()
        return self.model(**await response.json())


class PaginatedEndpoint(BaseEndpoint[_RETURN], Generic[_RETURN]):
    def __init__(
        self,
        method: str,
        path: str,
        model: type[_RETURN],
        params: tuple[str] | None = None,
    ) -> None:
        super().__init__(method, path, model, params)

    def execute(
        self, client: Client, /, **params: dict[str, object]
    ) -> Paginator[_RETURN]:
        return Paginator(self, self._build_path(**params), client)


class Paginator(Generic[_RETURN]):
    def __init__(
        self,
        endpoint: PaginatedEndpoint[_RETURN],
        path: tuple[str, dict[str, object]],
        client: Client,
    ) -> None:
        self.endpoint = endpoint
        self.path = path
        self.client = client

    async def fetch_page(
        self, *, limit: int | None = None, page: str | None = None
    ) -> PaginatedResult[_RETURN]:
        await self.endpoint.ratelimit.acquire()
        params = self.path[1].copy()
        if limit is not None:
            params["limit"] = limit
        if page is not None:
            params["page"] = page
        response = await self.client._session.request(
            self.endpoint.method, self.path[0], params=params
        )
        self.endpoint.ratelimit.parse_ratelimit(response)
        response.raise_for_status()
        data: dict[str, Any] = await response.json()
        next_page = prev_page = None
        if d := data.get("next"):
            next_page = d["page"]
        if d := data.get("previous"):
            prev_page = d["page"]
        return PaginatedResult(
            _limit=limit,
            _paginator=self,
            next_page=next_page,
            prev_page=prev_page,
            items=[self.endpoint.model(**d) for d in data["items"]],
        )


class PaginatedResult(BaseModel, Generic[_RETURN]):
    _limit: Optional[int]
    _paginator: Paginator[_RETURN]
    items: list[_RETURN]
    next_page: Optional[str]
    prev_page: Optional[str]

    async def next(self) -> PaginatedResult[_RETURN] | None:
        if self.next_page is None:
            return None
        return await self._paginator.fetch_page(
            limit=self._limit, page=self.next_page
        )

    async def prev(self) -> PaginatedResult[_RETURN] | None:
        if self.prev_page is None:
            return None
        return await self._paginator.fetch_page(
            limit=self._limit, page=self.prev_page
        )


class RateLimit:
    def __init__(self, endpoint: BaseEndpoint[_RETURN]) -> None:
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
