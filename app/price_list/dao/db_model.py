from typing import Optional
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime
from datetime import datetime
from sqlalchemy import UniqueConstraint


class PriceList(SQLModel, table=True):

    __tablename__ = "price_list"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    product_variant_id: Optional[int] = Field(default=None, foreign_key="products_variants.id")
    min_quantity: int
    max_quantity: int
    price: float

    created_on: datetime = Field(default_factory=datetime.utcnow)
    modified_on: Optional[datetime] = Field(
        sa_column=Column(
            "modified_on",
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        )
    )

    __table_args__ = (
        UniqueConstraint(
            "min_quantity",
            "max_quantity",
            "product_variant_id",
            name="special_price_based_on_min_and_max_quantity",
        ),
    )

    class Config:
        use_enum_values = True
