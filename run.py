import psycopg2

from decouple import config
from datafunctions.populate import Populator


if __name__ == "__main__":
	with psycopg2.connect(
			dbname=config("DB_DB"),
			user=config("DB_USER"),
			password=config("DB_PASSWORD"),
			host=config("DB_HOST"),
			port=config("DB_PORT")
	) as psql_conn:
		Populator().retrieve_and_save_data(psql_conn)

