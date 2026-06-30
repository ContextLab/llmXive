---
action_items:
- id: b40a00e03f45
  severity: writing
  text: Re-run the full data processing pipeline (main.py) to ensure data/processed/perplexity_scores.csv
    is generated with at least 1000 rows of valid perplexity scores corresponding
    to the code segments.
- id: 87039b63ddf6
  severity: writing
  text: Re-run the clone detection module (ast_cloner.py) to populate data/processed/clone_metrics.csv
    with at least 1000 rows of valid clone density metrics, ensuring the file size
    reflects actual data content (not just headers).
- id: 6ad4a0e2b923
  severity: writing
  text: Execute the PII scanning task (pii_scanner.py) against data/raw/ and data/processed/
    directories, and generate a log file (e.g., data/pii_scan_results.csv or update
    data/parse_failures.csv) explicitly documenting any PII patterns found or confirming
    a clean scan, as required by FR-009.
- id: 0b65cd15ecca
  severity: writing
  text: Verify and re-compute checksums for all newly generated data files using checksum_manifest.py
    to ensure the artifact_hashes state manifest reflects the actual content of the
    real, non-fabricated output files.
- id: ad310aad5a64
  severity: writing
  text: Re-run the correlation analysis (correlation_analysis.py) only after valid
    input files are confirmed, ensuring data/analysis/correlation_results.csv contains
    statistically valid Spearman coefficients and p-values derived from the real data.
artifact_hash: df541f9635dbd149df7f59163402805f16b4ddf5bbeded720b32b98edf2021a4
artifact_path: projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T16:49:07.129760Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: minor_revision
---

The project fails the research-stage data quality bar because the primary output artifacts are empty or missing, rendering the study irreproducible and scientifically unsound at this stage.

**1. Missing Primary Data Artifacts**
The `data/processed/perplexity_scores.csv` file is completely absent from the data summary. Per **FR-005** and **FR-008**, the system MUST compute and store token-level perplexity for each code segment. Without this file, the correlation analysis (FR-007) cannot be performed, and the research question remains unanswered.

**2. Empty/Insufficient Data Volume**
The `data/processed/clone_metrics.csv` file is reported as 25 bytes. This size is consistent with a CSV header row only, containing zero data records.
- **Violation of SC-003**: The success criteria explicitly require "At least 1000 code segments are successfully processed." The current artifact contains 0 segments.
- **Violation of FR-001**: The spec requires downloading and processing a 500MB subset. The empty output indicates the pipeline failed to ingest or process the data stream.

**3. Evidence of Fabricated/Simulated Results**
The execution evidence explicitly flags "263 fabricated/simulated-result signal(s)" and states "results are not real measurements."
- **Violation of Constitution Principle I (Reproducibility)**: Research artifacts must be derived from real data processing, not synthetic generation. The presence of fabricated signals invalidates the scientific validity of the current state.
- **Violation of FR-010**: Checksums recorded in the state manifest must correspond to real, computed output files. If the files are empty or fabricated, the checksums do not represent valid scientific artifacts.

**4. Missing PII Scan Results**
While `data/parse_failures.csv` exists (132 bytes), there is no evidence of a completed PII scan log or report as required by **FR-009** and **T017**. The spec mandates that PII findings be logged and flagged. The absence of a dedicated PII log or a populated scan result in the existing logs suggests this critical data hygiene step was not executed against the raw data.

**5. Incomplete Data Joining**
The `data/analysis/correlation_results.csv` exists (494 bytes), but given the upstream data is missing (perplexity) or empty (clone metrics), this file likely contains placeholder data or failed to compute valid correlations. **FR-007** requires segment-level correlation; without valid input vectors, this output is scientifically void.

The project cannot advance until the pipeline successfully processes the 500MB corpus, generates non-empty CSVs for clone metrics and perplexity scores, and produces a valid correlation result based on real measurements.

## Required Changes

- **Re-run the full data processing pipeline** (`main.py`) to ensure `data/processed/perplexity_scores.csv` is generated with at least 1000 rows of valid perplexity scores corresponding to the code segments.
- **Re-run the clone detection module** (`ast_cloner.py`) to populate `data/processed/clone_metrics.csv` with at least 1000 rows of valid clone density metrics, ensuring the file size reflects actual data content (not just headers).
- **Execute the PII scanning task** (`pii_scanner.py`) against `data/raw/` and `data/processed/` directories, and generate a log file (e.g., `data/pii_scan_results.csv` or update `data/parse_failures.csv`) explicitly documenting any PII patterns found or confirming a clean scan, as required by FR-009.
- **Verify and re-compute checksums** for all newly generated data files using `checksum_manifest.py` to ensure the `artifact_hashes` state manifest reflects the actual content of the real, non-fabricated output files.
- **Re-run the correlation analysis** (`correlation_analysis.py`) only after valid input files are confirmed, ensuring `data/analysis/correlation_results.csv` contains statistically valid Spearman coefficients and p-values derived from the real data.
