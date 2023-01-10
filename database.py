import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

SQLALCHEMY_DB_URL = os.getenv('SQLALCHEMY_DB_URL')
connection_args = {'sslmode': os.getenv('SSLMODE'),
                   'target_session_attrs': os.getenv('TARGET_SESSION_ATTRS')}
engine = create_engine(SQLALCHEMY_DB_URL, connect_args=connection_args)


def get_accounts_data(engine: Engine):
    """Return accounts data (dict) from db."""
    attribute_name = {3: "token", 4: "client_id", 5: "campaign_id"}
    accounts_data = {}  # {acc_id: {"client_id": ,"token": , "campaign_id": }, }
    query = """SELECT asd.account_id, asd.attribute_id, asd.attribute_value
                  FROM account_service_data asd
                 WHERE asd.attribute_id IN (3,4,5) AND
                     asd.account_id IN (
                        SELECT account_id
                          FROM (
                            SELECT *, row_number() OVER (
                                   PARTITION BY (attribute_id, attribute_value))
                              FROM account_service_data asd
                                JOIN account_list al ON asd.account_id = al.id
                             WHERE asd.attribute_id = 4 and al.status_1 = 'Active'
                               ) AS sq
                         WHERE row_number = 1)
                ORDER BY asd.account_id, asd.attribute_id;"""
    with engine.connect() as conn:
       rows = conn.execute(query)
    for acc_id, attribute_id, attribute_value in rows:
        if acc_id not in accounts_data:
            accounts_data[acc_id] = {}
        accounts_data[acc_id][attribute_name[attribute_id]] = attribute_value
    return accounts_data

