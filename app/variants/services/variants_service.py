from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from ..dto import request_model
from ..repository import variants_repository
from products.repository import products_repository


async def get_variants_list(
    session: AsyncSession, product_id: int
):
    variants = await variants_repository.get_variants_list_based_on_product_id(
        session=session, product_id=product_id
    )

    variants_list = list(map(lambda x: jsonable_encoder(x), variants))
    
    return variants_list


async def create_variant(
    session: AsyncSession, 
    variant_obj: request_model.CreateVariant
):
    db_product = await products_repository.get_product_by_id(
        id=variant_obj.product_id, session=session
    )

    if db_product is None:
        raise HTTPException(
            status_code=400, 
            detail="Product does not exist."
        )

    setattr(variant_obj, "product_id", db_product.id)
    
    check_if_variant_exists = await variants_repository.get_variants_by_sku(
        session=session, sku=variant_obj.sku
    )

    if len(check_if_variant_exists) > 0:
        raise HTTPException(
            status_code=400, 
            detail="SKU already mapped with other product."
        )

    variant = await variants_repository.create_variant(
        session=session, variant=variant_obj
    )
    if variant is None:
        raise HTTPException(
            status_code=400,
            detail="Variant creation failed."
        )

    return variant
