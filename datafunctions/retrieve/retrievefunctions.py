
class DataRetriever:
	"""
	ABC for data retrieval classes.
	"""

	def get_data(self) -> dict:
		"""
		Method for getting data. Every DataRetriever *must* implement this.

		Raises:
			NotImplementedError: If the DataRetriever has not implemented this method.

		Returns:
			dict: The data retrieved.
		"""

		raise NotImplementedError(f'{self.__class__.__name__} has not implemented get_data.')

