# Tasks: llmXive follow‑up – extending “ResearchStudio‑Idea”

**Input**: `specs/001-llmxive-extension/spec.md`, `plan.md`, existing artifacts, reviewer feedback.  
**Goal**: End‑to‑end pipeline that (1) acquires real abstracts from ML and non‑ML venues, (2) maps non‑ML problem statements to the 15 ML‑derived ideation patterns, (3) generates paired research proposals, (4) blind‑distributes them for expert rating, (5) performs a fully‑specified statistical analysis, and (6) produces a final report that satisfies every functional requirement and success criterion.

---

## Phase 1 – Project scaffolding

- [X] **T001** Create project layout (`projects/PROJ‑1011‑llmxive‑follow‑up‑extending‑researchstud/`, `code/`, `data/`, `tests/`).  
  *Verification*: `test_scaffold_directories` asserts existence of all top‑level folders.

- [X] **T002** Add `requirements.txt` (pinned Python 3.11 dependencies) and `run_pipeline.sh`.  
  *Verification*: `test_requirements_present` checks file existence and that `run_pipeline.sh` is executable.

- [X] **T003** Add `quickstart.md` with the command `./run_pipeline.sh --stage all`.  
  *Verification*: `test_quickstart_content` parses the markdown and confirms the command string.

- [ ] **T004** Create data directories (`data/raw/`, `data/processed/`, `data/results/`) and a `data/CHECKSUMS` manifest.  
  *Verification*: `test_data_dirs_and_checksum` confirms directories exist and manifest file is present.

- [X] **T005** Implement seed‑pinning utility (`code/utils/config.py`) for reproducibility.  
  *Verification*: `test_seed_pinning` imports the config and checks that `numpy.random.seed`, `random.seed`, and `torch.manual_seed` are set.

- [ ] **T006** Add state‑management helper (`code/utils/update_state.py`) for artifact hash tracking.  
  *Verification*: `test_state_update` runs the helper on a dummy file and asserts the hash is recorded in `state/...`.

- [X] **T007** Define data‑model classes (`code/models/abstract.py`, `pattern_card.py`, `proposal.py`, `rating.py`).  
  *Verification*: `test_model_classes` imports each class and validates schema‑conformance via `jsonschema`.

- [ ] **T008** Create error‑handling wrapper that **fails loudly** on data‑fetch errors and logs a model‑fallback switch.   <!-- FAILED-IN-EXECUTION: code/error_handling_wrapper.py exit=1 -->
  *Verification*: `test_error_wrapper` triggers a simulated fetch failure and asserts a non‑zero exit code.

- [ ] **T009** Create `data-sources.yaml` with verified URLs for the ML corpus, *Nature Climate Change*, and *Health Affairs*; include a `fallback` entry for each venue.  
  *Verification*: `test_data_sources_yaml` loads the YAML and checks that each venue has `primary` and `fallback` URLs.

---

## Phase 2 – Corpus acquisition & pre‑processing  

> **User Story 1 – Priority P1**  

- [ ] **T011** `code/01_data_acquisition.py` – download, paginate, balance, and validate abstracts.  
  *Requirements & outputs*  
  - Reads venue URLs from `data-sources.yaml`.  
  - Uses the arXiv API for the ML corpus and DOI‑based APIs for the non‑ML venues.  
  - Retrieves ≈ 200 ML, ≈ 200 non‑ML accepted, ≈ 200 non‑ML rejected records (±10 %).  
  - On any HTTP 4xx/5xx or pay‑wall detection, raises `DataFetchError` with a clear message listing the failed venue and **exits non‑zero** (no synthetic fallback).  
  - Streams the download to keep peak RAM < 5 GB.  
  - Writes raw JSONL to `data/raw/corpus_raw.jsonl` (checksummed).  
  - Validates each record against `contracts/schema_abstract.schema.yaml`; discards malformed entries with an error log.  
  - Writes the cleaned, balanced corpus to `data/processed/corpus_clean.jsonl`.  
  - Emits `INFO`/`ERROR` messages to `logs/data_acquisition.log` and records request metadata in `logs/data_provenance.jsonl`.  
  *Verification*: `test_download_and_parse_open_datasets` asserts balance, proper error handling, and that both output files exist with correct checksums.

