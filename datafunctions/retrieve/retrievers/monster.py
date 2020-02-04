#!/usr/bin/env python

import os
import sys
import logging
import time
import psycopg2
import bs4
import random
import requests

from decouple import config
from typing import Optional, List

from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located, element_to_be_clickable
from selenium.webdriver.firefox.options import Options

from datafunctions.retrieve.retrievefunctions import DataRetriever
from datafunctions.utils import titlecase

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
MONSTER_LOG = logging.getLogger()

curpath = os.path.dirname(os.path.abspath(__file__))
GECKOPATH = os.path.join(curpath, '../webdrivers/geckodriver_ff_linux64')


class MonsterScraper(DataRetriever):
	default_title_list = ['Data Analyst', 'Web Engineer', 'Software Engineer', 'UI Engineer', 'Backend Engineer', 'Machine Learning Engineer', 'Frontend Engineer', 'Support Engineer', 'Full-stack Engineer', 'QA Engineer', 'Web Developer', 'Software Developer', 'UI Developer', 'Backend Developer', 'Machine Learning Developer', 'Frontend Developer', 'Support Developer', 'Full-stack Developer', 'QA Developer', 'Developer']
	search_base_url = 'https://www.monster.com/jobs/search/'
	details_base_url = 'https://job-openings.monster.com/v2/job/pure-json-view'

	def __init__(self, driver=None, max_wait=5):
		if driver is None:
			options = Options()
			options.headless = True
			driver = webdriver.Firefox(
				executable_path=GECKOPATH,
				options=options
			)
		self.driver = driver
		self.wait = WebDriverWait(self.driver, max_wait)

	def build_search_url(self, job_title='', job_location='', time=1):
		params = {
			'where': job_location,
			'q': job_title,
			'tm': time,
		}
		MONSTER_LOG.info(f'Building search url with base url {self.search_base_url} and params {params}')
		query = urlencode(params)
		search_url = f'{self.search_base_url}?{query}'
		MONSTER_LOG.info(f'Built search url: {search_url}')
		return (search_url)

	def build_details_url(self, jobid):
		params = {
			'jobid': jobid,
		}
		MONSTER_LOG.info(f'Building details url with base url {self.details_base_url} and params {params}')
		query = urlencode(params)
		details_url = f'{self.details_base_url}?{query}'
		MONSTER_LOG.info(f'Built url: {details_url}')
		return (details_url)

	def add_to_db(self, db_conn, result):
		MONSTER_LOG.info('Adding result to database...')
		job_exists_query = """
			WITH listings AS (
				SELECT id
				FROM job_listings
				WHERE title = %(title)s
			), descriptions AS (
				SELECT job_id
				FROM job_descriptions
				WHERE description = %(description)s
			)
			SELECT listings.id
			FROM listings
			INNER JOIN descriptions
			ON listings.id = descriptions.job_id
			LIMIT 1;
		"""

		job_exists_query_2 = """
			WITH listings AS (
				SELECT id
				FROM job_listings
				WHERE title = %(title)s
			), c AS (
				SELECT id
				FROM companies
				WHERE name = %(name)s
			)
			SELECT listings.id
			FROM listings
			INNER JOIN job_companies
			ON job_companies.job_id = listings.id
			INNER JOIN c
			ON job_companies.company_id = c.id
			LIMIT 1
		"""

		job_listings_query = """
			INSERT INTO job_listings(title, post_date_utc)
			VALUES (%(title)s, to_timestamp(%(post_date_utc)s))
			RETURNING id;
		"""

		job_descriptions_query = """
			INSERT INTO job_descriptions(job_id, description)
			VALUES (%(job_id)s, %(description)s);
		"""

		job_links_query = """
			INSERT INTO job_links(job_id, external_url)
			VALUES (%(job_id)s, %(external_url)s);
		"""

		company_exists_query = """
			SELECT id
			FROM companies
			WHERE name = %(name)s
			LIMIT 1;
		"""

		companies_query = """
			INSERT INTO companies(name)
			VALUES (%(name)s)
			RETURNING id;
		"""

		job_companies_query = """
			INSERT INTO job_companies(job_id, company_id)
			VALUES (%(job_id)s, %(company_id)s);
		"""

		location_exists_query = """
			SELECT id
			FROM locations
			WHERE city = %(city)s
				AND state_province = %(state_province)s
				AND country = %(country)s
			LIMIT 1;
		"""

		locations_query = """
			INSERT INTO locations(city, state_province, country)
			VALUES (%(city)s, %(state_province)s, %(country)s)
			RETURNING id;
		"""

		job_locations_query = """
			INSERT INTO job_locations(job_id, location_id)
			VALUES (%(job_id)s, %(location_id)s);
		"""

		# Run order: job_listings, job_descriptions, companies, job_companies
		curr = db_conn.cursor()

		# Get the company id if it exists
		curr.execute(
			company_exists_query,
			{
				'name': result['company_name'],
			}
		)
		qr = curr.fetchone()
		if qr is not None:
			MONSTER_LOG.info(f'Company {result["company_name"]} already exists in DB.')
			company_id = qr[0]
		else:
			# Otherwise, insert the company and get the id
			MONSTER_LOG.info(f'Company {result["company_name"]} not yet in DB, adding...')
			curr.execute(
				companies_query,
				{
					'name': result['company_name'],
				}
			)
			company_id = curr.fetchone()[0]

		# Get the location id if it exists
		curr.execute(
			location_exists_query,
			{
				'city': result['city'],
				'state_province': result['state_province'],
				'country': result['country'],
			}
		)
		qr = curr.fetchone()
		if qr is not None:
			MONSTER_LOG.info(f'Location {result["city"]}, {result["state_province"]} already exists in DB.')
			location_id = qr[0]
		else:
			# Otherwise, insert the location and get the id
			MONSTER_LOG.info(f'Location {result["city"]}, {result["state_province"]} not yet in DB, adding...')
			curr.execute(
				locations_query,
				{
					'city': result['city'],
					'state_province': result['state_province'],
					'country': result['country'],
				}
			)
			location_id = curr.fetchone()[0]

		# Get the job listing id if it exists
		curr.execute(
			job_exists_query,
			{
				'title': result['title'],
				'description': result['description'],
			}
		)
		qr = curr.fetchone()
		# Get the job listing id if it exists, by company
		curr.execute(
			job_exists_query_2,
			{
				'title': result['title'],
				'name': result['company_name'],
			}
		)
		job_id = None
		qr2 = curr.fetchone()
		if qr is not None:
			MONSTER_LOG.info(f'Job listing for {result["title"]} already exists in DB.')
			job_id = qr[0]
		if qr2 is not None:
			MONSTER_LOG.info(f'Job listing for {result["title"]} at company {result["company_name"]} already exists in DB.')
			job_id = qr2[0]
		if job_id is None:
			# Otherwise, insert the job listing and get the id
			MONSTER_LOG.info(f'Job listing for {result["title"]} not yet in DB, adding...')
			curr.execute(
				job_listings_query,
				{
					'title': result['title'],
					'post_date_utc': result['timestamp'],
				}
			)
			job_id = curr.fetchone()[0]

			# Also add the relation to companies
			MONSTER_LOG.info(f'Adding relation job_id {job_id} to company_id {company_id}...')
			curr.execute(
				job_companies_query,
				{
					'job_id': job_id,
					'company_id': company_id,
				}
			)

			# Also add the relation to locations
			MONSTER_LOG.info(f'Adding relation job_id {job_id} to location_id {location_id}...')
			curr.execute(
				job_locations_query,
				{
					'job_id': job_id,
					'location_id': location_id,
				}
			)

			# And the description
			MONSTER_LOG.info('Saving description...')
			curr.execute(
				job_descriptions_query,
				{
					'job_id': job_id,
					'description': result['description'],
				}
			)

			# And the link to the job
			MONSTER_LOG.info('Saving link...')
			curr.execute(
				job_links_query,
				{
					'job_id': job_id,
					'external_url': result['inner_link'],
				}
			)

		curr.close()
		MONSTER_LOG.info('Committing changes...')
		db_conn.commit()
		MONSTER_LOG.info('Added result to database.')

	def get_jobs(self, db_conn, job_title='', job_location=''):
		url = self.build_search_url(job_title=job_title, job_location=job_location)
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

				wait_time = 0
				MONSTER_LOG.info(f'Loaded jobs, waiting {wait_time} seconds...')
				time.sleep(wait_time)
				# load_button.click()
			except Exception as e:
				tries += 1
				MONSTER_LOG.info(f'Exception {type(e)} while loading more jobs: {e}')
				MONSTER_LOG.info(e, exc_info=True)

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
			# result = self.get_info(result_element)
			result = self.get_details_json(result_element.get_attribute('data-jobid'))
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
				MONSTER_LOG.info('Getting outerHTML...')
				outerhtml = bs4.BeautifulSoup(result_element.get_attribute('outerHTML'))
				MONSTER_LOG.info('Converting to soup...')
				soup = outerhtml
				result = {}
				MONSTER_LOG.info('Getting company name...')
				# result['company_name'] = str(
				# 	result_element.find_element_by_xpath(
				# 		'.//*[@class="company"]/*[@class="name"]'
				# 	).get_attribute('innerHTML')
				# ).strip()
				result['company_name'] = str(
					soup.select_one('.company > .name').get_text().strip()
				)
				MONSTER_LOG.info('Getting location name...')
				# result['location'] = str(
				# 	result_element.find_element_by_xpath(
				# 		'.//*[@class="location"]/*[@class="name"]'
				# 	).get_attribute('innerHTML')
				# ).strip()
				result['location'] = str(
					soup.select_one('.location > .name').get_text().strip()
				)
				result['city'] = ''  # These would more properly be None
				result['state_province'] = ''  # However, psycopg2 manages to be utterly useless at handling NULL
				result['zip'] = ''  # So instead we use empty strings
				result['country'] = ''  # Good job, psycopg2
				try:
					location_parts = result['location'].split(',')
					result['city'] = titlecase(location_parts[0].strip())
					if len(location_parts) > 1:
						result['state_province'] = location_parts[1].strip().upper()
					if len(location_parts) > 2:
						result['zip'] = location_parts[2].strip()
					# if len(location_parts) > 3:
					# 	result['country'] = titlecase(location_parts[3].strip())
				except Exception as e:
					MONSTER_LOG.info(f'Exception while getting location parts: {e}')
					MONSTER_LOG.info(f'Location string: {result["location"]}')
				MONSTER_LOG.info('Getting job title...')
				# result['title'] = str(
				# 	result_element.find_element_by_xpath(
				# 		'.//*[@class="title"]/a'
				# 	).get_attribute('innerHTML')
				# ).strip()
				result['title'] = str(
					soup.select_one('.title > a').get_text().strip()
				)
				MONSTER_LOG.info('Getting job link...')
				# result['inner_link'] = str(
				# 	result_element.find_element_by_xpath(
				# 		'.//*[@class="title"]/a'
				# 	).get_attribute('href')
				# ).strip()
				result['inner_link'] = str(
					soup.select_one('.title > a')['href'].strip()
				)
				MONSTER_LOG.info('Getting jobid...')
				# result['title'] = str(
				# 	result_element.find_element_by_xpath(
				# 		'.//*[@class="title"]/a'
				# 	).get_attribute('innerHTML')
				# ).strip()
				result['monster_jobid'] = str(
					result_element.get_attribute('data-jobid')
				)

				# MONSTER_LOG.info('Getting date posted...')
				# result['posted'] = str(
				# 	result_element.find_element_by_xpath(
				# 		'.//*[@class="meta flex-col"]/time'
				# 	).get_attribute('innerHTML')
				# ).strip()

				# Monster doesn't provide a real post time
				# So instead we'll just put in right now
				# This will be at most 48 hours late, but usually closer to accurate
				result['timestamp'] = int(time.time())

				MONSTER_LOG.info(f'Got info: {result}')
				MONSTER_LOG.info('Clearing soup tree...')
				soup.decompose()

				result.update(self.get_details_json(result['monster_jobid']))
				break

			except Exception as e:
				MONSTER_LOG.info(f'Exception getting info for {result_element}: {e}')
				MONSTER_LOG.info(e, exc_info=True)
				wait_time = 1
				MONSTER_LOG.info(f'Waiting {wait_time} seconds...')
				time.sleep(wait_time)

		else:
			raise Exception('Unable to get info after 5 tries.')

		return (result)

	def get_details_json(self, result_element_jobid):
		details_url = self.build_details_url(result_element_jobid)
		MONSTER_LOG.info(f'Getting json for jobid: {result_element_jobid}')
		data = requests.get(details_url).json()
		MONSTER_LOG.info('Building description_soup...')
		description_soup = bs4.BeautifulSoup(data['jobDescription'])
		self.add_newlines(description_soup)
		MONSTER_LOG.info(f'Getting info...')
		title = data['companyInfo']['companyHeader'].replace(f' at {data["companyInfo"]["name"]}', '').strip()
		if data['isCustomApplyOnlineJob']:
			link = data['customApplyUrl']
		else:
			link = data['submitButtonUrl']
		result = {
			'description': description_soup.get_text().strip(),
			'company_name': data['companyInfo']['name'],
			'title': title,
			'inner_link': link,
			'country': data.get('jobLocationCountry', ''),
			'state_province': titlecase(data.get('jobLocationRegion', '')),
			'city': titlecase(data.get('jobLocationCity', '')),
			'timestamp': int(time.time()),
		}
		MONSTER_LOG.info(f'Got details, result: {result}')

		MONSTER_LOG.info('Cleaning description_soup...')
		description_soup.decompose()

		return (result)

	def add_newlines(self, soup):
		for elem in soup.find_all(['br', 'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
			elem.replace_with(elem.text + '\n')

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
		result['description'] = str(result_element.get_attribute('innerText')).strip()

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
		result['description'] = str(result_element.get_attribute('innerText')).strip()

		MONSTER_LOG.info('Done getting details for element.')
		return (result)

	def get_and_store_data(
			self,
			db_connection,
			title_list: Optional[List[str]] = None,
			**kwargs
	) -> None:
		if title_list is None:
			title_list = self.default_title_list
			random.shuffle(title_list)

		for job in title_list:
			try:
				self.get_jobs(db_connection, job_title=job)
			except Exception as e:
				MONSTER_LOG.warning(f'Failure while getting jobs for title {job}: {e}')
				MONSTER_LOG.info(e, exc_info=True)

	def __enter__(self):
		return (self)

	def __exit__(self, exc_type, exc_value, tb):
		MONSTER_LOG.info(f'__exit__ called, cleaning up...')
		MONSTER_LOG.info(f'exc_type: {exc_type}')
		self.driver.close()


# a = MonsterScraper()
# with psycopg2.connect(dbname=config("DB_DB"), user=config("DB_USER"), password=config("DB_PASSWORD"), host=config("DB_HOST"), port=config("DB_PORT")) as psql_conn:
# 	for job in title_list:
# 		a.get_jobs(psql_conn, job_title=job)
# a.driver.close()
# print(r[-1])

# sizes = []
# for r2 in r:
# 	for k, v in r2.items():
# 		sizes.append(sys.getsizeof(k))
# 		sizes.append(sys.getsizeof(v))
# print(sizes)
# print(sum(sizes) / len(r))
# print(sum(sizes))
