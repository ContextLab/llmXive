# PROJ-430: The Impact of Asynchronous Communication Delays on Team Cohesion

## Overview
This project investigates the correlation between asynchronous communication delays (response time variance) and team cohesion proxies in open-source software development.

## Structure
- `code/`: Source code for data ingestion, metrics calculation, sentiment analysis, and visualization.
- `data/`: Raw, derived, and validation data artifacts.
- `tests/`: Unit and integration tests.
- `specs/`: Research specifications and design documents.

## Prerequisites
- Python 3.11+
- Dependencies listed in `requirements.txt` (pandas, scikit-learn, nltk, requests, matplotlib, seaborn, pyyaml, langdetect, networkx)

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Configure paths in `code/config.py`.
3. Run the pipeline: `python code/pipeline.py`
