import logging
import gensim
import pickle
import numpy

from os.path import dirname, join
from typing import Dict, List
from sklearn.neighbors import KNeighborsClassifier

from datafunctions.model.modelfunctions import TopicModel

LDA_LOG = logging.getLogger(__name__)


class LDA17Model(TopicModel):
	FILES_DIRECTORY = 'lda17_files'

	def __init__(self, db_conn):
		LDA_LOG.info('Loading lda17 model...')
		self.model = gensim.models.LdaModel.load(
			join(dirname(__file__), self.FILES_DIRECTORY, 'model')
		)
		self.id2word = gensim.corpora.Dictionary.load(
			join(dirname(__file__), self.FILES_DIRECTORY, 'id2word')
		)
		self.nearest_neighbors = self.open_or_create_nn(db_conn)
		LDA_LOG.info('Done loading model.')

	def open_or_create_nn(self, db_conn):
		try:
			LDA_LOG.info('Trying to open NearestNeighbors from file...')
			with open(
					join(dirname(__file__), self.FILES_DIRECTORY, 'nearest_neighbors'),
					'rb',
			) as f:
				return pickle.load(f)
		except Exception as e:
			LDA_LOG.info(f'Unable to open NearestNeighbors from file: {e}')
			LDA_LOG.info('Attempting to recreate NearestNeighbors...')
			return self.create_nn(db_conn)

	def create_nn(self, db_conn):
		LDA_LOG.info('Creating NearestNeighbors...')

		LDA_LOG.info('Resetting lda17_topics.in_nn flag in database...')
		clear_query = '''
			UPDATE lda17_topics
			SET in_nn = FALSE;
		'''
		curr = db_conn.cursor()
		curr.execute(clear_query)
		curr.close()
		db_conn.commit()
		LDA_LOG.info('lda17_topics.in_nn flag reset to FALSE.')

		nearest_neighbors = KNeighborsClassifier(n_neighbors=20)
		LDA_LOG.info('Created empty KNeighborsClassifier.')

		return nearest_neighbors

	def train_nn(self, new_X, new_y):
		if hasattr(self.nearest_neighbors, '_fit_X'):
			old_X = self.nearest_neighbors._fit_X
			old_y = self.nearest_neighbors._y
			combined_X = numpy.vstack([old_X, new_X])
			combined_y = numpy.hstack([old_y, new_y])
			LDA_LOG.info(f'''
				old_X.shape: {old_X.shape}
				old_y.shape: {old_y.shape}
				new_X.shape: {new_X.shape}
				new_y.shape: {new_y.shape}
				combined_X.shape: {combined_X.shape}
				combined_y.shape: {combined_y.shape}
			''')
		else:
			combined_X = new_X
			combined_y = new_y
		self.nearest_neighbors.fit(combined_X, combined_y)

	def save_nn(self):
		LDA_LOG.info('Saving NearestNeighbors...')
		with open(
				join(dirname(__file__), self.FILES_DIRECTORY, 'nearest_neighbors'),
				'wb',
		) as f:
			return pickle.dump(self.nearest_neighbors, f)
		LDA_LOG.info('NearestNeighbors saved.')

	def save_and_flag_nn(self, db_conn, updated_job_ids):
		LDA_LOG.info('Saving and flagging NearestNeighbors...')
		flag_query = '''
			UPDATE lda17_topics
			SET in_nn = TRUE
			WHERE job_id IN %(job_ids)s;
		'''

		params = {
			'job_ids': tuple(updated_job_ids),  # This must be a tuple for psycopg2
		}

		try:
			LDA_LOG.info('Setting isolation level to READ COMMITTED')
			db_conn.set_isolation_level(1)
			LDA_LOG.info('Starting transactions...')
			curr = db_conn.cursor()

			# Flag the updated job ids as being in NearestNeighbors
			curr.execute(
				flag_query,
				params,
			)

			curr.close()

			self.save_nn()

			LDA_LOG.info('Committing changes...')
			db_conn.commit()
			LDA_LOG.info('Added result to database.')

		except Exception as e:
			LDA_LOG.warn(f'Exception {type(e)} while saving lda17 scores: {e}')
			LDA_LOG.warn(e, exc_info=True)
			curr.close()

	def populate_database(self, db_conn, per_iter_limit=500):
		LDA_LOG.info('Populating database with lda17 scores...')
		while True:
			job_descriptions = self.get_missing_descriptions(db_conn, limit=per_iter_limit)
			LDA_LOG.info(f'Got {len(job_descriptions)} descriptions without lda17 scores...')
			if len(job_descriptions) == 0:
				break

			job_scores = self.get_topic_scores(job_descriptions)
			self.save_scores(db_conn, job_scores)
		LDA_LOG.info('Done populating database with lda17 scores.')

		self.update_nn(db_conn)

	def update_nn(self, db_conn):
		LDA_LOG.info('Updating NearestNeighbors...')
		while True:
			missing = self.get_missing_from_nn(db_conn)
			if len(missing) == 0:
				break

			job_ids, topics = zip(*missing.items())
			self.train_nn(numpy.array(topics), numpy.array(job_ids))

			try:
				self.save_and_flag_nn(db_conn, job_ids)
			except Exception as e:
				LDA_LOG.warn(f'Exception {type(e)} while saving and flagging NearestNeighbors: {e}')
				LDA_LOG.warn(e, exc_info=True)

		LDA_LOG.info('Done updating NearestNeighbors.')

	def get_missing_from_nn(self, db_conn, limit=10000) -> Dict[int, List[float]]:
		'''
		Finds up to `limit` scored jobs that have not been added to the NearestNeighbors model.

		Args:
			db_conn: Database connection.
			limit (int, optional): Maximum number of jobs to retrieve. Defaults to 500.

		Returns:
			Dict[int, List[float]]: Dict of job_id: [lda0, lda1, ..., lda16]
		'''

		LDA_LOG.info('Getting lda17 scores that haven\'t been added to NearestNeighbors...')

		nn_query = '''
			SELECT job_id, lda0, lda1, lda2, lda3, lda4, lda5, lda6, lda7, lda8, lda9, lda10, lda11, lda12, lda13, lda14, lda15, lda16
			FROM lda17_topics
			WHERE in_nn = FALSE
			LIMIT %(limit)s;
		'''

		results = {}

		try:
			curr = db_conn.cursor()

			# Get the scores that aren't in NearestNeighbors
			curr.execute(
				nn_query,
				{
					'limit': limit,
				}
			)
			qr = curr.fetchall()

			for result in qr:
				results[result[0]] = result[1:]

		except Exception as e:
			LDA_LOG.warn(f'Exception {type(e)} while getting scores not in NearestNeighbors: {e}')
			LDA_LOG.warn(e, exc_info=True)

		finally:
			curr.close()

		return results

	def get_missing_descriptions(self, db_conn, limit=500):
		LDA_LOG.info('Getting descriptions that do not have lda17 scores...')

		descriptions_query = '''
			SELECT
				DISTINCT ON (job_descriptions.job_id)
					job_descriptions.job_id,
				description
			FROM job_descriptions
			LEFT JOIN lda17_topics
			ON job_descriptions.job_id = lda17_topics.job_id
			WHERE lda17_topics.id IS NULL
			LIMIT %(limit)s;
		'''

		results = {}

		try:
			curr = db_conn.cursor()

			# Get the descriptions that don't have topic scores
			curr.execute(
				descriptions_query,
				{
					'limit': limit,
				}
			)
			qr = curr.fetchall()

			for result in qr:
				results[result[0]] = str(result[1])

		except Exception as e:
			LDA_LOG.warn(f'Exception {type(e)} while getting unscored descriptions: {e}')
			LDA_LOG.warn(e, exc_info=True)

		finally:
			curr.close()

		return results

	def save_scores(self, db_conn, job_scores: dict):
		LDA_LOG.info('Saving lda17 scores...')

		save_scores_query = '''
			INSERT INTO lda17_topics(job_id, lda0, lda1, lda2, lda3, lda4, lda5, lda6, lda7, lda8, lda9, lda10, lda11, lda12, lda13, lda14, lda15, lda16)
			VALUES (%(job_id)s, %(lda0)s, %(lda1)s, %(lda2)s, %(lda3)s, %(lda4)s, %(lda5)s, %(lda6)s, %(lda7)s, %(lda8)s, %(lda9)s, %(lda10)s, %(lda11)s, %(lda12)s, %(lda13)s, %(lda14)s, %(lda15)s, %(lda16)s);
		'''

		params_list = []
		for job_id, topic_scores in job_scores.items():
			params = {f'lda{n}': score for n, score in enumerate(topic_scores)}
			params['job_id'] = job_id
			params_list.append(params)

		try:
			LDA_LOG.info('Setting isolation level to READ COMMITTED')
			db_conn.set_isolation_level(1)
			LDA_LOG.info('Starting transactions...')
			curr = db_conn.cursor()

			# Save the topic scores to the database
			curr.executemany(
				save_scores_query,
				params_list
			)

			curr.close()
			LDA_LOG.info('Committing changes...')
			db_conn.commit()
			LDA_LOG.info('Added result to database.')

		except Exception as e:
			LDA_LOG.warn(f'Exception {type(e)} while saving lda17 scores: {e}')
			LDA_LOG.warn(e, exc_info=True)
			curr.close()

	def get_topic_scores(self, job_descriptions: Dict[int, str]) -> Dict[int, List[float]]:
		'''
		Gets the topic scores for one or more job descriptions

		Args:
			job_descriptions (dict): A dict of job_id: job_description

		Returns:
			dict: A dict of job_id: topic_scores (List[float])
		'''

		LDA_LOG.info(f'Getting lda17 topic scores for {len(job_descriptions)} descriptions...')
		job_ids, descriptions = zip(*job_descriptions.items())
		processed_descriptions = self.sentence_to_words(descriptions)
		bows = [self.id2word.doc2bow(description) for description in processed_descriptions]
		scores_list = []
		for bow in bows:  # for Bag of Words in Bags of Wordses
			topic_scores = [0 for _ in range(17)]
			topics = self.model.get_document_topics(
				bow,
				minimum_probability=0,
				minimum_phi_value=0
			)
			for topic_tuple in topics:
				# Note that topic numbers are 1-indexed by gensim
				# Hence why we assign to topic_tuple[0]-1
				topic_scores[topic_tuple[0] - 1] = float(topic_tuple[1])
				# We have to convert our numpy.float32 to Python floats
				# Since psycopg2 doesn't understand numpy.
			scores_list.append(topic_scores)

		results = {}
		for index, job_id in enumerate(job_ids):
			results[job_id] = scores_list[index]

		LDA_LOG.info('Got lda17 topic scores.')
		return results

	@staticmethod
	def sentence_to_words(sentences):
		for sentence in sentences:
			yield(gensim.utils.simple_preprocess(str(sentence), deacc=True))

	def __enter__(self):
		return (self)

	def __exit__(self, exc_type, exc_value, tb):
		LDA_LOG.info(f'__exit__ called, cleaning up...')
		LDA_LOG.info(f'exc_type: {exc_type}')
		del self.model
		del self.id2word
