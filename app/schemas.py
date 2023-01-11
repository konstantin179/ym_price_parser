from pydantic import BaseModel
from enum import Enum


class All(str, Enum):
    all = "all"


class RequestUpdatePrices(BaseModel):
    client_id: All | int | list[int]
