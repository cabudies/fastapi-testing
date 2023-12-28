from pydantic import BaseModel
from typing import List


class CartItem(BaseModel):
    sku: str
    quantity: float

    class Config:
        orm_mode = True


class CreateCart(BaseModel):
    customer_mobile_number: str
    cart_items: List[CartItem]
    
    class Config:
        orm_mode = True
