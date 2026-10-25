# Tasks: How does topological complexity of logical dependency graphs limit convergence of Reflective Masking loops in Mask Diffusion Models?

**Inputs**: `specs/001-llmxive-follow-up-extending-multi-turn-r/spec.md`, `plan.md`, `data-model.md`, `contracts/`  

The following checklist implements the full end‑to‑end study while addressing the reviewer‑reported failures in **T002**, **T003**, and **T004**. Checked tasks are already verified; unchecked tasks remain to be executed.

---

- [ ] T001  Project scaffolding and dependency pinning  
  *Create the required directory tree (`data/raw/`, `data/processed/`, `data/results/`, `code/`, `code/utils/`, `code/tests/`, `results/paper_figures/`) and a reproducible `code/requirements.txt` that pins `torch==2.2.0`, `transformers`, `datasets`, `networkx`, `lifelines`, `scikit-learn`, `pandas`, `numpy==1.24.3`, `pytest`, `ruff`, `black`.*  
  **Verification**: `pip install -r code/requirements.txt` succeeds; `find . -name __init__.py` lists three init files; `ruff check --output-format=concise` exits 0.  

- [ ] T002  Resolve test‑environment incompatibility and add integration tests for the puzzle generator  
  *Modify `code/graph_generator.py` to avoid importing `datasets`/`pyarrow` at import time (lazy‑load only when needed) and adjust `code/tests/test_graph_generator.py` accordingly. Add a lightweight integration test that (1) runs the generator on a tiny seed (e.g., `--num 10`), (2) validates the resulting JSONL against `SyntheticPuzzle` schema, and (3) checks that the empirical Pearson |r| between `nesting_depth` and `branching_factor` is < 0.2.*  
  **Prerequisite**: T003 (generator must exist).  
  **Tags**: [FR-001]  
  **Verification**: `pytest code/tests/test_graph_generator.py` exits 0 with all tests passing.

- [ ] T003  Orchestrate deterministic synthetic puzzle generation (wrapper)  
  *Runs the subtasks T014‑T016 to produce primary and auxiliary puzzle sets, enforce orthogonalization, and generate checksums.*  
  **Tags**: [FR-001] [FR-006] [FR-007]  
  **Verification**: All subtasks succeed; final checksum files exist and validate.

- [ ] T014  Graph construction and topology control  
  *Create `code/graph_generator.py` and `code/utils/graph_utils.py` that generate DAGs with controlled `nesting_depth` (3‑6 for primary, 7‑10 for auxiliary) and `branching_factor` (1‑5). Enforce acyclicity and solvability, compute `nesting_depth`, `branching_factor`, `token_length`, `lexical_complexity`, and `target_path_id` (perturbed from longest path).*  
  **Tags**: [FR-001] [FR-006] [FR-007]  
  **Verification**: Generation script runs without error and produces in‑memory structures matching constraints.

- [ ] T015  Schema validation and file writing  
  *Validate each generated puzzle against `contracts/synthetic_puzzle.schema.yaml`. Write primary puzzles to `data/raw/synthetic_puzzles.jsonl` (500 instances) and auxiliary puzzles to `data/raw/aux_puzzles.jsonl` (200 instances).*  
  **Tags**: [FR-001] [FR-006] [FR-007]  
  **Verification**: `wc -l` counts are correct; `jsonschema.validate` passes for every line.

- [ ] T016  Checksum generation and manifest update  
  *Compute SHA‑256 checksums for `synthetic_puzzles.jsonl` and `aux_puzzles.jsonl` and write them to `data/checksums_primary.txt` and `data/checksums_aux.txt` respectively. Append both entries to the master checksum manifest later.*  
  **Tags**: [FR-001]  
  **Verification**: `sha256sum -c` succeeds for both files.

- [ ] T004  Implement CPU‑only Reflective Masking executor and smoke‑test run  
  *Create `code/rm_executor.py` and extend `code/utils/graph_utils.py` with an Independent Logical Validator (ILV) that:*  
  1. **Loads** the pre‑trained Mask Diffusion model on `device="cpu"` (`torch_dtype=torch.float32`) using a path read from `code/.env` (`MODEL_PATH`). Failure to load aborts with a clear error (no GPU fallback).  
  2. **Runs** the RM loop `run_rm_loop(puzzle_text, model, max_turns)` with a hard turn cap of 50 (primary) and records per‑turn masks/predictions.  
  3. **Computes** `path_coverage` (fraction of edges matched) and `exact_match` (inferred path equals `ground_truth_path`).  
  4. **Logs** each run to a temporary CSV with columns matching the `ExecutionLog` contract.  
  5. **Provides** a smoke‑run script `code/run_rm_smoke.py` that processes the first 10 puzzles from `data/raw/synthetic_puzzles.jsonl` and writes `data/processed/execution_log_smoke.csv`.  
  6. **Adds unit tests** in `code/tests/test_rm_executor.py` covering model loading, turn‑limit enforcement, ILV logic on handcrafted outputs, and schema compliance of the CSV.  
  **Tags**: [FR-002] [FR-003]  
  **Verification**: `pytest code/tests/test_rm_executor.py` exits 0; header present; 10 rows present; CSV validates against `contracts/execution_log.schema.yaml`.

