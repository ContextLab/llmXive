# Quickstart: The Influence of Chatbot Politeness on User-Perceived Quality

## Prerequisites

- Python 3.11+
- R 4.3+ (for CLMM)
- Git
- HuggingFace CLI (optional, for manual downloads)
- `HF_TOKEN` (if datasets require authentication, though verified ones are public)

## Installation

1. **Clone the Repository**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-755-the-influence-of-chatbot-politeness-on-u
   ```

2. **Set Up Python Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

3. **Set Up R Environment**
   ```bash
   # Install R packages (if not pre-installed in CI)
   Rscript -e 'install.packages(c("ordinal", "lme4", "lmerTest", "car", "pryr"))'
   ```

4. **Configure Environment Variables**
   Create a `.env.template` file in the root (T010b):
   ```bash
   HF_TOKEN=your_token_here
   ```
   Copy to `.env` and fill in your token.

5. **Create Directory Structure** (T001a, T001b, T001c, T001d)
   Ensure the following directories exist:
   - `data/raw`, `data/processed`, `data/models`
   - `code`, `code/utils`
   - `tests`, `tests/contract`, `tests/unit`, `tests/integration`
   - `docs`, `docs/reports`, `state`

6. **Configure Linting** (T003)
   Create `pyproject.toml` with Black and Ruff settings:
   ```toml
   [tool.black]
   line-length = 88

   [tool.ruff]
   select = ["E", "F", "I"]
   ```

## Running the Pipeline

### 1. Data Download and Scoring (US1)
```bash
python code/download_and_score.py
# Output: data/processed/dialogues_scored.parquet
```
*Note: This step may take 1-3 hours on CPU. It will automatically stream data to avoid OOM.*

### 2. Primary Analysis (US2)
```bash
Rscript code/analysis_clmm.R
# Output: results/clmm_results.csv
```

### 3. Robustness Analysis (US3)
```bash
python code/robustness_analysis.py
# Output: results/robustness_results.csv
```

### 4. Generate Report
```bash
python code/generate_report.py
# Output: docs/reports/final_report.md
```

## Verification

To verify the installation and data integrity:
```bash
pytest tests/unit/
pytest tests/contract/
```

## CI Configuration (T004, T004b)

The `.github/workflows/ci.yml` file must include:
- Python 3.11 installation.
- R 4.3 installation.
- Installation of R packages: `lme4`, `ordinal`.
- Execution of `pytest` and `testthat`.
- Memory and runtime checks.

Example snippet:
```yaml
- name: Install R packages
  run: |
    Rscript -e 'install.packages(c("ordinal", "lme4", "lmerTest"))'
```

## Troubleshooting

- **OOM Error**: Ensure `streaming=True` is used in the data loader.
- **CLMM Convergence Failure**: The script will automatically log the failure and attempt a simplified fixed-effects model.
- **LIWC Missing**: The script will fall back to the `textstat` politeness lexicon and log the deviation.
