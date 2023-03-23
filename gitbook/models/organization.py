from __future__ import annotations

from pydantic import BaseModel


class Organization(BaseModel):
    id: str
    title: str
