from __future__ import annotations

import aiohttp
from pydantic import BaseModel, Field

from gitbook.abc.model import Model


class User(Model, BaseModel):
    id: str
    display_name: str = Field(alias="displayName")
    email: str
    photo_url: str = Field(alias="photoURL")

    @classmethod
    async def _from_response(cls, response: aiohttp.ClientResponse) -> User:
        data: dict[str, object] = await response.json()
        return cls(**data)
