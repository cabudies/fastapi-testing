from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi_versioning import version

from db import get_session
from ..dto import request_model
from ..services import carts_service


router = APIRouter()


@router.post("/generate-price", status_code=201)
@version(1)
async def create_cart(
    cart_obj: request_model.CreateCart,
    session: AsyncSession = Depends(get_session),
):
    cart = await carts_service.create_cart(
        session=session, cart_obj=cart_obj
    )

    return cart
