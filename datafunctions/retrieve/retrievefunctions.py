
from typing import Optional


class DataRetriever:
	"""
	ABC for data retrieval classes.
	"""

	def get_and_store_data(self, db_callback: callable, db_connection) -> None:
		"""
		Method for getting data and storing it to a database.
		Every DataRetriever *must* implement either this or get_data.
		Note that the DataRetriever is expected to perform deduplication if this method is implemented.

		Args:
			db_callback (callable): Callback to database addition function.
			db_connection: Connection to the database. Should be used for deduplication only.

		Raises:
			NotImplementedError: If the DataRetriever has not implemented this method.
		"""

		raise NotImplementedError(f'{self.__class__.__name__} has not implemented get_and_store_data.')

	def get_data(self) -> dict:
		"""
		Method for getting data.
		Every DataRetriever *must* implement either this or get_and_store_data.

		Raises:
			NotImplementedError: If the DataRetriever has not implemented this method.

		Returns:
			dict: The data retrieved.
		"""

		raise NotImplementedError(f'{self.__class__.__name__} has not implemented get_data.')

