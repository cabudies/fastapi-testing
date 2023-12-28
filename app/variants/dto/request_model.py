from typing import Optional
from pydantic import BaseModel


class CreateVariant(BaseModel):
    product_id: Optional[int]
    sku: str
    
    class Config:
        orm_mode = True
