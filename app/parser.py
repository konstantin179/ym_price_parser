import app.database as db
from app.database import engine
from app.yandex_market import YMClient
from concurrent.futures import ThreadPoolExecutor


def save_ym_prices(creds):
    client_id = creds[0]
    token = creds[1]
    campaign_id = creds[2]
    client = YMClient(client_id, token, campaign_id)
    client.get_prices()


def update_accounts_prices(client_id: str | int | list[int] = 'all'):
    accounts_data = db.get_accounts_data(engine, client_id=client_id)
    credentials = []
    for acc_data in accounts_data.values():
        credentials.append((acc_data['client_id'], acc_data['token'], acc_data['campaign_id']))
    # print(credentials)
    # print(len(credentials))

    # # One-thread
    # for cred in credentials:
    #     save_ym_prices(cred)

    # Multi-thread
    with ThreadPoolExecutor() as executor:
        executor.map(save_ym_prices, credentials)


if __name__ == '__main__':
    update_accounts_prices()
