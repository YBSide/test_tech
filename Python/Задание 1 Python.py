import requests
import warnings
from datetime import datetime, timedelta
from sqlalchemy import create_engine, exc
warnings.simplefilter(action='ignore', category=exc.RemovedIn20Warning)


class EtlJob:

    def __init__(self):
        self.yesterday_date = None
        self.second_currency_rate = None
        self.user_table = None
        self.engine = None
        self.target_type = None
        self.out_json = None

    def get_exchange_json(self):

        with open('token.txt', 'r') as token_file:
            payload = {'access_key': token_file.read(),
                       'symbols': self.target_type
                       }

        self.yesterday_date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        r = requests.get(f'http://data.fixer.io/api/{self.yesterday_date}',
                         params=payload
                         )

        self.out_json = r.json()

    def get_exchange_rates(self):
        if self.out_json['success']:
            self.second_currency_rate = self.out_json['rates'][self.target_type]
        else:
            with open('error_log.txt', 'a') as log:
                log.write(str(self.out_json['error']) + '\n')
            raise Exception('ETL-error: see log file for more information.')

    def insert_row(self):
        with self.engine.connect() as conn:
            try:
                conn.execute(f"INSERT INTO {self.user_table} "
                             f"VALUES('{self.yesterday_date}', {self.second_currency_rate})")
                print('Row was inserted')
            except Exception:
                print('The row was not inserted')

    def all_etl(self,
                target_currency_type='USD',
                user_table='eur_usd_rate',
                engine_url='postgresql://root:root@localhost:5431/fixerio_db'):
        self.engine = create_engine(engine_url)
        self.target_type = target_currency_type
        self.user_table = user_table
        self.get_exchange_json()
        self.get_exchange_rates()
        self.insert_row()


if __name__ == '__main__':
    job = EtlJob()
    job.all_etl()
