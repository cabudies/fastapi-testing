from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi_versioning import version

from db import get_session
from ..dto import request_model
from ..services import price_list_service


router = APIRouter()


@router.get(
    "",
    status_code=200
)
@version(1)
async def fetch_price_list(
    product_id: str,
    variant_id: int,
    search_criteria: request_model.SearchCriteriaPriceList = Depends(),
    session: AsyncSession = Depends(get_session),
):
    setattr(search_criteria, "product_id", product_id)
    setattr(search_criteria, "variant_id", variant_id)

    response = await price_list_service.get_price_list(
        session=session, search_criteria=search_criteria
    )

    return response


@router.post(
    "",
    status_code=201
)
@version(1)
async def create_price_list(
    product_id: int,
    variant_id: int,
    price_list_model: request_model.CreatePriceList,
    session: AsyncSession = Depends(get_session),
):
    setattr(price_list_model, "product_variant_id", variant_id)

    price_list = await price_list_service.create_price_list(
        price_list_model=price_list_model, 
        product_id=product_id,
        session=session
    )
    
    return price_list
