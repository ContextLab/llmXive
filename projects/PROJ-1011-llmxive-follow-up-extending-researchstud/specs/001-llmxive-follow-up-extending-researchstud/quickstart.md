# Quickstart: llmXive follow-up: extending "ResearchStudio-Idea"

## Prerequisites

*   Python 3.11+
*   Git
*   Access to GitHub Actions (for CI execution) or local environment with sufficient RAM.
*   API Key (Hugging Face) - required for generation.
*   Prolific Account (for expert recruitment) - required for real evaluation.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-1011-llmxive-follow-up-extending-researchstud
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### Step 1: Data Acquisition
Download and parse the abstracts. (Automatically switches to fallback if paywalled).
```bash
python code/01_data_acquisition.py
```
*Expected Output*: `data/processed/corpus_clean.jsonl` (600 entries).

### Step 2: Pattern Mapping & Validation
Compute embeddings and validate pattern applicability.
```bash
python code/02_pattern_mapping.py
python code/02_pattern_validation.py
```
*Expected Output*: `data/processed/embeddings.jsonl`, `data/processed/pattern_validation.jsonl`.

### Step 3: Proposal Generation
Generate proposals (pattern-guided, random-pattern, and baseline).
```bash
python code/03_proposal_generation.py
```
*Note*: This step uses Hugging Face API. If rate-limited, it automatically switches to Ollama.

### Step 4: Expert Recruitment & Evaluation
**Recruitment**:
1.  Run `python code/utils/recruit_experts.py` to generate the Prolific study link and instructions.
2.  Recruit 15 experts until Krippendorff's alpha ≥ 0.6 is achieved.
3.  Upload the collected `ratings.csv` to `data/processed/ratings.csv`.

**Load Data**:
```bash
python code/04_evaluation_loader.py
```
*Expected Output*: `data/processed/ratings.csv` (validated).

### Step 5: Statistical Analysis
Run the statistical tests and generate the report.
```bash
python code/05_statistical_analysis.py
```
*Expected Output*: `data/processed/results.json`, `paper/analysis_report.md`.

## Verification

To verify the pipeline on a small scale (Dry-Run mode):
```bash
pytest tests/unit/test_statistical_logic.py -v
python code/05_statistical_analysis.py --dry-run
```

## Troubleshooting

*   **OOM Error**: Reduce batch size in `config.py` or switch to API-based generation.
*   **Paywall Error**: Check the logs. The pipeline should have automatically switched to `arxiv` or `pubmed` fallback.
*   **Missing Data**: Ensure `data/raw/` is populated before running `01_data_acquisition.py`.
*   **Low IRR**: If Krippendorff's alpha < 0.6, the pipeline will halt and request more experts. Recruit additional raters and re-run Step 4.