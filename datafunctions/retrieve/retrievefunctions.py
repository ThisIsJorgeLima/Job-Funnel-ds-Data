
from typing import Optional


class DataRetriever:
	"""
	ABC for data retrieval classes.
	"""

	def get_and_store_data(self, db_connection, db_callback: Optional[callable] = None, **kwargs) -> None:
		"""
		Method for getting data and storing it to a database.
		Every DataRetriever *must* implement either this or get_data.
		Note that the DataRetriever is expected to perform deduplication if this method is implemented.

		Args:
			db_connection: Connection to the database.
			db_callback (callable, optional): Callback to database addition function.

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

	def __enter__(self):
		raise NotImplementedError(f'{self.__class__.__name__} has not implemented __enter__.')

	def __exit__(self, exc_type, exc_value, tb):
		raise NotImplementedError(f'{self.__class__.__name__} has not implemented __exit__.')
