
from typing import Optional


class TopicModel:
	"""
	ABC for topic modeling classes.
	"""

	def populate_database(self, db_connection, **kwargs) -> None:
		"""
		Method for getting data and storing it to a database.
		Every TopicModel *must* implement this.

		Args:
			db_connection: Connection to the database.

		Raises:
			NotImplementedError: If the TopicModel has not implemented this method.
		"""

		raise NotImplementedError(f'{self.__class__.__name__} has not implemented populate_database.')

	def __enter__(self):
		raise NotImplementedError(f'{self.__class__.__name__} has not implemented __enter__.')

	def __exit__(self, exc_type, exc_value, tb):
		raise NotImplementedError(f'{self.__class__.__name__} has not implemented __exit__.')
