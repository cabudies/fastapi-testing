from fastapi import FastAPI
from starlette.middleware import Middleware
from fastapi_versioning import VersionedFastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

from db import disconnect_db
from products.controllers import products_controller
from variants.controllers import variants_controller
from price_list.controllers import price_list_controller
from carts.controllers import carts_controller


middlewares = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
    Middleware(GZipMiddleware, minimum_size=1000),
    Middleware(TrustedHostMiddleware, allowed_hosts=["*"]),
]


app = FastAPI(title="Products", middleware=middlewares)


app.include_router(
    products_controller.router, 
    prefix="/product", 
    tags=["products"]
)
app.include_router(
    variants_controller.router,
    prefix="/product/{product_id}/variant",
    tags=["variants"],
)
app.include_router(
    price_list_controller.router,
    prefix="/product/{product_id}/variant/{variant_id}/price-list",
    tags=["price-list"],
)
app.include_router(
    carts_controller.router,
    prefix="/cart",
    tags=["cart"],
)


app = VersionedFastAPI(
    app,
    version_format="{major}",
    prefix_format="/products-service/v{major}",
    middleware=middlewares,
)


@app.on_event("shutdown")
async def shutdown():
    await disconnect_db()
