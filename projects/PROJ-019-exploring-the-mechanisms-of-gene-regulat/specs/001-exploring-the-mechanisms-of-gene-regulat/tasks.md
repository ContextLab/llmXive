# Tasks: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

**Input**: `spec.md`, `plan.md`, `data-model.md`, contracts in `specs/001-gene-regulation/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `data-model.md` (entity definitions)  

---  

## Phase 1 – Project scaffolding & pre‑flight checks  

- [X] T001 **Create project directory layout** – `mkdir -p code utils tests/unit tests/integration data/raw data/interim data/processed`  
  *Verification*: **T026** asserts that each of the directories exists after creation using `os.path.isdir`.  

- [ ] T002 **Pin Python dependencies** – write `requirements.txt` containing `requests pandas pybedtools scipy seaborn matplotlib biopython pytest psutil joblib` (Python 3.11).  
  *Verification*: **T027** runs `pip install -r requirements.txt` in a fresh virtualenv and checks that the exit code is 0.  

- [X] T003 **Implement configuration module** – create `code/config.py` defining `TMP_DIR` (default `/tmp`), `DATA_RAW_DIR`, `DATA_INTERIM_DIR`, `DATA_PROCESSED_DIR`, `MAX_RETRIES=3`, `RETRY_BACKOFF=2`, `EXPECTED_CELL_TYPES=['GM12878','K562','HepG2','H1-hESC','IMR90']`.  
  *Verification*: **T028** imports `code.config` and asserts that each constant exists with the expected type/value.  

- [X] T004 **Add pre‑flight utility scripts** –  
  - `code/utils/memory_check.py` (≥ 7 GB RAM)  
  - `code/utils/disk_check.py` (≥ 14 GB free on `TMP_DIR`)  
  - `code/utils/time_check.py` (abort > 6 h)  
  - `code/utils/network.py` (exponential back‑off, raises `MaxRetriesError`)  
  *Verification*: **T030** runs each script with artificially low limits and confirms a non‑zero exit status. Additional granular checks: **T032** (memory_check), **T033** (disk_check), **T034** (time_check), **T035** (network retry behavior).  

- [ ] T005 **Integrate pre‑flight checks into orchestrator** – modify `code/main.py` to import and execute the four utilities at the start of `run_pipeline()`.  
  *Verification*: **T036** executes `code/main.py --dry-run` with a failing utility and asserts that the pipeline aborts early.  

---  

## Phase 2 – Data ingestion & preprocessing (User Story 1)  

- [ ] T006 **Download ENCODE peak files with retry logic** – `code/download.py` uses `requests` + `code/utils/network.py` to fetch ATAC‑seq and ChIP‑seq BED files for the five cell types, writes them to `data/raw/`, and records SHA‑256 checksums in `data/provenance.json`.  
  *Verification*: **T037** checks that for each expected cell type a file exists in `data/raw/` and that its checksum matches the recorded value.  

- [ ] T007 **Parse and annotate peaks** – `code/preprocess.py` reads each raw BED, validates format, uses `pybedtools` to map to the nearest hg38 gene symbol, and writes standardized BEDs to `data/interim/annotated_<cell>.bed`.  
  *Verification*: **T038** validates each output BED against `peak.schema.yaml` via jsonschema.  

- [ ] T008 **Create per‑target background‑union BED** – `code/preprocess.py` aggregates the annotated peaks of the *other* four cell types for each target and writes `data/interim/background_union_<target>.bed`.  
  *Verification*: **T039** asserts that each union file exists and contains the union of the correct four cell‑type peak sets (simple line‑count sanity check).  

- [ ] T030 **Create concatenated background_union.bed** – concatenate all per‑target union files into `data/interim/background_union.bed` for convenience.  
  *Verification*: **T040** asserts that the concatenated file exists and that its line count equals the sum of the per‑target union files.  

- [ ] T009 **Generate ingestion summary** – `code/main.py` implements `run_ingestion()` which writes `data/processed/ingestion_summary.json` with the exact keys `total_peaks` (int), `cell_types` (list), `parsed_count` (int).  
  *Verification*: **T041** validates the JSON file against a tiny schema ensuring the three required keys and correct types.  

- [ ] T009V **Verify ingestion summary** – unit test that loads `ingestion_summary.json`, checks presence of required keys, and asserts `total_peaks` equals sum of per‑cell peak counts.  
  *Verification*: **T042** (new) runs the test and expects exit code 0.  

---  

## Phase 3 – Motif scanning (User Story 2)  

- [ ] T010 **Run FIMO on each cell‑type peak set** – `code/scan.py` builds a subprocess call:  
  ```bash
  fimo --thresh 0.0001 --text --bgfile data/interim/background_union_<cell>.bed \
       motifs/JASPAR2024.meme data/interim/annotated_<cell>.bed
  ```  
  Parses FIMO output and writes `data/interim/motif_matches_<cell>.tsv` conforming to `motif_match.schema.yaml`.  
  *Verification*: **T043** checks that the subprocess is invoked with the `--thresh 0.0001` flag and the correct background file, and that the resulting TSV validates against the schema.  

- [ ] T010V **Verify FIMO execution** – test that the subprocess call includes the correct threshold and background file, and that the output TSV passes schema validation.  
  *Verification*: **T044** runs the test and expects success.  

- [ ] T011 **Aggregate motif matches** – concatenate per‑cell TSVs into `data/interim/all_motif_matches.tsv`.  
  *Verification*: **T045** asserts that the aggregated file exists, contains rows from all five cells, and passes schema validation.  

---  

## Phase 4 – Enrichment analysis (User Story 2 continued)  

- [ ] T012 **Compute Fisher’s exact test per motif‑cell pair** – `code/enrichment.py` loads `all_motif_matches.tsv` and the appropriate `background_union_<cell>.bed`, builds contingency tables, runs `scipy.stats.fisher_exact`, and writes raw results to `data/interim/enrichment_raw.tsv`.  
  *Verification*: **T046** validates that `enrichment_raw.tsv` contains required columns and that p‑values are within [0,1].  

- [ ] T012V **Verify Fisher’s test output** – JSON‑schema validation of `enrichment_raw.tsv` against `enrichment.schema.yaml` (raw part) and sanity‑check that no p‑value is out of bounds.  
  *Verification*: **T047** runs the validation and expects exit code 0.  

- [ ] T013 **Apply Benjamini‑Hochberg correction** – `code/enrichment.py` reads raw p‑values, performs BH adjustment, adds `q_value` and `is_significant` fields, and writes the final matrix `data/processed/enrichment_matrix.csv` conforming to `enrichment.schema.yaml`.  
  *Verification*: **T048** validates the CSV against the schema and asserts that any row with `q_value < 0.05` has `is_significant = true`.  

- [ ] T013V **Verify enrichment matrix** – test that the CSV adheres to the schema, that BH correction was applied (q-values monotonic), and that at least one motif‑cell pair satisfies `q_value < 0.05` (SC‑002).  
  *Verification*: **T049** runs the test and expects success.  

---  

## Phase 5 – Visualization & clustering (User Story 3)  

- [ ] T014a **Generate heatmap image** – `code/visualize.py` loads `enrichment_matrix.csv`, pivots to a motif × cell matrix of q‑values, clusters with Euclidean distance, and saves `data/processed/heatmap.png`.  
  *Verification*: **T050** checks that `heatmap.png` exists and is a readable PNG file.  

- [ ] T014b **Compute silhouette score** – the same script computes the silhouette score (using `sklearn.metrics.silhouette_score`), writes `data/processed/silhouette_score.json`, and ensures the value is ≥ 0.4.  
  *Verification*: **T051** validates the JSON file exists and that the `silhouette_score` field meets the threshold.  

- [ ] T014c **Verify visualisation outputs** – test that `heatmap.png` is non‑empty, that `silhouette_score.json` passes schema validation, and that the score ≥ 0.4 (SC‑003).  
  *Verification*: **T052** runs the test and expects exit code 0.  

---  

## Phase 6 – Independent ChIP‑seq validation (User Story 3)  

- [ ] T015 **Fetch independent ChIP‑seq peaks** – `code/validate.py` queries the ENCODE REST API for each top‑ranked TF (q < 0.05) and its cell type, downloads the BED files to `data/raw/chip_<motif>_<cell>.bed`.  
  *Verification*: **T053** (renamed from previous T047) confirms that for every requested TF‑cell pair a BED file exists and that its checksum matches the provenance record.  

- [ ] T015V **Verify fetched ChIP‑seq files** – test that each downloaded BED file passes checksum verification and that provenance.json records are correct.  
  *Verification*: **T054** runs the test and expects success.  

- [ ] T016 **Calculate overlap statistics** – intersect predicted motif locations (`all_motif_matches.tsv`) with the fetched ChIP‑seq peaks, compute `overlap_percentage`, run a Fisher’s exact test for enrichment, and write `data/processed/validation_stats.json` adhering to `validation.schema.yaml`.  
  *Verification*: **T055** validates the JSON against the schema and asserts that for the top motifs `overlap_percentage >= 60`.  

- [ ] T016V **Verify validation statistics** – test that `validation_stats.json` conforms to the schema and that the ≥ 60 % overlap condition holds for the designated top motifs (SC‑003).  
  *Verification*: **T056** runs the test and expects exit code 0.  

- [ ] T017 **Assemble validation report** – `code/main.py` combines heatmap silhouette results, validation statistics, and writes `data/processed/validation_report.json` containing: `silhouette_score`, `silhouette_test_passed`, `overlap_percentage`, `overlap_test_passed`, `validation_passed`, and a list of top motifs with their q‑values and overlap stats.  
  *Verification*: **T057** checks the JSON schema and that boolean flags correctly reflect the thresholds (silhouette ≥ 0.4, overlap ≥ 60%).  

- [ ] T017V **Verify validation report** – test that `validation_report.json` matches its schema and that the flags are consistent with underlying metrics.  
  *Verification*: **T058** runs the test and expects success.  

---  

## Phase 7 – Final reporting  

- [ ] T018 **Create summary table** – `code/report.py` reads `enrichment_matrix.csv` and `validation_report.json`, selects the top N motifs (q < 0.05), and writes `data/processed/summary_table.csv` with columns `motif_id`, `p_value_raw`, `q_value_adj`, `chip_overlap_pct`.  
  *Verification*: **T059** validates the CSV schema and confirms that the `chip_overlap_pct` column is present and populated.  

- [ ] T018V **Verify summary table** – test that `summary_table.csv` adheres to the expected column schema and includes only rows where `q_value_adj < 0.05`.  
  *Verification*: **T060** runs the test and expects exit code 0.  

- [ ] T019 **Write quick‑start documentation** – `quickstart.md` (under `specs/001-gene-regulation/`) lists the single command `python -m code.main` and enumerates expected output files (`ingestion_summary.json`, `enrichment_matrix.csv`, `heatmap.png`, `validation_report.json`, `summary_table.csv`) plus hardware prerequisites (≥ 7 GB RAM, ≥ 14 GB disk, ≤ 6 h runtime).  
  *Verification*: **T061** runs the quick‑start command in a fresh clone and asserts that all listed files are generated.  

- [ ] T019V **Verify quick‑start execution** – integration test that executes the command from `quickstart.md` and checks for the presence and integrity of all expected output files.  
  *Verification*: **T062** runs the test and expects success.  

---  

## Phase 8 – Automated verification (tests)  

- [ ] T020 **Unit test for malformed BED handling** – `tests/unit/test_ingest.py::test_parse_handles_malformed_bed` expects `ValueError` and logs the error.  

- [ ] T021 **Unit test for network back‑off** – `tests/unit/test_network.py::test_retry_exponential_backoff` asserts `MaxRetriesError` after the configured number of attempts.  

- [ ] T022 **Unit test for background union correctness** – `tests/unit/test_background.py::test_union_aggregation` verifies that the union BED contains the correct number of unique intervals.  

- [ ] T023 **Unit test for Fisher‑exact & BH correction** – `tests/unit/test_motifs.py::test_fisher_exact_correction` checks known contingency tables against expected p‑values and q‑values.  

- [ ] T024 **Unit test for heatmap silhouette computation** – `tests/unit/test_viz.py::test_heatmap_silhouette_score` ensures a silhouette score is returned and logged.  

- [ ] T025 **Unit test for ChIP‑seq overlap calculation** – `tests/unit/test_validate.py::test_chip_overlap_calculation` validates the percentage computation on a small synthetic overlap scenario.  

- [ ] T053 **CI verification of test suite** – CI step runs `pytest -q` and asserts exit code 0 (no test failures).  

- [ ] T053V **Verify CI test execution** – ensures the CI step actually executed `pytest` and that the exit code was 0.  
  *Verification*: **T063** checks CI logs for successful pytest run.  

- [ ] T054 **Reference‑Validator invocation** – script `code/validate_citations.py` calls the platform’s Reference‑Validator Agent on all code and documentation files to ensure citation accuracy per Constitution Principle II.  
  *Verification*: CI step checks that the validator returns a success status.  

---  

## Dependencies & execution order  

| Task | Depends on |
|------|------------|
| T003 – T005 | T001, T002 |
| T006 | T003, T004 |
| T007 | T006, T003 |
| T008 | T007 |
| T030 | T008 |
| T009 | T008, T003 |
| T009V | T009 |
| T010 | T008, T003 |
| T010V | T010 |
| T011 | T010 |
| T012 | T011, T008 |
| T012V | T012 |
| T013 | T012 |
| T013V | T013 |
| T014a | T013 |
| T014b | T013 |
| T014c | T014a, T014b |
| T015 | T014a, T013 |
| T015V | T015 |
| T016 | T015 |
| T016V | T016 |
| T017 | T014a, T016, T014b |
| T017V | T017 |
| T018 | T013, T017 |
| T018V | T018 |
| T019 | T013, T018 |
| T019V | T019 |
| T020‑T025 | Corresponding implementation tasks |
| T053 | All implementation tasks |
| T053V | T053 |
| T054 | All code & docs |
| Tests (T020‑T025, T053‑T054) | Corresponding implementation tasks |

---  

**Note** – All tasks write only to project‑owned directories (`code/`, `data/`, `tests/`, `specs/...`). No synthetic data is generated; any failure to fetch real ENCODE or JASPAR resources aborts loudly, allowing the execution engine to retry on a GPU if needed (not applicable here). The pipeline is fully CPU‑tractable and respects the 6‑hour wall‑time budget.  
