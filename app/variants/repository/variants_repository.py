from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dao import db_model
from ..dto import request_model
from products.dao import db_model as products_db_model


async def get_variants_list_based_on_product_id(
    session: AsyncSession, product_id: int
):
    query_statement = (
        select(
            db_model.ProductsVariants
        )
        .join(
            products_db_model.Products,
            db_model.ProductsVariants.product_id == products_db_model.Products.id
        )
        .where(
            db_model.ProductsVariants.product_id == product_id
        )
    )
    
    result = await session.execute(query_statement)
    variants_list = result.scalars().all()

    return variants_list


async def create_variant(
    session: AsyncSession, variant: request_model.CreateVariant
):
    db_new_variant = db_model.ProductsVariants.from_orm(variant)
    session.add(db_new_variant)
    await session.commit()
    await session.refresh(db_new_variant)
    return db_new_variant


async def get_variants_by_sku(
    session: AsyncSession,
    sku: str
):
    query_statement = select(db_model.ProductsVariants).where(
        db_model.ProductsVariants.sku.ilike(f"{sku}")
    )

    results = await session.execute(query_statement)
    variants = results.scalars().all()
    return variants


async def get_variants_by_sku_list(
    session: AsyncSession,
    sku_list: List[str]
):
    query_statement = select(db_model.ProductsVariants).where(
        db_model.ProductsVariants.sku.in_(sku_list)
    )

    results = await session.execute(query_statement)
    variants = results.scalars().all()
    return variants