- [ ] **T012** `code/01_data_acquisition.py` – logging & checksum update (covered within T011).  
  *Verification*: `test_checksum_update` confirms SHA‑256 entries for both raw and processed files are added to `data/CHECKSUMS`.

- [ ] **T007b** `code/02_problem_statement.py` – create and validate **ProblemStatement** entities from `data/processed/corpus_clean.jsonl`.  
  *Requirements & outputs*  
  - Extracts the problem statement from the abstract text.  
  - Validates each ProblemStatement against a corresponding JSON schema (id, abstract_id, problem_text, domain).  
  - Writes `data/processed/problem_statements.jsonl`.  
  *Verification*: `test_problem_statement_creation` checks that each non‑ML abstract yields exactly one ProblemStatement with a unique ID and correct foreign‑key to the abstract.

- **Verification** (unit tests in `tests/unit/`):  
  - `test_download_and_parse_open_datasets` (balance & error handling).  
  - `test_preprocessing_validation` (empty abstracts raise `ValueError`).  
  - `test_memory_usage_constraint` (streams full download, peak RAM < 7 GB via `tracemalloc`).  

---

## Phase 3 – Pattern mapping (embedding)  

> **User Story 2 – Priority P2**  

- [ ] **T020** `code/02_pattern_mapping.py` – compute semantic similarity using a **quantized BERT‑base** retrieval system (`sentence-transformers/bert-base-nli-mean-tokens` quantized for CPU).  
  *Requirements*  
  - Loads the quantized BERT-base model.  
  - If model loading exceeds the 6.5 GB memory budget, catches the error and falls back to a smaller MiniLM variant (`sentence-transformers/all-MiniLM-L12-v2-quantized`), logging the switch with reason.  
  - Stores embeddings in `data/processed/embeddings.jsonl`.  
  - For every problem statement, returns the **top‑3** pattern IDs with cosine similarity ≥ 0.6 and records the three similarity scores.  
  *Verification*: `test_pattern_mapping_similarity` ensures fallback is triggered on a simulated `MemoryError` and that the returned list always contains three patterns meeting the threshold.

---

## Phase 4 – Paired proposal generation  

> **User Story 2 – continued**  

- [ ] **T024** `code/03_proposal_generation.py` – generate 50 pattern‑guided and 50 baseline proposals (100 total).  
  *Core logic*  
  - Reads problem statements from `data/processed/problem_statements.jsonl` (selects the 50 non‑ML statements).  
  - For each statement:  
    1. Retrieves top‑3 patterns via **T020**.  
    2. Constructs a **pattern‑guided** prompt that injects the three pattern descriptions.  
    3. Constructs a **baseline** prompt that only contains “Be creative and propose a research study addressing the problem.”  
    4. Calls the LLM API (or local quantised model) with deterministic `seed` (pinned in `config.py`).  
    5. Records generation metadata (model name, timestamp, token count, generation time, `patterns_used`).  
    6. Stores the three cosine scores under `pattern_confidence_scores`.  
  - Writes a single JSONL file `data/results/generated_proposals.jsonl` that conforms to `contracts/schema_proposal.schema.yaml` and contains exactly 100 rows (50 pattern‑guided, 50 baseline).  
  *Verification*: `test_proposal_generation_logic` asserts row count = 100, correct split, presence of `pattern_confidence_scores` for pattern‑guided rows only, and that generation metadata fields are populated.

---

## Phase 5 – Expert recruitment, blind distribution & mock rating generation  

> **User Story 3 – Priority P3**  

- [ ] **T050** `code/05_expert_recruitment.py` – recruit domain experts, verify ORCID IDs, confirm ≥ 5 years experience, and record verified expert profiles in `data/experts/verified_experts.csv`.  
  *Verification*: `test_expert_orcid_verification` checks that each listed expert has a valid ORCID checksum and the required experience field.

