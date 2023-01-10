import database as db
from database import engine
from yandex_market import YMClient
from concurrent.futures import ThreadPoolExecutor


def save_ym_prices(client_id, token, campaign_id):
    client = YMClient(client_id, token, campaign_id)
    client.get_prices()


if __name__ == '__main__':
    accounts_data = db.get_accounts_data(engine)
    print(accounts_data)
    credentials = []
    for acc_data in accounts_data.values():
        credentials.append((acc_data['client_id'], acc_data['token'], acc_data['campaign_id']))

    for cred in credentials:
        save_ym_prices(*cred)

    # with ThreadPoolExecutor() as executor:
    #     executor.map(save_ym_prices, credentials)

