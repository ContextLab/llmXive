# Quickstart Guide: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

This guide explains how to run the pipeline, handle data scarcity, and interpret the results.

## Prerequisites

- Python 3.11+
- Virtual environment activated
- Dependencies installed (`pip install -r code/requirements.txt`)

## 1. Setup and Data Generation

Ensure the project directories exist and generate the mock dataset for testing:

```bash
python code/setup_directories.py
python code/data/generators.py --config default
```

This creates `data/raw/studies.csv` with synthetic mock data (labeled as such) for pipeline validation.

## 2. Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py
```

**Note:** The pipeline automatically detects the number of valid studies. If `N < 10` or `N_valid < 10`, it will **pivot to Narrative Mode** (see below).

## 3. Narrative Mode (Data Scarcity Handling)

If the dataset contains fewer than 10 studies, the quantitative meta-analysis is invalid. The system automatically switches to **Narrative Mode**.

### How to Trigger
- Run the pipeline with a small dataset (e.g., the default mock data often generates <10 studies).
- The `code/analysis/gatekeeper.py` script checks `study_count.json` and `valid_pair_count.json`.
- If `N < 10` or `N_valid < 10`, `gate_result.json` is set to `{"status": "narrative_required", "synthesis_mode": "narrative"}`.

### Expected Output Files
When in Narrative Mode, the following files are generated instead of quantitative results:
- `data/derived/pivot_log.json`: Contains the exact reason for the pivot (e.g., "N=5 < 10").
- `data/derived/narrative_summary.md`: The final report summarizing the absence of quantitative evidence.
- `data/derived/narrative_content.md`: The thematic analysis of available qualitative descriptors.

### ⚠️ Critical Warning
**Quantitative results are invalid if `synthesis_mode` is "narrative".**
Do not attempt to interpret meta-analysis statistics (e.g., forest plots, pooled effect sizes) if the pivot log indicates a narrative synthesis. The system will skip Egger's test, Bonferroni correction, and forest plot generation in this mode.

## 4. Verifying Results

Validate the output artifacts:

```bash
python code/quickstart_validator.py
```

This checks for the presence of required files and validates JSON schemas.

## 5. Generating the Paper Draft

Once the pipeline completes successfully:

```bash
python code/report/generate_paper.py
```

This renders `docs/paper_draft.md` using the results from `data/derived/results.json` or `data/derived/narrative_summary.md`.
