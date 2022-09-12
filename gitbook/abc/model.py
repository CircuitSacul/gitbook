from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

import aiohttp

_SELF = TypeVar("_SELF", bound="Model")


class Model(ABC):
    @classmethod
    @abstractmethod
    async def _from_response(
        cls: type[_SELF], response: aiohttp.ClientResponse
    ) -> _SELF:
        ...
