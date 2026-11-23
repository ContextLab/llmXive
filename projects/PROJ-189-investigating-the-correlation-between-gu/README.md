# PROJ-189: Investigating the Correlation Between Gut Microbiome and Cognitive Decline

## Description
This project analyzes the correlation between gut microbiome composition (AGP 16S data) and cognitive decline metrics (HRS data). The pipeline ingests raw data, performs preprocessing (rarefaction, filtering), and executes statistical correlation and predictive modeling.

## Setup Instructions
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `source venv/bin/activate` (Linux/Mac) or `venv\\Scripts\\activate` (Windows)
4. Install dependencies: `pip install -r code/requirements.txt`
5. Run directory setup: `python code/setup_dirs.py`
6. Configure environment variables: Copy `code/.env.example` to `code/.env` and fill in values.
