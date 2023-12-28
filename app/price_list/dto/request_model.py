from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from fastapi.param_functions import Form
from fastapi import Query


class CreatePriceList(BaseModel):
    product_variant_id: Optional[int]
    min_quantity: int
    max_quantity: int
    price: float

    class Config:
        orm_mode = True

class CreatePriceListResponseModel(BaseModel):
    id: int
    product_variant_id: int
    price_type: str
    price: float
    channel: Optional[str]
    area: str
    area_type: str
    is_active: bool
    currency_id: int
    label: str
    special_price: float
    area_state: Optional[str]

    class Config:
        orm_mode = True


class UpdatePriceList(BaseModel):
    product_variant_id: Optional[int]
    currency_id: Optional[int]
    label: Optional[str]
    price: Optional[float]
    special_price: Optional[float]
    channel: Optional[str]
    area_type: Optional[str]
    area: Optional[str]
    area_state: Optional[str]
    is_active: Optional[bool]
    full_name: Optional[str]
    email: Optional[str]
    role: Optional[str]
    x_app_token: Optional[str]
    originated_by: Optional[str]

    class Config:
        orm_mode = True


class UpdatePriceListResponseModel(BaseModel):
    id: int
    product_variant_id: int
    currency_id: int
    price_type: str
    label: str
    price: float
    special_price: float
    channel: Optional[str]
    area_type: str
    area: str
    area_state: Optional[str]
    is_active: bool
    originated_by: Optional[str]

    class Config:
        orm_mode = True


class SearchCriteriaPriceList(BaseModel):
    product_id: Optional[str]
    variant_id: Optional[int]
    min_quantity: Optional[int]
    max_quantity: Optional[int]
    price: Optional[float]

    class Config:
        orm_mode = True
