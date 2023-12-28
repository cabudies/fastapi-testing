from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi_versioning import version

from db import get_session
from ..dto import request_model
from ..services import products_service

router = APIRouter()


@router.get("", status_code=200)
@version(1)
async def get_product_by_search_criteria(
    search_criteria: request_model.SearchCriteriaProducts = Depends(),
    session: AsyncSession = Depends(get_session),
):
    response = await products_service.get_product_by_search_criteria(
        session=session, search_criteria=search_criteria
    )
    
    return response


@router.post("", status_code=201)
@version(1)
async def create_product(
    product_obj: request_model.CreateProducts,
    session: AsyncSession = Depends(get_session),
):
    product = await products_service.create_product(
        session=session, product_obj=product_obj
    )
    
    return product
