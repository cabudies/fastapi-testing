from typing import List, Optional
from fastapi import Query
from pydantic import BaseModel, Field, root_validator


class SearchCriteriaProducts(BaseModel):
    id: Optional[int]
    
    page_size: Optional[int] = Query(
        20, strict=True, ge=1, le=200, multiple_of=10
    )
    current_page: Optional[int] = Query(1, strict=True, ge=1)

    class Config:
        orm_mode = True


class CreateProducts(BaseModel):
    name: str
    description: str
    
    class Config:
        orm_mode = True
