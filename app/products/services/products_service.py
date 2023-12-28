from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from ..dto import request_model
from ..repository import products_repository


async def get_product_by_search_criteria(
    session: AsyncSession,
    search_criteria: request_model.SearchCriteriaProducts
):
    offset = (search_criteria.current_page - 1) * search_criteria.page_size
    limit = search_criteria.page_size

    products_list = await products_repository.get_product_by_search_criteria(
        offset=offset, limit=limit, session=session
    )

    total_products = len(products_list)
    
    last_page = True
    if total_products == limit:
        last_page = False

    final_obj = {
        "products_list": products_list, 
        "is_last_page": last_page
    }
    
    return final_obj


async def create_product(
    session: AsyncSession, 
    product_obj: request_model.CreateProducts
):
    product_with_name_already_exists = await products_repository.get_product_by_name(
        name=product_obj.name, session=session
    )
    if product_with_name_already_exists:
        raise HTTPException(
            status_code=400,
            detail="Product name already exists."
        )

    product = await products_repository.create_product(
        session=session, product_obj=product_obj
    )

    return product
