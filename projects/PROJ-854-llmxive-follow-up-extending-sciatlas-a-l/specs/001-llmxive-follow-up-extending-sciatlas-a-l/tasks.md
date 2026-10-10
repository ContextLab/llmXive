# Tasks: Interdisciplinary Bridging Coefficient Analysis  

**Inputs**: `spec.md`, `plan.md`, existing code base, contracts, data schemas.  
**Goal**: Deliver a fully reproducible CPU‑only pipeline that (1) ingests an OpenAlex‑derived subgraph from the prescribed local Parquet file, (2) computes Louvain clusters and bridging coefficients on the full graph, (3) generates title embeddings and topology‑independent novelty scores, (4) runs confounding‑controlled linear regression and Spearman correlation, (5) records all required success‑criterion metrics, and (6) produces a validated hand‑off report.  

---  

## Phase 0 – Project scaffolding & spec alignment  

- [ ] **T001** **Create project skeleton** – `mkdir -p src/{models,services,cli,utils} tests/{contract,integration,unit} data/{raw,processed} artifacts/{results,plots}`.  
  - *Verification*: `test -d src/models && test -d tests/unit && test -d data/processed`.  

- [ ] **T002** **Initialize `pyproject.toml`** – Define build system, project metadata, and runtime dependencies (`networkx>=3.0`, `pandas>=2.0`, `sentence-transformers>=2.2`, `scikit-learn>=1.3`, `statsmodels>=0.14`, `pyarrow>=12.0`, `datasets>=2.14`).  
  - *Verification*: `grep -q "networkx>=3.0" pyproject.toml && pip check`.  

- [ ] **T003** **Amend spec & plan for OpenAlex source** – Update every occurrence of “PubGraph” to “OpenAlex‑derived Subgraph” in `specs/001-bridging-coefficient-analysis/spec.md` and `specs/001-bridging-coefficient-analysis/plan.md`.  
  - *Verification*: `! grep -r "PubGraph" specs/001-bridging-coefficient-analysis/`.  

- [ ] **T004** **Amend FR‑006 to explicitly require Linear Regression** – Ensure the spec states “Linear Regression” (no NB GLM) and the plan mirrors this.  
  - *Verification*: `grep -q "Linear Regression" specs/001-bridging-coefficient-analysis/spec.md`.  

---  

## Phase 1 – Data ingestion & validation (US‑001)  

- [ ] **T005** **Ingest local subgraph** – Load `data/processed/subgraph.parquet` with `pandas.read_parquet`, validate each record against `data/schema/openalex_works.json` using `jsonschema`. Missing `cited_by_count` defaults to 0; null titles are logged to `data/processed/excluded_nodes.json`.  
  - *Verification*: Unit test `tests/unit/test_ingest_local.py` asserts schema‑validation passes and that a deliberately malformed row raises a `jsonschema.ValidationError`.  

- [ ] **T007** **Validate ingested graph integrity** – After T005, confirm required columns exist, compute basic statistics (node count, edge count), and ensure no schema violations remain.  
  - *Verification*: `tests/unit/test_graph_integrity.py` checks that the validation report reports zero errors.  

- [ ] **T022** **Record schema‑validation error rate (SC‑001)** – Parse the validation log from T005/T007, compute `error_rate = errors / total_records`, and write `artifacts/results/schema_validation_rate.json` (must be `0.0`). The CI fails if the rate is non‑zero.  
  - *Verification*: `tests/unit/test_schema_error_rate.py` asserts the JSON field `error_rate` equals `0.0`.  

- [ ] **T008** **Persist enriched subgraph (post‑clustering)** – After clustering (T009) and bridging calculation, write `data/processed/subgraph_with_clusters.parquet` with columns `id`, `title`, `cited_by_count`, `publication_date`, `field`, `primary_cluster`, `degree`, `inter_cluster_edges`, `bridging_coefficient`, `is_singleton`. Update `state/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l.yaml` with SHA‑256 hash and timestamp.  
  - *Verification*: `tests/integration/test_subgraph_output.py` validates schema against `contracts/subgraph_schema.schema.yaml` and checks the hash entry.  

---  

## Phase 2 – Topology & embedding (US‑002)  

- [ ] **T009** **Louvain clustering & bridging coefficient on full graph** – Load the full graph from T005, run Louvain (`community_louvain.best_partition`), compute `degree`, `inter_cluster_edges`, and `bridging_coefficient` per FR‑003 (including degree‑0 and intra‑cluster edge cases).  
  - *Verification*: `tests/unit/test_topology.py` asserts coefficients are 0.0 for isolated nodes and within `[0.0,1.0]` otherwise.  

- [ ] **T010** **Embedding generation (CPU‑only)** – Using `sentence-transformers/all-MiniLM-L6-v2` in CPU mode, batch titles (size 32), write embeddings to `data/processed/embeddings.parquet`. Log IDs with null/empty titles to `data/processed/excluded_nodes.json`.  
  - *Verification*: `tests/bench/test_embedding_speed.py` ensures median latency ≤ 50 ms per node; `tests/unit/test_embedding_dims.py` checks vector length 384.  

- [ ] **T011** **Compute topology‑independent novelty score** – Normalise embeddings, compute global centroid (mean of normalized vectors), calculate cosine distance for each node, store `novelty_score` in `data/processed/subgraph_with_clusters.parquet`. Nodes without embeddings receive `NaN`.  
  - *Verification*: `tests/unit/test_novelty_global_centroid.py` validates distance 0.0 for a matching synthetic vector; `tests/unit/test_novelty_independence.py` confirms scores unchanged after shuffling `primary_cluster`.  

