---
action_items:
- id: ecc6e3b36831
  severity: writing
  text: '"Execute the full pipeline on the 500MB corpus and verify that data/processed/clone_metrics.csv
    contains at least 1000 rows of valid data (matching SC-003) and data/processed/perplexity_scores.csv
    is generated with corresponding perplexity values."'
- id: 062b03068b60
  severity: writing
  text: '"Debug and fix the silent failure in code/main.py or code/ast_cloner.py that
    results in empty output files, ensuring that the data loading (T018) and clone
    detection (T019) steps actually process the streamed dataset."'
- id: f874f3777708
  severity: writing
  text: '"Implement and verify the perplexity calculation logic in code/model_metrics.py
    to ensure it loads the Salesforce/codegen-350M-mono model and writes valid log-probability
    outputs to data/processed/perplexity_scores.csv."'
- id: 58ce92d05c6b
  severity: writing
  text: '"Run the PII scanner (code/pii_scanner.py) on the generated data files and
    ensure data/parse_failures.csv and the checksum manifest (code/checksum_manifest.py)
    are updated with valid entries for all non-empty output files."'
artifact_hash: df541f9635dbd149df7f59163402805f16b4ddf5bbeded720b32b98edf2021a4
artifact_path: projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T16:47:52.044886Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_correctness
score: 0.0
verdict: minor_revision
---

The implementation does not correctly realize the design specifications regarding data processing and metric generation. While the code structure exists, the execution evidence confirms a critical failure in the data pipeline: the primary output artifact `data/processed/clone_metrics.csv` is only 25 bytes (likely a header row with no data), and `data/processed/perplexity_scores.csv` is entirely missing. This directly contradicts **FR-001** (download 500MB subset), **FR-003** (compute clone density), and **FR-005** (compute perplexity), which require the system to process the corpus and store valid intermediate metrics.

The advisory note regarding "263 fabricated/simulated-result signal(s)" aligns with the implementation correctness failure: the code appears to have skipped the actual computation loops or failed silently without raising exceptions, resulting in empty or header-only CSVs. **FR-007** explicitly requires segment-level correlation analysis, which is impossible with empty input files. Additionally, **FR-009** (PII scanning) and **FR-010** (checksums) cannot be validated if the data files are empty or missing.

The current state represents a silent deviation from the spec where the pipeline orchestration (`main.py`) or individual modules (`ast_cloner.py`, `model_metrics.py`) failed to produce the required artifacts. The implementation must be corrected to ensure the data flow executes fully and populates the CSV files with actual computed values before the project can be considered reproducible.

## Required Changes
- "Execute the full pipeline on the 500MB corpus and verify that `data/processed/clone_metrics.csv` contains at least 1000 rows of valid data (matching SC-003) and `data/processed/perplexity_scores.csv` is generated with corresponding perplexity values."
- "Debug and fix the silent failure in `code/main.py` or `code/ast_cloner.py` that results in empty output files, ensuring that the data loading (T018) and clone detection (T019) steps actually process the streamed dataset."
- "Implement and verify the perplexity calculation logic in `code/model_metrics.py` to ensure it loads the `Salesforce/codegen-350M-mono` model and writes valid log-probability outputs to `data/processed/perplexity_scores.csv`."
- "Run the PII scanner (`code/pii_scanner.py`) on the generated data files and ensure `data/parse_failures.csv` and the checksum manifest (`code/checksum_manifest.py`) are updated with valid entries for all non-empty output files."
