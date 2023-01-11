from app import logger
from fastapi import APIRouter
from app.schemas import RequestUpdatePrices, All
from app.parser import update_accounts_prices

logger = logger.init_logger(__name__)

router = APIRouter()


@router.post("/yandex_market/update_prices", tags=['Yandex market'])
async def update_prices(client_ids: RequestUpdatePrices):
    """Update prices from Yandex Market for client.
    Send in request body client_id with id of one client or list of client ids or string "all" for all clients."""
    client_id = client_ids.client_id
    if client_id is All.all:
        update_accounts_prices()
    if isinstance(client_id, int):
        update_accounts_prices(client_id)
    if isinstance(client_id, list):
        update_accounts_prices(client_id)
    return {"message": "Prices were updated."}

