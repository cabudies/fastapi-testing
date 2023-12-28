from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from ..dto import request_model
from variants.repository import variants_repository
from price_list.repository import price_list_repository


async def create_cart(
    session: AsyncSession, 
    cart_obj: request_model.CreateCart
):
    final_total_value = 0

    variants_sku_list = list(map(lambda x: str(x.sku), cart_obj.cart_items))

    variants_list_from_db = await variants_repository.get_variants_by_sku_list(
        session=session, sku_list=variants_sku_list
    )

    if len(variants_list_from_db) != len(variants_sku_list):
        raise HTTPException(
            status_code=400, 
            detail="Few of the Variant's are invalid."
        )

    for variant in cart_obj.cart_items:
        price_list_based_on_sku = await price_list_repository.get_price_list_by_sku_and_order_quantity(
            session=session, 
            sku=variant.sku, 
            quantity=variant.quantity
        )

        if price_list_based_on_sku is None:
            raise HTTPException(
                status_code=400, 
                detail="There's no price available for the given product."
            )
        
        final_total_value = final_total_value + (price_list_based_on_sku.price * variant.quantity)
    
    return JSONResponse(
        status_code=200,
        content={
            "message": f"Your cart's total amount is - $ {final_total_value}."
        }
    )
