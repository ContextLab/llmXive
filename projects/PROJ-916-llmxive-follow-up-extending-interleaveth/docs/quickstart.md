# Quickstart Guide for llmXive

## Prerequisites

- Python 3.11+
- pip
- Git

## Setup

1. Clone the repository:
 ```bash
 git clone
 cd llmxive
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. Configure environment variables (optional):
 ```bash
 cp.env.example.env
 # Edit.env with your configuration
 ```

## Running the Pipeline

To run the full experiment pipeline:
```bash
python run_experiment.py
```

To run a specific user story:
```bash
python run_experiment.py --story US1
```

## Data

Real data is fetched automatically by the data loader. Ensure you have network access.
Core datasets (WISE, RISE) are required; the pipeline will fail if they are unavailable.

## Validation

Run the validation suite:
```bash
pytest tests/
```

## Next Steps

- Read `docs/design.md` for architecture details.
- Review `docs/api.md` for API reference.
- Explore `docs/user_stories.md` for feature specifications.
