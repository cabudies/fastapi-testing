from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi_versioning import version

from db import get_session
from ..dto import request_model
from ..services import variants_service


router = APIRouter()


@router.get("", status_code=200)
@version(1)
async def get_variants_list(
    product_id: int,
    session: AsyncSession = Depends(get_session),
):
    response = await variants_service.get_variants_list(
        session=session, 
        product_id=product_id
    )
    return response


@router.post("", status_code=201)
@version(1)
async def create_variant(
    product_id: int,
    variant_obj: request_model.CreateVariant,
    session: AsyncSession = Depends(get_session),
):
    setattr(variant_obj, "product_id", product_id)
    
    variant = await variants_service.create_variant(
        session=session, variant_obj=variant_obj
    )

    return variant
