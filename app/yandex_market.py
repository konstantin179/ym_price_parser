import time
import pandas as pd
import requests
from app import logger

logger = logger.init_logger("yandex_market")


class YMClient:
    """Class represents a client to work with yandex market API."""

    def __init__(self, client_id, token, campaign_id):
        self.url = "https://api.partner.market.yandex.ru/v2"
        self.client_id = client_id
        self.token = token
        self.campaign_id = campaign_id
        self.headers = {'Authorization': f'OAuth oauth_token={token}, oauth_client_id={client_id}'}
        self.vat_values = {2: 0.1, 5: 0.0, 6: 0.0, 7: 0.2, None: 0.0}

    def get_prices(self):
        offer_mapping_entries = self.get_offer_mapping_entries()
        data = []
        for offer_mapping_entry in offer_mapping_entries:
            row = {'product_id': offer_mapping_entry['mapping']['marketSku'],
                   'offer_id': offer_mapping_entry['offer']['shopSku']}
            data.append(row)
        if not data:
            logger.error(f"Client_id: {self.client_id} has no data.")
            return None
        # Create df with product and offer ids.
        df = pd.DataFrame.from_records(data)
        # Delete duplicates
        df.drop_duplicates(subset=['product_id'], inplace=True)
        # Add prices and vat to df.
        offers = self.get_offers()
        for offer in offers:
            product_id = offer.get('marketSku')
            price_dict = offer.get('price')
            if not (product_id and price_dict):
                continue
            price = price_dict.get('value')
            if price is not None:
                df.loc[df['product_id'] == product_id, 'price'] = price
            old_price = price_dict.get('discountBase')
            if old_price is not None:
                df.loc[df['product_id'] == product_id, 'old_price'] = old_price
            vat = price_dict.get('vat')
            vat = self.vat_values[vat]
            df.loc[df['product_id'] == product_id, 'vat'] = vat

        # Add recommended_price to df.
        counter = 0
        # Max 100 000 products within an hour.
        for hundred_thousand_skus in series_chunks(df['product_id'], 100_000):
            if counter > 0:
                time.sleep(3600)  # 1-hour sleep
            # Max 1000 products in one request.
            for thousand_skus in series_chunks(hundred_thousand_skus, 1000):
                market_skus = {'offers': []}
                for product_id in thousand_skus:
                    market_skus['offers'].append({'marketSku': product_id})
                price_suggestions = self.get_price_suggestions(market_skus)
                for offer in price_suggestions:
                    product_id = offer.get('marketSku')
                    suggestions = offer.get('priceSuggestion')
                    if not (product_id and suggestions):
                        continue
                    for suggestion in suggestions:
                        if suggestion.get('type') == 'BUYBOX':
                            recommended_price = suggestion.get('price')
                            if recommended_price is not None:
                                df.loc[df['product_id'] == product_id, 'recommended_price'] = recommended_price
            counter += 1
        # Add tariffs to df.
        # Max 500 products in one request.
        for offer_ids_500 in series_chunks(df['offer_id'], 500):
            shop_skus = {'shopSkus': []}
            for offer_id in offer_ids_500:
                shop_skus['shopSkus'].append(offer_id)
            sku_tariffs = self.get_tariffs(shop_skus)
            for sku in sku_tariffs:
                offer_id = sku.get('shopSku')
                product_id = sku.get('marketSku')
                tariffs = sku.get('tariffs')
                if not (offer_id and product_id and tariffs):
                    continue
                for tariff in tariffs:
                    percent = tariff.get('percent')
                    amount = tariff.get('amount')
                    if tariff.get('type') == 'FEE':
                        if percent is not None:
                            df.loc[(df['product_id'] == product_id) & (df['offer_id'] == offer_id),
                                   'sales_percent'] = percent
                    if tariff.get('type') == 'FULFILLMENT':
                        if amount is not None:
                            df.loc[(df['product_id'] == product_id) & (df['offer_id'] == offer_id),
                                   'fbo_fulfillment_amount'] = amount
                    if tariff.get('type') == 'AGENCY_COMMISSION':
                        if percent is not None:
                            df.loc[(df['product_id'] == product_id) & (df['offer_id'] == offer_id),
                                   'equering_cost'] = percent
        # Add api_id, shop_id, date to df.
        df['api_id'] = self.campaign_id
        df['shop_id'] = 2
        df['date'] = time.strftime('%Y-%m-%d', time.localtime())
        self.send_to_db(df)

    @staticmethod
    def send_to_db(df):
        """Send data to 'JSON to DB API' to save it in price_table."""
        # Dropping nan and converting to list of dicts
        data = [row.dropna().to_dict() for i, row in df.iterrows()]
        json_to_db_url = "https://apps1.ecomru.ru:4439/db/price_table"
        # json_to_db_url = "http://127.0.0.1:8000/db/price_table"
        try:
            response = requests.post(json_to_db_url, json=data)
            response.raise_for_status()
            logger.info("Data was sent.")
        except requests.exceptions.RequestException as e:
            logger.error(repr(e))

    def get_tariffs(self, shop_skus):
        sku_tariffs = []
        try:
            response = requests.post(self.url + f"/campaigns/{self.campaign_id}/stats/skus.json",
                                     headers=self.headers, json=shop_skus)
            response.raise_for_status()
            data = response.json()
            if data['status'] == 'ERROR':
                logger.error(repr(data['errors']))
                return sku_tariffs
            result = data['result']
            sku_tariffs.extend(result['shopSkus'])
        except requests.exceptions.RequestException as e:
            logger.error(repr(e))
        return sku_tariffs

    def get_price_suggestions(self, market_skus):
        price_suggestions = []
        try:
            response = requests.post(self.url + f"/campaigns/{self.campaign_id}/offer-prices/suggestions.json",
                                     headers=self.headers, json=market_skus)
            response.raise_for_status()
            data = response.json()
            if data['status'] == 'ERROR':
                logger.error(repr(data['errors']))
                return price_suggestions
            result = data['result']
            price_suggestions.extend(result['offers'])
        except requests.exceptions.RequestException as e:
            logger.error(repr(e))
        return price_suggestions

    def get_offer_mapping_entries(self):
        params = {'page_token': '',
                  'status': 'READY',
                  'limit': 100}
        offer_mapping_entries = []
        while True:
            try:
                response = requests.get(self.url + f"/campaigns/{self.campaign_id}/offer-mapping-entries.json",
                                        headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                if data['status'] == 'ERROR':
                    logger.error(repr(data['errors']))
                    break
                result = data['result']
                offer_mapping_entries.extend(result['offerMappingEntries'])
                next_page_token = result['paging'].get('nextPageToken')
                if not next_page_token:
                    break
                params['page_token'] = next_page_token
            except (UnicodeEncodeError, requests.exceptions.RequestException) as e:
                logger.error(repr(e))
                break
        return offer_mapping_entries

    def get_offers(self):
        params = {'page_token': '',
                  'limit': 500}
        offers = []
        while True:
            try:
                response = requests.get(self.url + f"/campaigns/{self.campaign_id}/offer-prices.json",
                                        headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                if data['status'] == 'ERROR':
                    logger.error(repr(data['errors']))
                    break
                result = data['result']
                offers.extend(result['offers'])
                next_page_token = result['paging'].get('nextPageToken')
                if not next_page_token:
                    break
                params['page_token'] = next_page_token
            except requests.exceptions.RequestException as e:
                logger.error(repr(e))
                break
        return offers


def series_chunks(series, n):
    """Yield successive n-sized chunks from pd series."""
    for i in range(0, len(series), n):
        yield series.iloc[i:i + n]
