import logging
import gensim

from os.path import dirname, join

from datafunctions.model.modelfunctions import TopicModel

LDA_LOG = logging.getLogger(__name__)


class LDA17Model(TopicModel):
	def __init__(self):
		LDA_LOG.info('Loading lda17 model...')
		self.model = gensim.models.LdaModel.load(
			join(dirname(__file__), 'lda17_files', 'model')
		)
		self.id2word = gensim.corpora.Dictionary.load(
			join(dirname(__file__), 'lda17_files', 'id2word')
		)
		LDA_LOG.info('Done loading model.')

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

	def get_missing_descriptions(self, db_conn, limit=500):
		LDA_LOG.info('Getting descriptions that do not have lda17 scores...')

		descriptions_query = """
			SELECT
				DISTINCT ON (job_descriptions.job_id)
					job_descriptions.job_id,
				description
			FROM job_descriptions
			LEFT JOIN lda17_topics
			ON job_descriptions.job_id = lda17_topics.job_id
			WHERE lda17_topics.id IS NULL
			LIMIT %(limit)s;
		"""

		results = {}

		try:
			LDA_LOG.info('Starting transactions...')
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

		save_scores_query = """
			INSERT INTO lda17_topics(job_id, lda0, lda1, lda2, lda3, lda4, lda5, lda6, lda7, lda8, lda9, lda10, lda11, lda12, lda13, lda14, lda15, lda16)
			VALUES (%(job_id)s, %(lda0)s, %(lda1)s, %(lda2)s, %(lda3)s, %(lda4)s, %(lda5)s, %(lda6)s, %(lda7)s, %(lda8)s, %(lda9)s, %(lda10)s, %(lda11)s, %(lda12)s, %(lda13)s, %(lda14)s, %(lda15)s, %(lda16)s);
		"""

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

	def get_topic_scores(self, job_descriptions: dict):
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
