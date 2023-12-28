from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dao import db_model
from ..dto import request_model
from ..repository import price_list_repository

from products.repository import products_repository
from products.dao import db_model as db_product
from products.services import products_service


async def create_price_list(
    price_list_model: request_model.CreatePriceList, 
    product_id: int, 
    session: AsyncSession
):
    product_details = await products_repository.get_product_by_id(
        id=product_id, session=session
    )
    if product_details is None:
        raise HTTPException(
            status_code=400,
            detail="Product slug or Product ID not found."
        )
    product_id = product_details.id

    price_list_based_on_sku = await price_list_repository.get_price_list_by_product_variant_id_and_order_quantity(
        session=session, 
        product_variant_id=price_list_model.product_variant_id, 
        min_quantity=price_list_model.min_quantity,
        max_quantity=price_list_model.max_quantity
    )

    if price_list_based_on_sku:
        raise HTTPException(
            status_code=400, 
            detail="Price already exists for the given range for this variant."
        )

    db_new_price_list = await price_list_repository.create_price_list(
        session=session, price_list_model=price_list_model
    )
    return db_new_price_list


async def get_price_list(
    session: AsyncSession,
    search_criteria: request_model.SearchCriteriaPriceList,
):
    query_statement = await generate_price_list_query_statement(
        search_criteria=search_criteria, session=session
    )

    db_price_list = await price_list_repository.get_price_list(
        session=session, query_statement=query_statement
    )

    return {
        "price_list": db_price_list
    }


async def generate_price_list_query_statement(
    session: AsyncSession,
    search_criteria: request_model.SearchCriteriaPriceList,
):
    query_statement = select(db_model.PriceList).where(
        db_model.PriceList.product_variant_id == search_criteria.variant_id,
    )

    if search_criteria.min_quantity:
        query_statement = query_statement.where(
            db_model.PriceList.min_quantity >= search_criteria.min_quantity
        )
    if search_criteria.max_quantity:
        query_statement = query_statement.where(
            db_model.PriceList.max_quantity <= search_criteria.max_quantity
        )
    
    return query_statement
