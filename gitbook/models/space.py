from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Visibility(str, Enum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    SHARE_LINK = "share-link"
    VISITOR_AUTH = "visitor-auth"
    IN_COLLECTION = "in-collection"
    PRIVATE = "private"


class SpaceURLs(BaseModel):
    app: str


class Space(BaseModel):
    id: str
    title: str
    visibility: Visibility
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    urls: SpaceURLs
