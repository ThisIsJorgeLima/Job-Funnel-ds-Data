
import os
import subprocess
import sys

from flask import Flask, jsonify

application = Flask(__name__)

SCRAPER_NAME = './run_scrapers.py'


@application.route('/start')
def start():
	"""
	Starts the web scrapers.
	"""

	tries = 0
	result = {
		'running': False,
		'tries': 0,
		'message': 'Unknown failure.'
	}
	try:
		while not check_running(SCRAPER_NAME) and tries < 5:
			with open(os.devnull, 'r+b', 0) as DEVNULL:
				subprocess.Popen(['nohup', sys.executable, SCRAPER_NAME],
					stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, close_fds=True, preexec_fn=os.setpgrp)
			tries += 1

		if check_running(SCRAPER_NAME):
			if tries == 0:
				result = {
					'running': True,
					'tries': tries,
					'message': f'{SCRAPER_NAME} already running.'
				}
			else:
				result = {
					'running': True,
					'tries': tries,
					'message': f'{SCRAPER_NAME} started after {tries} tries.'
				}
		else:
			result = {
				'running': False,
				'tries': tries,
				'message': f'Failed to start {SCRAPER_NAME} after {tries} tries.'
			}

	except Exception as e:
		result = {
			'running': False,
			'tries': tries,
			'message': f'Aborting after {type(e)} exception on try {tries}: {e}'
		}

	return jsonify(result)


def check_running(pname):
	result = os.system(f'ps -Af | grep -v grep | grep -v log | grep {pname}')
	return result == 0


if __name__ == '__main__':
	application.run()
