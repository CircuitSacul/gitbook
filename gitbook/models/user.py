from __future__ import annotations

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    display_name: str = Field(alias="displayName")
    email: str
    photo_url: str = Field(alias="photoURL")