- [ ] **T059a** `code/04_evaluation_loader.py` – create blind batches for expert rating and enforce expert‑verification constraints.  
  *Steps*  
  - Loads `data/results/generated_proposals.jsonl`.  
  - Strips all fields containing generation metadata.  
  - Generates a deterministic `blinded_id` (UUID v5 based on proposal ID).  
  - Writes `data/results/blinded_batches.csv` with columns: `blinded_id, problem_statement, domain, instructions`.  
  - `instructions` embed the alignment rubric (“Rate feasibility, bottleneck identification, and contextual alignment on a 1‑5 Likert scale. Do **not** consider how the proposal was generated.”).  
  - **Hard block**: runs `verify_blind_metadata()` that aborts with exit‑code 1 if any prohibited token (e.g., `pattern‑guided`, `baseline`, `confidence`) appears.  
  - **Expert‑verification check**: ensures that `data/experts/verified_experts.csv` exists and that every expert listed has a valid ORCID and ≥ 5 years experience.  
  - **Rating‑minimum check**: asserts that the downstream rating ingestion will provide ≥ 3 ratings per proposal (fails early if not).  
  *Verification*: `test_blind_batch_integrity` confirms no prohibited tokens, correct column set, and that the expert‑verification and rating‑minimum preconditions are satisfied.

- [ ] **T059b** `code/04_evaluation_loader.py` – deterministic mock‑rating generator (dry‑run only).  
  *Outputs*  
  - Uses a fixed random seed (`42`).  
  - For each of the 100 proposals creates **3** expert ratings for each of the three metrics (`feasibility`, `bottleneck`, `alignment`).  
  - Writes `data/results/ratings_filled.csv` adhering to `contracts/schema_rating.schema.yaml` with `mock: true` on every row.  
  - Includes a few extreme outlier scores (e.g., 1 and 5) to exercise the outlier‑removal logic later.  
  *Verification*: `test_mock_real_schema_equivalence` confirms that the mock CSV matches the schema of real ratings and that the `mock` flag is present.

- [ ] **T064** `run_pipeline.sh` – add a `--dry-run` flag that executes only the health‑check, power‑analysis config (`T024b`), and mock‑rating path (`T059b`) without contacting external APIs or the LLM.  
  *Verification*: `test_dry_run_flag` runs the script with `--dry-run` and checks that only the expected artifact files are created and no network calls are made (mocked).

- [ ] **T061** `code/utils/fabrication_guard.py` – scans every file under `data/` and `code/` for prohibited synthetic markers (`mock_`, `synthetic`, stray `random_seed`).  
  *Runs* as a pre‑commit hook **and** as a CI step **before** T055.  
  *Verification*: `test_fabrication_guard` creates a temporary file with a forbidden marker and asserts that the guard raises `FabricationError`.

- [ ] **T068** `code/01_data_acquisition.py` – extend logging to record full request metadata (URL, query params, response headers) for every successful fetch; write JSON lines to `logs/data_provenance.jsonl`.  
  *Verification*: `test_provenance_log` reads the log and asserts that each entry contains `request_url`, `request_params`, and `response_headers`.

---

## Phase 6 – Statistical‑analysis pipeline (single comprehensive task)

- [ ] **T024b** `code/05_statistical_analysis.py` – **power‑analysis** implementation.  
  *Function*: reads `n_pairs` from `data/results/generated_proposals.jsonl`, computes achieved power for α = 0.05 and target d = 0.5 using `statsmodels`, writes `data/results/power_analysis_config.json` with fields `n_pairs`, `alpha`, `target_effect_size`, `achieved_power`.  
  *Verification*: `test_power_analysis_output` checks that the JSON file exists, contains all required fields, and that `achieved_power` is a number between 0 and 1.

- [ ] **T036** `code/05_statistical_analysis.py` – **calculate_validity_improvement()** implementation.  
  *Function*: using expert mean **alignment** scores (not retrieval similarity), compute `alignment_mean_pattern_guided`, `alignment_mean_baseline`, `alignment_difference`, and write `data/results/validity_metrics.json` (conforms to `schema_results`).  
  *Verification*: `test_validity_metrics_schema` validates the JSON against the schema and checks that `metric_source` equals `"expert_mean_scores"`.