- [ ] T005  Full primary RM execution on the 500‑instance dataset  
  *Using `code/rm_executor.py`, stream `data/raw/synthetic_puzzles.jsonl` in batches of 4, run the RM loop with `max_turns=50`, and write the results to `data/processed/execution_log.csv` (exact schema fields). Record total wall‑clock time (must be ≤ 6 h) and append the SHA‑256 checksum of the CSV to `data/checksums_primary.txt`.*  
  **Tags**: [FR-002] [FR-003] [SC-001] [SC-003]  
  **Verification**: `len(df)==500`; checksum passes; runtime ≤ 21600 s.

- [ ] T006  Compute divergence between model output paths and longest graph paths  
  *Create `code/verify_divergence.py` that reads `data/processed/execution_log.csv`, recomputes the longest path for each puzzle (using `graph_utils`), calculates `longest_path_divergence` (fraction of steps differing), and writes a summary JSON `data/results/divergence_summary.json`. Append its checksum to `data/checksums_divergence.txt`.*  
  **Tags**: [SC-006]  
  **Verification**: script exits 0; JSON contains non‑null `average_divergence`; checksum passes.

- [ ] T007  Extended‑budget validation on a random 20 % subset of primary failures  
  *Select a reproducible random 20 % of instances where `convergence_status == "failure"` in `execution_log.csv` (seed = 42). Re‑run these instances with `max_turns=1000` using the same executor, write results to `data/processed/extended_budget_log.csv`, and record a checksum in `data/checksums_extended.txt`.*  
  **Tags**: [FR-008] [SC-007]  
  **Verification**: row count equals 0.2 × (number of primary failures); schema compliance; checksum passes.

- [ ] T008  Statistical analysis and aggregated result generation  
  *Implement `code/analyzer.py` to perform:*  
  1. **Cox Proportional Hazards** on `turns_to_converge` (censored at 50) with predictors `nesting_depth` and `branching_factor`. Run Schoenfeld residuals test; if PH assumption fails, automatically fall back to an Accelerated Failure Time model.  
  2. **Generalized Linear Model (logistic regression)** on binary success/failure as a secondary inference (satisfies FR‑004).  
  3. **Spearman rank correlation** between `nesting_depth` and `turns_to_converge`.  
  4. **Segmented (piecewise linear) regression** to locate the tipping‑point depth, reporting `tipping_point_depth` and `tipping_point_slope_change`.  
  5. **Collinearity diagnostics** (VIF) and recompute the orthogonality Pearson coefficient.  
  6. **Budget‑exhaustion rate** from T007 (fraction of 50‑turn failures that succeed by 1000 turns).  
  7. **Assemble** all metrics into `results/statistical_report.json` matching `analysis_result.schema.yaml`.  
  8. **Write** a checksum to `data/checksums_analysis.txt` and add unit tests `code/tests/test_analyzer.py` for schema compliance and sanity checks on synthetic data.  
  **Tags**: [FR-004] [FR-005] [SC-001] [SC-002] [SC-004] [SC-005]  
  **Verification**: `pytest code/tests/test_analyzer.py` exits 0; JSON validates; required fields present.

- [ ] T009  Sensitivity analysis on convergence thresholds (40 / 50 / 60 turns)  
  *Read `execution_log.csv` and `extended_budget_log.csv`, recompute failure rates for turn caps 40, 50, and 60, update the `failure_rates` map inside `results/statistical_report.json`, and write a human‑readable markdown summary `results/extended_budget_analysis.md`. Record checksum in `data/checksums_sensitivity.txt`.*  
  **Tags**: [FR-005] [SC-004]  
  **Verification**: JSON contains keys `"40"`, `"50"`, `"60"`; markdown lists counts and percentages; checksum passes.

