
import logging

from typing import Optional, Type, List
from datafunctions.retrieve.retrievefunctions import DataRetriever
from datafunctions.retrieve import retrievers
from datafunctions.utils import descendants

POPULATE_LOG = logging.getLogger(__name__)


class Populator:
	def __init__(self):
		POPULATE_LOG.info('Populator instantiated.')

	def retrieve_and_save_data(self, db_conn, retriever_classes: Optional[List[Type[DataRetriever]]] = None) -> None:
		"""
		Retrieves data from each DataRetriever provided, then saves it to the database.

		Arguments:
			retriever_class (Optional[List[Type[DataRetriever]]], optional): Classes of retriever_class to call.
				Defaults to every retriever_class in datafunctions.retrieve.retriever_class.
		"""

		if retriever_classes is None:
			POPULATE_LOG.info('retriever_classes not passed, auto-populating.')
			retriever_classes = descendants(DataRetriever)
		POPULATE_LOG.info(f'retriever_classes: {retriever_classes}')
		retriever_classes_store = []
		retriever_classes_get = []
		for retriever_class in retriever_classes:
			# If the retriever_class class has a get_data method, we'll use that
			if getattr(retriever_class, "get_data", None) not in [None, DataRetriever.get_data]:
				retriever_classes_get.append(retriever_class)
			# Otherwise, we'll use the get_and_store_data method
			else:
				retriever_classes_store.append(retriever_class)
		POPULATE_LOG.info(f'retriever_classes_get: {retriever_classes_get}')
		POPULATE_LOG.info(f'retriever_classes_store: {retriever_classes_store}')
		if len(retriever_classes_get):
			data = self.retrieve_data(retriever_classes_get)
			data_deduplicated = self.deduplicate_data(data)
			self.save_data(db_conn, data_deduplicated)
		if len(retriever_classes_store):
			self.get_and_store_data(db_conn, retriever_classes_store)

	def get_and_store_data(self, db_conn, retriever_class: List[Type[DataRetriever]]) -> None:
		"""
		Retrieves data from each DataRetriever provided, and stores it in the database.

		Arguments:
			retriever_class (List[Type[DataRetriever]]): retriever_class classes to call.
		"""

		POPULATE_LOG.info('get_and_store_data called.')
		for retriever_class in retriever_class:
			POPULATE_LOG.info(f'Instantiating retriever class: {retriever_class}')
			with retriever_class() as r:
				POPULATE_LOG.info(f'Calling get_and_store_data on instance: {r}')
				r.get_and_store_data(db_conn)
				POPULATE_LOG.info(f'Done get_and_store_data on instance: {r}')
		POPULATE_LOG.info('get_and_store_data done.')

	def retrieve_data(self, retriever_class: List[Type[DataRetriever]]) -> List[dict]:
		"""
		Retrieves data from each DataRetriever provided.

		Arguments:
			retriever_class (List[Type[DataRetriever]]): retriever_class classes to call.

		Returns:
			list: The results of `retriever_class.get_data()` for each retriever_class.
		"""

		data = []
		for retriever_class in retriever_class:
			with retriever_class() as r:
				data.append(r.get_data())

		return (data)

	def deduplicate_data(self, data: List[dict]) -> List[dict]:
		"""
		Deduplicates a list of data dicts.

		Note that this *does not* deduplicate against data already in the DB;
			That functionality is provided in `self.save_data()`.

		Args:
			data (List[dict]): A list of data dicts, returned from `self.get_data()`.

		Returns:
			List[dict]: A deduplicated version of the input list.
		"""

		raise NotImplementedError

	def save_data(self, db_conn, data: List[dict]) -> None:
		"""
		This function will save the data to the database.

		Deduplication against the DB should occur here.
		"""

		raise NotImplementedError