- [ ] **T055** `code/05_statistical_analysis.py` – end‑to‑end analysis covering IRR, outlier handling, normality, hypothesis testing, multiple‑comparison correction, power analysis, validity improvement, and report generation.  
  *Sub‑steps* (sequential, each writing an artifact):  
  1. Load ratings (`data/results/ratings_filled.csv`).  
  2. **IRR gate** – compute Krippendorff’s α; abort if any α < 0.6.  
  3. **Outlier removal** – IQR method, flag rows removed.  
  4. **Normality check** – Shapiro‑Wilk on paired differences; choose paired t‑test or Wilcoxon.  
  5. **Primary paired test** – compute raw p‑value, effect size, store in `data/results/statistical_tests.json`.  
  6. **Multiple‑comparison correction** – Benjamini‑Hochberg across three metrics.  
  7. **Validity‑improvement** – invoke `calculate_validity_improvement()` (T036).  
  8. **Power‑analysis configuration** – invoke T024b.  
  9. **Report generation** – invoke `generate_report()` (T037).  
  *Verification*: `test_full_analysis_pipeline` asserts that all intermediate artifacts (`irrs.json`, `outliers_removed.csv`, `statistical_tests.json`, `validity_metrics.json`, `power_analysis_config.json`, `analysis_report.md`) exist, that IRR ≥ 0.6, and that the report contains the required sections.

- [ ] **T037** `code/05_statistical_analysis.py` – **report generation** implementation.  
  *Requirements*: render `data/results/analysis_report.md` including:  
  - Data provenance summary (links to `logs/data_provenance.jsonl`).  
  - Table of raw and BH‑corrected p‑values, effect sizes, outlier‑removal flags.  
  - Validity‑improvement numbers.  
  - Power‑analysis outcome and note if power < 0.80.  
  - Mandatory phrase **“associational, not causal”** in the conclusion (asserted; aborts otherwise).  
  - If all ratings are mock, prepend a dry‑run disclaimer.  
  *Verification*: `test_report_rhetorical_constraint` parses the generated Markdown and asserts the required phrase, correct dry‑run labeling, and that all artifact files exist.

---

## Phase 7 – Cross‑cutting safeguards & utilities  

- [ ] **T040** `code/utils/runtime_monitor.py` – monitor total pipeline execution time and peak RAM usage.  
  *Integration*: invoked at the start of `run_pipeline.sh` and writes `logs/runtime_monitor.log` with `total_seconds` and `peak_ram_gb`.  
  *Verification*: `test_runtime_monitor` runs a short dummy pipeline and asserts that the logged values are ≤ 6 h and ≤ 7 GB, satisfying **SC‑003**.

- [ ] **T069** `tests/unit/test_fabrication_guard.py` – implements verification for T061.  

- [ ] **T070** `tests/unit/test_dry_run_flag.py` – implements verification for T064.  

- [ ] **T071** `tests/unit/test_provenance_log.py` – implements verification for T068.  

- [ ] **T072** `tests/unit/test_runtime_monitor.py` – implements verification for T040 (covers SC‑003).  

---

## Dependency & execution order (updated)

| Phase | Task ID | Depends on |
|------|---------|------------|
| 1 | T001‑T009 | – |
| 2 | T011‑T013, T007b | T009 (data‑sources.yaml) |
| 3 | T020 | T011 (clean corpus) |
| 4 | T024 | T020 (embeddings) |
| 5 | T050 | – |
| 5 | T059a | T024 (generated proposals) |
| 5 | T059b | – (dry‑run path) |
| 6 | T024b | T024 (generated proposals) |
| 6 | T036 | T059a (blinded batches) |
| 6 | T037 | T036 |
| 7 | T061 | **must run before** T055 |
| 6 | T055 | T059a **or** T059b, **after** T061 |
| 7 | T064 | – |
| 7 | T068 | runs within T011 |
| 7 | T040 | runs at pipeline start, results used for SC‑003 verification |
| 7 | T069‑T072 | unit‑test suite (CI) |

Running the full pipeline:

```bash
./run_pipeline.sh --stage all          # real end‑to‑end execution
./run_pipeline.sh --stage all --dry-run  # CI sanity check (no external calls)
```

All tasks are unchecked (`[ ]`) and will be marked complete by the CI verification suite once their respective unit/integration tests pass.  