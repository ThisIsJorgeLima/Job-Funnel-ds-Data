#!/usr/bin/env python

import os
import sys
import logging
import time
import psycopg2

from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located, element_to_be_clickable
from selenium.webdriver.firefox.options import Options

# from datafunctions.retrieve.retrievefunctions import DataRetriever

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
MONSTER_LOG = logging.getLogger()

curpath = os.path.dirname(os.path.abspath(__file__))
GECKOPATH = os.path.join(curpath, '../webdrivers/geckodriver_ff_linux64')

# options = Options()
# options.headless = True

# MONSTER_LOG.info('Initializing webdriver.Firefox...')
# with webdriver.Firefox(
# 		executable_path=GECKOPATH,
# 		options=options
# ) as driver:
# 	MONSTER_LOG.info('driver initialized.')

# 	wait = WebDriverWait(driver, 10)  # We'll wait a max of 10 seconds for elements to become available.

# 	url = 'https://www.monster.com/jobs/search/?q=Data+Analyst&where='
# 	MONSTER_LOG.info(f'Getting url: {url}')
# 	driver.get(url)

# 	# MONSTER_LOG.debug(driver.page_source)

# 	MONSTER_LOG.info('Finding mainContent...')
# 	mc = wait.until(
# 		presence_of_element_located(
# 			(By.XPATH, '//*[@id=\'mainContent\']')
# 		)
# 	)
# 	'/html/body/div[2]/main/div[1]/div[1]/div/div/div[2]/div/section[5]'

# 	MONSTER_LOG.info(f'mainContent: {mc}')

# 	MONSTER_LOG.info('Finding SearchResults...')
# 	wait.until(
# 		presence_of_element_located(
# 			(By.XPATH, '//*[@id="SearchResults"]/*[@class="card-content "]')
# 		)
# 	)

# 	MONSTER_LOG.info('Getting card-content...')
# 	results = driver.find_elements_by_xpath(
# 		'//*[@class="company"]//*[@class="name"]'
# 	)

# 	for result in results:
# 		MONSTER_LOG.info('card-content:')
# 		MONSTER_LOG.info(result.get_attribute('innerHTML'))


