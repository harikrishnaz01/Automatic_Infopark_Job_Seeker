import csv
import re
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

LISTING_URL = "https://infopark.in/companies-job"
OUTPUT_FILE = "fresher_jobs.csv"
FRESHER_TERMS = re.compile(
	r"\b(fresher|freshers|entry[- ]level|trainee|intern|internship|graduate|"
	r"junior|0\s*(?:-|to)\s*1\s+years?|no\s+experience)\b",
	re.IGNORECASE,
)


def get_soup(session, url):
	response = session.get(url, timeout=15)
	response.raise_for_status()
	return BeautifulSoup(response.text, "html.parser")


def extract_jobs(soup):
	jobs = []
	for row in soup.select("table tr"):
		cells = row.find_all("td")
		if len(cells) < 4:
			continue

		detail_link = row.find("a", href=True)
		if detail_link is None:
			continue

		jobs.append(
			{
				"posted": cells[0].get_text(" ", strip=True),
				"title": cells[1].get_text(" ", strip=True),
				"company": cells[2].get_text(" ", strip=True),
				"closing_date": cells[3].get_text(" ", strip=True),
				"url": urljoin(LISTING_URL, detail_link["href"]),
			}
		)
	return jobs


session = requests.Session()
session.headers["User-Agent"] = "InfoparkJobseeker/1.0"
fresher_jobs = []

page_number = 1
while True:
	listing_url = LISTING_URL if page_number == 1 else f"{LISTING_URL}?page={page_number}"
	try:
		soup = get_soup(session, listing_url)
	except requests.RequestException as error:
		print(f"Could not fetch listing page {page_number}: {error}")
		break

	jobs = extract_jobs(soup)
	if not jobs:
		break

	print(f"Checking job listing page {page_number}: {len(jobs)} jobs")
	for job in jobs:
		if not FRESHER_TERMS.search(job["title"]):
			continue

		try:
			detail_soup = get_soup(session, job["url"])
		except requests.RequestException as error:
			print(f"Could not fetch {job['url']}: {error}")
			continue

		detail_text = detail_soup.get_text(" ", strip=True)
		if FRESHER_TERMS.search(f"{job['title']} {detail_text}"):
			fresher_jobs.append(job)

		sleep(1)

	page_number += 1
	sleep(1)

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as output:
	writer = csv.DictWriter(
		output,
		fieldnames=["posted", "title", "company", "closing_date", "url"],
	)
	writer.writeheader()
	writer.writerows(fresher_jobs)

print(f"Found {len(fresher_jobs)} possible fresher jobs.")
print(f"Saved results to {OUTPUT_FILE}")