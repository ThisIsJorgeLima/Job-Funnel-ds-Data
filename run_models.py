import psycopg2
import logging

from decouple import config
from datafunctions.populate import Populator
from datafunctions.log.log import startLog, getLogFile


if __name__ == "__main__":
	ROOT_LOG = startLog(getLogFile(__file__))
	RUN_LOG = logging.getLogger(__name__)
	RUN_LOG.info('Establishing database connection...')
	try:
		with psycopg2.connect(
				dbname=config("DB_DB"),
				user=config("DB_USER"),
				password=config("DB_PASSWORD"),
				host=config("DB_HOST"),
				port=config("DB_PORT")
		) as psql_conn:
			RUN_LOG.info('Running models...')
			Populator().model_and_save_topics(psql_conn)
	except Exception as e:
		RUN_LOG.warning(f'Failure while connecting or modeling: {e}')
		RUN_LOG.warning(e, exc_info=True)

	RUN_LOG.info('Done, exiting.')