- [ ] T010  Generate figures and tables for the paper  
  *Create `code/visualize.py` that consumes `results/statistical_report.json` and the CSV logs to produce:*  
  1. Hazard‑ratio curve by depth (PNG).  
  2. Segmented‑regression tipping‑point plot (PNG).  
  3. Threshold‑sensitivity bar chart (PNG).  
  4. Table `data/results/summary_table.csv` summarising key metrics.  
  All PNGs are saved under `results/paper_figures/`. Scripts are seeded for deterministic output; re‑run produces byte‑identical files.  
  **Tags**: [SC-001] [SC-002] [SC-004]  
  **Verification**: each PNG exists and is non‑empty; `md5sum -c` matches stored checksums.

- [ ] T011  Aggregate all checksum manifests into a master file  
  *Concatenate `data/checksums_primary.txt`, `data/checksums_aux.txt`, `data/checksums_divergence.txt`, `data/checksums_extended.txt`, `data/checksums_analysis.txt`, `data/checksums_sensitivity.txt`, and any other checksum files into `data/checksums.txt`. Verify the master file with `sha256sum -c data/checksums.txt`.*  
  **Verification**: command exits 0; master file lists a checksum line for every artifact produced in the pipeline.

- [ ] T012  Write a concise methods & results narrative linked to artifacts  
  *Compose `specs/001-llmxive-follow-up-extending-multi-turn-r/research.md` (or `results/RESULTS.md`) that:*  
  - Describes dataset construction (primary + auxiliary), orthogonalization, and randomized path perturbation (FR‑001, FR‑006, FR‑007).  
  - Details the RM loop configuration, CPU‑only model loading, turn limits, and ILV success definition (FR‑002, FR‑003).  
  - Summarizes statistical methodology (Cox PH, AFT fallback, GLM, segmented regression, Spearman, sensitivity analysis) and reports the exact numbers from `results/statistical_report.json`.  
  - Presents the divergence metric findings (SC‑006) and the budget‑exhaustion rate (SC‑007).  
  - Includes explicit references to all generated artefacts (e.g., “Figure 1 – `results/paper_figures/hazard_curve.png`”).  
  **Verification**: A script `code/verify_narrative.py` parses the markdown, extracts all numeric literals via the regex `\b\d+(\.\d+)?\b`, reads a generated index file `data/narrative_index.json` that maps each numeric claim to the line number(s) in the referenced artifact, and asserts that every claim has a corresponding entry. The script exits 0 only if all checks pass.  
  **Tags**: [SC-001] [SC-002] [SC-004] [SC-006] [SC-007]

- [ ] T013  Create a reproducible quick‑start guide and validate end‑to‑end execution  
  *Add `specs/001-llmxive-follow-up-extending-multi-turn-r/quickstart.md` that lists the exact commands to:*  
  1. Install dependencies (`pip install -r code/requirements.txt`).  
  2. Run the generator (`python -m code.graph_generator --num 500`).  
  3. Execute the primary RM run (`python -m code.rm_executor --max-turns 50`).  
  4. Run the extended‑budget validation (`python -m code.rm_executor --max-turns 1000 --subset failures`).  
  5. Perform analysis (`python -m code.analyzer`).  
  6. Produce figures (`python -m code.visualize`).  
  7. Verify checksums (`sha256sum -c data/checksums.txt`).  
  *Finally, run the entire workflow on a fresh clone in a temporary directory and confirm that the resulting checksums match those recorded in `data/checksums.txt`.*  
  **Verification**: a CI‑style script `code/run_full_workflow.sh` clones the repository, follows the quickstart steps, and exits 0; the final checksum verification passes, demonstrating full reproducibility.  
  **Tags**: [Infrastructure]

## Dependency mapping

| Spec requirement | Covered by task(s) |
|------------------|--------------------|
| FR‑001, FR‑006, FR‑007 | T003, T014, T015, T016 |
| FR‑002, FR‑003 | T004, T005 |
| FR‑004, FR‑005 | T008, T009 |
| FR‑008 | T007 |
| SC‑001 – SC‑007 | T005‑T010, T008 |
| Contracts (schemas) | T002, T004, T008, T010, T012 |
| Infrastructure | T001, T011, T013 |

Execution order (implicit from dependencies):  

T001 → T003 → T014 → T015 → T016 → T002 → T004 → T005 → {T006, T007} → T008 → T009 → T010 → T011 → T012 → T013.  

All tasks respect data flow, use real synthetic data, run on CPU, and avoid any fabricated inputs.  

---  

**Note**: Parallel execution flags (`[P]`) have been removed from tasks that modify shared state or depend on other tasks, ensuring safe sequential execution.  
