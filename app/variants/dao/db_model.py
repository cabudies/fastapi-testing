from typing import Optional
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import VARCHAR
from sqlmodel import Field, SQLModel, Relationship,DateTime
from datetime import datetime


class ProductsVariants(SQLModel, table=True):

    __tablename__ = "products_variants"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    product_id: Optional[int] = Field(default=None, foreign_key="products.id")
    sku: str = Field(sa_column=Column("sku", VARCHAR, unique=True))
    
    created_on: datetime = Field(default_factory=datetime.utcnow)
    modified_on: Optional[datetime] = Field(
        sa_column=Column(
            "modified_on",
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        )
    )