class MonsterScraper:  # (DataRetriever):
	search_base_url = 'https://www.monster.com/jobs/search/'

	def __init__(self, driver=None, max_wait=5):
		if driver is None:
			options = Options()
			# options.headless = True
			driver = webdriver.Firefox(
				executable_path=GECKOPATH,
				options=options
			)
		self.driver = driver
		self.wait = WebDriverWait(self.driver, max_wait)

	def build_url(self, job_title='', job_location='', time=1):
		params = {
			'where': job_location,
			'q': job_title,
			'tm': time,
		}
		MONSTER_LOG.info(f'Building url with base url {self.search_base_url} and params {params}')
		query = urlencode(params)
		search_url = f'{self.search_base_url}?{query}'
		MONSTER_LOG.info(f'Built url: {search_url}')
		return (search_url)

	def add_to_db(self, db_conn, result):
		MONSTER_LOG.info('Adding result to database...')
		"""
			WITH j_values AS (
				SELECT
					%(title)s::TEXT AS title,
					%(description)s::TEXT AS description
			), extant AS (
				SELECT job_id AS id FROM jobs_descriptions
				WHERE
					jobs_descriptions.description = j_values.description
			),
		"""
		job_listings_query = """
			WITH j_values AS (
				SELECT
					%(title)s::TEXT AS title,
					%(description)s::TEXT AS description
			)
			INSERT INTO job_listings(title)
			SELECT j_values.title
			FROM j_values
			WHERE NOT EXISTS (
				SELECT job_id AS id FROM jobs_descriptions
				WHERE
					jobs_descriptions.description = j_values.description
			)
			RETURNING id;
		"""
		jobs_descriptions_query = """
			WITH jd_values AS (
				SELECT
					%(job_id)s AS job_id,
					%(description)s::TEXT AS description
			)
			INSERT INTO jobs_descriptions(job_id, description)
			SELECT jd_values.job_id, jd_values.description
			FROM jd_values
			WHERE NOT EXISTS (
				SELECT id FROM jobs_descriptions
				WHERE
					jobs_descriptions.job_id = jd_values.job_id
					AND jobs_descriptions.description = jd_values.description
			)
			RETURNING id;
		"""
		companies_query = """
			WITH c_values AS (
				SELECT
					%(name)s::TEXT AS name,
					%(description)s::TEXT AS description,
					%(size)s::INT AS size,
					%(revenue)s::INT AS revenue
			)
			INSERT INTO companies(name, description, size, revenue)
			SELECT
				c_values.name,
				c_values.description,
				c_values.size,
				c_values.revenue
			FROM c_values
			WHERE NOT EXISTS (
				SELECT id FROM companies
				WHERE
					companies.name = c_values.name
			)
			RETURNING id;
		"""
		jobs_companies_query = """
			WITH jc_values AS (
				SELECT
					%(job_id)s::INT AS job_id,
					%(company_id)s::INT AS company_id
			)
			INSERT INTO jobs_companies(job_id, company_id)
			SELECT
				jc_values.job_id,
				jc_values.company_id
			FROM jc_values
			WHERE NOT EXISTS (
				SELECT id FROM jobs_companies
				WHERE
					jobs_companies.job_id = jc_values.job_id
					AND jobs_companies.company_id = jc_values.company_id
			)
			RETURNING id;
		"""

		# Run order: job_listings, jobs_descriptions, companies, jobs_companies
		curr = db_conn.cursor()
		curr.execute(
			job_listings_query,
			{
				'title': result['title'],
				'description': result['description'],
			}
		)
		job_id = curr.fetchone()[0]
		curr.execute(
			jobs_descriptions_query,
			{
				'job_id': job_id,
				'description': result['description'],
			}
		)
		curr.execute(
			companies_query,
			{
				'name': result['company_name'],
				'description': None,
				'revenue': None,
				'size': None,
			}
		)
		company_id = curr.fetchone()[0]
		curr.execute(
			jobs_companies_query,
			{
				'job_id': job_id,
				'company_id': company_id
			}
		)
		curr.close()
		MONSTER_LOG.info('Committing changes...')
		db_conn.commit()
		MONSTER_LOG.info('Added result to database.')

	def get_jobs(self, db_conn, job_title='', job_location=''):
		url = self.build_url(job_title=job_title, job_location=job_location)
		MONSTER_LOG.info(f'Getting url: {url}')
		self.driver.get(url)

		content_xpath = '//*[@id="SearchResults"]/*[contains(@class, "card-content") and not(contains(@class, "apas-ad"))]'
		MONSTER_LOG.info(f'Waiting for element: {content_xpath}')
		self.wait.until(
			presence_of_element_located(
				(By.XPATH, content_xpath)
			)
		)

		load_button_xpath = '//*[@id="loadMoreJobs"]'

		page_count = 1
		tries = 0
		max_tries = 3
		while tries < max_tries:
			MONSTER_LOG.info(f'Attempting to load more jobs (try {tries + 1} of {max_tries}) (page {page_count})')
			try:
				load_button = self.wait.until(
					presence_of_element_located(
						(By.XPATH, load_button_xpath)
					)
				)

				self.driver.execute_script("arguments[0].click();", load_button)

				tries = 0
				page_count += 1
				# load_button.click()
			except Exception as e:
				tries += 1
				MONSTER_LOG.info(f'Exception {type(e)} while loading more jobs: {e}')

		# MONSTER_LOG.info('Waiting 10 seconds...')
		# time.sleep(10)

		MONSTER_LOG.info(f'Getting elements: {content_xpath}')
		result_elements = self.driver.find_elements_by_xpath(
			content_xpath
		)
		result_elements_count = len(result_elements)
		MONSTER_LOG.info(f'Got {result_elements_count} elements.')

		# results = []

		for index, result_element in enumerate(result_elements):
			MONSTER_LOG.info(f'Getting info for element {index + 1} of {result_elements_count}')
			result = self.get_info(result_element)
			self.add_to_db(db_conn, result)

		# MONSTER_LOG.info(f'Getting details for jobs...')
		# for result in results:
		# 	max_tries = 3
		# 	for tries in range(max_tries):
		# 		try:
		# 			result = self.get_details(result)
		# 			break
		# 		except Exception as e:
		# 			MONSTER_LOG.info(f'Exception getting details [try {tries + 1} of {max_tries}]: {e}')

		MONSTER_LOG.info(f'Done getting jobs.')
		# return (results)

	def get_info(self, result_element, max_tries=5):
		for tries in range(max_tries):
			try:
				MONSTER_LOG.info(f'Getting info for {result_element} [try {tries + 1} of {max_tries}]')
				result = {}
				result['company_name'] = result_element.find_element_by_xpath(
					'.//*[@class="company"]/*[@class="name"]'
				).get_attribute('innerHTML')
				result['location'] = result_element.find_element_by_xpath(
					'.//*[@class="location"]/*[@class="name"]'
				).get_attribute('innerHTML')
				result['title'] = result_element.find_element_by_xpath(
					'.//*[@class="title"]/a'
				).get_attribute('innerHTML')
				result['inner_link'] = result_element.find_element_by_xpath(
					'.//*[@class="title"]/a'
				).get_attribute('href')
				result['posted'] = result_element.find_element_by_xpath(
					'.//*[@class="meta flex-col"]/time'
				).get_attribute('innerHTML')

				MONSTER_LOG.info(f'Got info: {result}')

				result.update(self.get_details_inline(result_element))
				break

			except Exception as e:
				MONSTER_LOG.info(f'Exception getting info: {e}')
				MONSTER_LOG.info(f'Element HTML:\n{result_element.get_attribute("innerHTML")}')
				wait_time = 1
				MONSTER_LOG.info(f'Waiting {wait_time} seconds...')
				time.sleep(wait_time)

		return (result)

	def get_details_inline(self, result_element):
		result = {}

		MONSTER_LOG.info(f'Getting details for {result_element}')
		self.driver.execute_script("arguments[0].click();", result_element)
		# result_element.click()

		content_xpath = '//*[@id="JobDescription"]'
		MONSTER_LOG.info(f'Waiting for element: {content_xpath}')
		result_element = self.wait.until(
			presence_of_element_located(
				(By.XPATH, content_xpath)
			)
		)

		MONSTER_LOG.info('Getting element text...')
		result['description'] = result_element.text

		MONSTER_LOG.info('Done getting details for element.')
		return (result)

	def get_details(self, result):
		MONSTER_LOG.info(f'Getting details for result: {result}')

		url = result['inner_link']
		MONSTER_LOG.info(f'Getting url: {url}')
		self.driver.get(url)

		content_xpath = '//*[@id="JobDescription"]'
		MONSTER_LOG.info(f'Waiting for element: {content_xpath}')
		result_element = self.wait.until(
			presence_of_element_located(
				(By.XPATH, content_xpath)
			)
		)

		MONSTER_LOG.info('Getting element text...')
		result['description'] = result_element.text

		MONSTER_LOG.info('Done getting details for element.')
		return (result)

	def get_data(self):
		return super().get_data()


a = MonsterScraper()
with psycopg2.connect(database='jobs') as psql_conn:
	a.get_jobs(psql_conn, job_title='Data Analyst')
a.driver.close()
# print(r[-1])

# sizes = []
# for r2 in r:
# 	for k, v in r2.items():
# 		sizes.append(sys.getsizeof(k))
# 		sizes.append(sys.getsizeof(v))
# print(sizes)
# print(sum(sizes) / len(r))
# print(sum(sizes))
