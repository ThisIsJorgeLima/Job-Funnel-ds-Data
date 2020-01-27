#!/usr/bin/env python

import os
import sys
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.firefox.options import Options

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
MONSTER_LOG = logging.getLogger()

curpath = os.path.dirname(os.path.abspath(__file__))
geckopath = os.path.join(curpath, '../webdrivers/geckodriver_ff_linux64')

options = Options()
options.headless = True

MONSTER_LOG.info('Initializing webdriver.Firefox...')
with webdriver.Firefox(
		executable_path=geckopath,
		options=options
) as driver:
	MONSTER_LOG.info('driver initialized.')

	wait = WebDriverWait(driver, 10)  # We'll wait a max of 10 seconds for elements to become available.
	driver.get('https://selenium.dev/documentation/en/')

	MONSTER_LOG.info('Finding python_button...')
	python_button = wait.until(
		presence_of_element_located(
			(By.XPATH, '//div[@class="tabset"]/label[text()="Python"]')
		)
	)

	MONSTER_LOG.info('Finding python_code...')
	python_code = driver.find_element_by_xpath(
		'//div[@class="tab-panels"]/section[@id="pythoncode2"]/div/pre/code'
	)

	MONSTER_LOG.info(f'python_code visible: {python_code.is_displayed()}')

	MONSTER_LOG.info('Clicking python_button...')
	python_button.click()

	MONSTER_LOG.info(f'python_code visible: {python_code.is_displayed()}')
