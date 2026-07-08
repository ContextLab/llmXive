# Quickstart: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

## Prerequisites

- Python 3.11+
- `pip` (or `venv`/`poetry`)
- Access to an LLM API (e.g., OpenAI) or local model setup (e.g., `llama-cpp-python`).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-274-evaluating-the-impact-of-llm-generated-c
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Set environment variables** (for LLM API access):
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. **Pin random seeds** in `code/config.py`:
   ```python
   import random
   import numpy as np

   SEED = 42
   random.seed(SEED)
   np.random.seed(SEED)
   ```

## Running the Study

### Step 1: Repository Selection & Rubric (Phase 0)
```bash
python code/validation.py --rubric-check --input data/raw/repo_candidates.json --output data/raw/repo_selection_rubric.json
```

### Step 2: Generate Documentation (LLM Condition)
```bash
python code/doc_generation.py --repo <repo-url> --commit <commit-hash> --output data/raw/llm_docs/
```

### Step 3: Run Participant Sessions
- Recruit participants and assign conditions randomly.
- Use `code/data_collection.py` to log metrics during sessions.
- *Note*: If a moderator intervenes, ensure `intervention_flag` and `failure_reason` are recorded.

### Step 4: Contract Validation & Data Processing (Phase 3)
```bash
python code/validation.py --validate-schema --input data/raw/participant_logs.json --schema contracts/dataset.schema.yaml
python code/analysis.py --input data/processed/cleaned_dataset.csv --output data/reports/final_report.md
```

### Step 5: Analyze Data (LMM)
- The analysis script automatically fits a Linear Mixed-Effects Model (LMM) with `Repository` as a random effect.

## Validation

- **Mock Study**: Run with 3 simulated participants to verify data logging, schema validation, and analysis pipeline.
- **Contract Tests**: Validate data schemas against `contracts/*.schema.yaml`.
- **Power Check**: Verify that the report explicitly states the pilot nature and power limitations.

