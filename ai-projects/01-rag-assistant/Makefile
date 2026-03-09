.PHONY: install test run ingest

install:
	pip install -r requirements.txt

test:
	pytest -q

run:
	uvicorn api:app --reload --port 8000

ingest:
	python ingest.py --source data --out index.json
