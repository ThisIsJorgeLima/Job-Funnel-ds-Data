
from typing import Optional
from datafunctions.retrieve.retrievefunctions import DataRetriever
from datafunctions.retrieve.retrievers import *
from datafunctions.utils import descendants


class Populator:
	def __init__(self):
		pass

	def retrieve_and_save_data(self, db_conn, retrievers: Optional[list[DataRetriever]] = None) -> None:
		"""
		Retrieves data from each DataRetriever provided, then saves it to the database.

		Arguments:
			retrievers (Optional[list[DataRetriever]], optional): Retrievers to call.
				Defaults to every retriever in datafunctions.retrieve.retrievers.
		"""

		data = self.retrieve_data(retrievers=retrievers)
		data_deduplicated = self.deduplicate_data(data)
		self.save_data(data_deduplicated)

	def retrieve_data(self, retrievers: Optional[list[DataRetriever]] = None) -> list[dict]:
		"""
		Retrieves data from each DataRetriever provided.

		Arguments:
			retrievers (Optional[list[DataRetriever]], optional): Retrievers to call.
				Defaults to every retriever in datafunctions.retrieve.retrievers.

		Returns:
			list: The results of `retriever.get_data()` for each retriever.
		"""

		if retrievers is None:
			retrievers = descendants(DataRetriever)

		data = []
		for retriever in retrievers:
			data.append(retriever.get_data())

		return (data)

	def deduplicate_data(self, data: list[dict]) -> list[dict]:
		"""
		Deduplicates a list of data dicts.

		Note that this *does not* deduplicate against data already in the DB;
			That functionality is provided in `self.save_data()`.

		Args:
			data (list[dict]): A list of data dicts, returned from `self.get_data()`.

		Returns:
			list[dict]: A deduplicated version of the input list.
		"""

		raise NotImplementedError

	def save_data(self, db_conn) -> None:
		"""
		This function will save the data to the database.

		Deduplication against the DB should occur here.
		"""

		raise NotImplementedError