- [ ] **T023** **Log novelty‑score variance (SC‑002)** – Compute variance of all `novelty_score` values and write `artifacts/results/novelty_variance.json`. This metric is later used in the final report.  
  - *Verification*: `tests/unit/test_novelty_variance.py` asserts the JSON field `novelty_score_variance` matches `np.var` of the scores.  

- [ ] **T012** **Assemble final analysis dataset** – Merge clustering, bridging, and novelty columns (excluding any `topic_cluster` field) into `data/processed/final_analysis_dataset.parquet` conforming to `contracts/final_dataset_schema.schema.yaml`.  
  - *Verification*: `tests/integration/test_final_dataset.py` validates schema compliance and required column ranges.  

---  

## Phase 3 – Statistical analysis & reporting (US‑003)  

- [ ] **T013** **Spearman correlation** – Compute Spearman rho and p‑value for (`bridging_coefficient`, `cited_by_count`) and (`bridging_coefficient`, `novelty_score`). Store results in `artifacts/results/correlation.json`.  
  - *Verification*: `tests/unit/test_correlation.py` checks JSON keys `rho`, `p_value`, `method`.  

- [ ] **T014** **Linear Regression with covariates (FR‑006)** – Fit an OLS model (`statsmodels.api.OLS`) with outcome `cited_by_count`, predictor `bridging_coefficient`, and covariates `publication_date` (as numeric age) and `field` (one‑hot). Record coefficients, p‑values, VIF scores, and R‑squared.  
  - *Verification*: `tests/unit/test_linear_regression.py` asserts VIF ≤ 5 and that the predictor coefficient appears in the output.  

- [ ] **T024** **Baseline regression & R‑squared improvement (SC‑003)** – Fit a baseline OLS model without covariates (only `bridging_coefficient`), compute `r_squared_improvement = r2_full - r2_baseline`, and write `artifacts/results/r_squared_improvement.json`.  
  - *Verification*: `tests/unit/test_rsq_improvement.py` checks that the JSON field `r_squared_improvement` is non‑negative.  

- [ ] **T015** **Multiple‑comparison correction** – CLI flag `--correction-method {bonferroni,bh}` selects method; apply to all p‑values from T013‑T014‑T024 and write `artifacts/results/corrected_pvalues.json`.  
  - *Verification*: `tests/unit/test_correction_config.py` asserts the `method` field matches the flag and adjusted p‑values differ from raw values.  

- [ ] **T016** **Generate analysis report** – `src/cli/main.py` creates `artifacts/results/analysis_report.md` containing methodology, correlation tables, regression tables (with VIF), novelty‑score variance (from T023), R‑squared improvement (from T024), explicit “associational” label, and conclusions.  
  - *Verification*: `tests/integration/test_report_generation.py` parses the markdown and asserts presence of the word “associational” and absence of “causal”.  

---  

## Phase 4 – Robustness, performance, and hand‑off  

- [ ] **T017** **Embedding latency benchmark** – Run the embedding pipeline on a 5 k‑node sample, write `artifacts/results/latency_report.json` (`max_latency_ms`).  
  - *Verification*: `tests/unit/test_latency_report.py` asserts `max_latency_ms` ≤ 50.  

- [ ] **T018** **Runtime measurement** – Execute the full pipeline (T005‑T016) on the default target size, write `artifacts/results/runtime_report.json` (`total_runtime_seconds`).  
  - *Verification*: `tests/unit/test_runtime_report.py` checks the value ≤ 21600 s (6 h).  

- [ ] **T019** **Memory profiling** – Enable `memory_profiler` in ingestion and embedding modules, run pipeline, write `artifacts/results/memory_report.json` (`peak_ram_gb`).  
  - *Verification*: `tests/unit/test_memory_report.py` asserts `peak_ram_gb` ≤ 7.0.  

- [ ] **T021** **Reproducibility audit** – Re‑run entire pipeline on a fresh clone, recompute SHA‑256 hashes for all artefacts in `artifacts/results/`, compare to entries in `state/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l.yaml`. Exit 0 on exact match.  
  - *Verification*: `tests/unit/test_audit.py` asserts success.  

---  

## Dependencies & execution order  

| Task | Depends on |
|------|------------|
| T001 | – |
| T002 | – |
| T003 | – |
| T004 | – |
| T005 | – |
| T007 | T005 |
| T022 | T007 |
| T008 | T009 |
| T009 | T005 |
| T010 | – |
| T011 | T010 |
| T023 | T011 |
| T012 | T009, T011 |
| T013 | T012 |
| T014 | T012 |
| T024 | T014 |
| T015 | T013, T014, T024 |
| T016 | T015 |
| T017 | T010 |
| T018 | T016 |
| T019 | T005, T010 |
| T021 | T016, T018, T019 |

---  

**Checkpoint summary**  

1. **Phase 0** – Project scaffolding and spec alignment are complete.  
2. **Phase 1** – Local ingestion, strict schema validation, and SC‑001 measurement are ready.  
3. **Phase 2** – Full‑graph clustering, embedding, novelty computation, and SC‑002 variance are produced.  
4. **Phase 3** – Linear regression, baseline comparison, R‑squared improvement (SC‑003), multiple‑comparison correction, and final report are generated.  
5. **Phase 4** – Performance, memory, and reproducibility artefacts guarantee compliance with all non‑functional requirements.  

All tasks now satisfy the specification, success criteria, and ordering constraints.  
