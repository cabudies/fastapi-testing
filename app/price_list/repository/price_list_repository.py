import datetime
from typing import List
from sqlalchemy import between, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic.main import BaseModel
from sqlalchemy.sql.elements import and_

from ..dao import db_model
from ..dto import request_model
from variants.dao import db_model as variants_db_model


async def create_price_list(
    session: AsyncSession, price_list_model: db_model.PriceList
):
    db_price_list = db_model.PriceList.from_orm(price_list_model)
    session.add(db_price_list)
    await session.commit()
    await session.refresh(db_price_list)
    return db_price_list


async def get_price_list(
    session: AsyncSession, query_statement: BaseModel
):
    execute_price_list_query = await session.execute(query_statement)
    response = execute_price_list_query.scalars().all()
    return response


async def get_price_list_by_sku_and_order_quantity(
    session: AsyncSession, 
    sku: str,
    quantity: int
):
    query_statement = select(
        db_model.PriceList
    ).join(
        variants_db_model.ProductsVariants,
        db_model.PriceList.product_variant_id == variants_db_model.ProductsVariants.id
    ).where(
        and_(
            variants_db_model.ProductsVariants.sku.ilike(f"{sku}"),
            between(
                quantity,
                db_model.PriceList.min_quantity,
                db_model.PriceList.max_quantity
            )
        )
    )

    execute_query = await session.execute(query_statement)
    response = execute_query.scalars().first()
    return response


async def get_price_list_by_product_variant_id_and_order_quantity(
    session: AsyncSession, 
    product_variant_id: int,
    min_quantity: int,
    max_quantity: int
):
    query_statement = select(
        db_model.PriceList
    ).where(
        and_(
            db_model.PriceList.product_variant_id == product_variant_id,
            or_(
                between(
                    min_quantity,
                    db_model.PriceList.min_quantity,
                    db_model.PriceList.max_quantity
                ),
                between(
                    max_quantity,
                    db_model.PriceList.min_quantity,
                    db_model.PriceList.max_quantity
                )
            )
        )
    )

    execute_query = await session.execute(query_statement)
    response = execute_query.scalars().first()
    return response
