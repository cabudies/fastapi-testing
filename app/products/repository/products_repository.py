from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..dao import db_model
from ..dto import request_model


async def get_product_by_id(
    session: AsyncSession, id: int
):
    query_statement = select(
        db_model.Products
    ).where(db_model.Products.id == id)
    
    result = await session.execute(query_statement)
    product = result.scalars().first()
    
    return product


async def get_product_by_name(
    session: AsyncSession, name: str
):
    query_statement = select(
        db_model.Products
    ).where(db_model.Products.name.ilike(f"{name}"))
    
    result = await session.execute(query_statement)
    product = result.scalars().first()
    
    return product


async def get_product_by_search_criteria(
    session: AsyncSession, 
    offset: int,
    limit: int
):
    query_statement = select(
        db_model.Products
    ).offset(offset).limit(limit)
    
    result = await session.execute(query_statement)
    product = result.scalars().all()
    return product


async def create_product(
    session: AsyncSession, 
    product_obj: request_model.CreateProducts
):
    db_product = db_model.Products.from_orm(product_obj)
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product
