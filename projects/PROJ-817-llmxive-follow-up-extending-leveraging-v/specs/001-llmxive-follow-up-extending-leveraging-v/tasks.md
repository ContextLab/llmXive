# Tasks: Does a symbolic constraint‑graph preprocessing module mitigate verifier degradation on conflicting image‑editing instructions?

**Inputs**: `specs/001-llmxive-verifier-graph/spec.md`, `plan.md`, `data-model.md`, `evaluation_report.schema.yaml`, original research idea and validation notes.

The tasks respect the data‑flow ordering, compute‑feasibility rules, and all functional requirements (FR‑001 – FR‑010) and success criteria (SC‑001 – SC‑010). Paths are relative to the project root and write only under `data/`, `figures/`, `code/`, or `specs/`.

---

## Phase 1 – Setup and first end‑to‑end analysis  

*Goal*: Verify that a thin pipeline runs on real data before scaling to the full study.

- [ ] T001 **[P1] [US‑1] Download raw InstructPix2Pix shards** – implement `code/src/data/download.py` that:
  1. Retrieves the three verified parquet shard URLs listed in the spec (e.g.,  
     `https://huggingface.co/datasets/instructpix2pix/resolve/main/train-00000.parquet`, etc.).
  2. Streams each file to `data/raw/` without loading the whole file into memory.
  3. Computes a SHA‑256 checksum for every row and writes a manifest `data/raw/checksums_manifest.json`.
  4. Fails loudly on any network or checksum error; **no synthetic fallback** is permitted.  
  *Verification*: Run `python -m code.src.data.download`; confirm the three parquet files exist, each contains ≥ 30 000 rows, and the manifest entries match the on‑disk checksums. The script must exit with a non‑zero code if any download fails.

- [ ] T002 **[P1] [US‑1] Curate a balanced 1 000‑prompt CSV** – implement `code/src/data/curate.py` (and helper `code/src/data/conflict_generator.py`) to:
  1. Load the raw parquet shards from `data/raw/`.
  2. Randomly select 500 neutral prompts (no explicit contradiction or temporal cue).
  3. Programmatically generate 500 *genuine* conflicting prompts by pairing two real edit instructions that contain antonymic targets (e.g., “add a tree” + “remove the tree”) and inserting an explicit temporal marker (“first … then …”).
  4. Assign deterministic UUIDs, copy the row‑level checksum, compute a placeholder `synthetic_score` (rule‑based feasibility heuristic), and write **`data/results/curated_prompts.csv`** with columns  
     `prompt_id, instruction_type, prompt_text, synthetic_score, checksum, human_score` (the `human_score` column is left **null** pending annotation).  
  *Verification*: Unit test `code/tests/test_curate.py` asserts (a) exact 500/500 class balance, (b) every `checksum` matches an entry in the manifest, and (c) `human_score` is null for all rows.

- [ ] T003 **[P2] [US‑2] Build the CPU‑only symbolic constraint‑graph parser** – implement `code/src/parser/graph_builder.py` using spaCy `en_core_web_sm` and NetworkX with rule‑based contradiction detection (antonym dictionary) and temporal‑marker heuristics. For each prompt in `curated_prompts.csv` output a JSON file `data/results/graphs/graph_<prompt_id>.json` conforming to the data‑model schema.  
  *Edge‑case handling*:
  - If no contradictions are detected, log a warning and emit a graph with an empty `edges` list.
  - If temporal order is ambiguous, add an edge labeled `no-order`.  
  *Verification*: `pytest code/tests/test_graph_builder.py` must pass; a full‑set run records total CPU time ≤ 30 min and peak RAM ≤ 7 GB in `data/results/parser_runtime.json` and `data/results/parser_ram.json`. The script must abort with a non‑zero exit if any GPU memory is allocated.

- [ ] T004 **[P1] [US‑1] Collect real human feasibility scores for **all 1 000** prompts** – implement `code/src/data/human_annotation.py` that:
  1. Presents each prompt to crowd‑workers (or internal annotators) via a configurable annotation interface.
  2. Collects ≥ 3 independent 0‑1 ratings per prompt, aggregates the mean, records the source (`annotation_source`) and `n_raters`.
  3. Writes `data/results/human_validation.csv` (`prompt_id, human_rating, annotation_source, n_raters`).
  4. Merges the aggregated rating back into `data/results/curated_prompts.csv` as the `human_score` column (overwrites the previous nulls).  
  *Verification*: The CSV contains exactly 1 000 rows, each with `n_raters ≥ 3` and a non‑null `human_score`. The pipeline raises an error if any `human_score` is missing or if a synthetic score is detected, thereby satisfying FR‑010.

- [ ] T005 **[P1] [US‑1] Run baseline verifier on a small subset** – implement `code/src/verifier/baseline.py` that:
  1. Loads the distilled Edit‑R1 1B verifier (`"llmXive/EditR1-1B"`) **on CPU** with 8‑bit quantization via bitsandbytes (`load_in_8bit=True`).
  2. Processes the first 50 prompts from `curated_prompts.csv` (25 conflicting, 25 neutral).
  3. Computes a 0‑1 feasibility score, calculates `alignment_delta = verifier_score – human_score`, and writes `data/results/baseline_subset_scores.csv`.  
  *Robustness*: Individual prompt timeouts or crashes are logged and the prompt is skipped without aborting the run.  
  *Verification*: ≥ 90 % of rows have non‑null `verifier_score`; `alignment_delta` is present for every row with both scores. Assert `model.device == "cpu"` and that 8‑bit quantization is active; any GPU allocation causes task failure.

- [ ] T006 **[P3] [US‑3] Run graph‑augmented verifier on the same subset and perform paired statistics** – implement `code/src/verifier/augmented.py` that:
  1. Loads the same CPU‑only 8‑bit Edit‑R1 1B model.
  2. For each of the 50 subset prompts, injects the corresponding JSON graph (`data/results/graphs/graph_<prompt_id>.json`) as additional context.
  3. Also runs two control conditions: `control_filler` (injects a dummy filler JSON) and `control_empty` (injects no extra context).
  4. Writes `data/results/augmented_subset_scores.csv` with columns `prompt_id, condition, verifier_score, human_score, alignment_delta`.  
  5. Executes `code/src/analysis/stats.py` on the subset to (a) perform a paired t‑test (or Wilcoxon if normality fails) between baseline and graph‑augmented `alignment_delta`, (b) compute Cohen’s d, 95 % CI, and (c) store results in `data/results/subset_stats.json`.  
  *Verification*: `subset_stats.json` contains `p_value`, `effect_size`, `ci_95`, and `corrected`. Unit test `code/tests/test_stats.py` validates calculations on a toy dataset. The verifier must again be confirmed CPU‑only 8‑bit.

---

## Phase 2 – Complete the study and validate its evidence  

*Goal*: Scale all components to the full 1 000‑prompt dataset, add robustness checks, and generate the contract‑compliant report.

- [ ] T007 **[P1] [US‑1] Run baseline verifier on the full dataset** – reuse `code/src/verifier/baseline.py` (CPU‑only 8‑bit) on all 1 000 prompts, writing `data/results/baseline_scores.csv`. Record wall‑clock time and peak RAM in `data/results/baseline_runtime.json`.  
  *Verification*: `baseline_runtime.json` reports `runtime_seconds ≤ 7200` (SC‑009) and `baseline_scores.csv` contains 1 000 rows (or documented skips). Confirm CPU‑only execution and 8‑bit quantization.

- [ ] T008 **[P2] [US‑2] Generate graphs for the full dataset and run graph‑augmented evaluation** – execute the parser (T003) on all 1 000 prompts (CPU, ≤ 30 min) producing JSON files under `data/results/graphs/`. Then run `code/src/verifier/augmented.py` for the three conditions (graph, filler, empty) on the full set, producing `data/results/augmented_scores.csv` (3 000 rows).  
  *Verification*: `augmented_scores.csv` has 3 000 rows with non‑null `verifier_score`. Parser runtime and RAM are logged in `parser_runtime.json` and `parser_ram.json` and respect the ≤ 30 min / ≤ 7 GB limits.

- [ ] T009 **[P3] [US‑3] Create and evaluate a re‑phrased hold‑out set** – using `code/src/data/conflict_generator.py`:
  1. Synthesize **100 new conflicting** prompts and **100 neutral** prompts with linguistic templates distinct from the primary set.
  2. Store them in `data/results/holdout_prompts.csv` with `instruction_type` labels.
  3. Collect real human feasibility scores for these 200 prompts via the same annotation pipeline, extending `human_validation.csv` and merging into `holdout_prompts.csv`.
  4. Parse the hold‑out prompts (T003) and evaluate both baseline and graph‑augmented conditions (CPU) to obtain `data/results/holdout_baseline_scores.csv` and `data/results/holdout_augmented_scores.csv`.
  5. Run `code/src/analysis/stats.py` on the hold‑out set and write `data/results/holdout_stats.json`.  
  *Verification*: All 200 hold‑out prompts have `human_score`; `holdout_stats.json` reports a non‑significant drop in effect size (p ≥ 0.05) as required by SC‑005.

- [ ] T010 **[P3] [US‑3] Perform full statistical analysis and emit the contract‑conformant report** – extend `code/src/analysis/stats.py` / `code/src/analysis/report.py` to:
  1. Run paired tests for (i) primary conflicting subset (baseline vs. graph), (ii) neutral subset (baseline vs. graph), (iii) graph vs. filler, (iv) graph vs. empty, and (v) hold‑out robustness.
  2. Apply Benjamini‑Hochberg correction across all hypotheses.
  3. Compute Pearson r between verifier scores (both baseline and graph‑augmented) and human scores; assert r ≥ 0.5 for each.
  4. Assemble `data/results/report.json` adhering to `specs/001-llmxive-verifier-graph/contracts/evaluation_report.schema.yaml`.
  5. Produce a supplementary `data/results/report.csv` with raw and corrected statistics.  
  *Verification*: `pytest code/tests/test_evaluation_report.py` validates the JSON against the schema; `report.json` records total pipeline runtime ≤ 6 h and peak RAM ≤ 7 GB. The Pearson‑r check must pass (≥ 0.5) or the task fails.

- [ ] T011 **[P3] Independent validation checks** – add a test suite `code/tests/validation/` that:
  a. Confirms all `alignment_delta` values match source CSVs.  
  b. Re‑runs the statistical analysis with both t‑test and Wilcoxon to ensure consistent conclusions.  
  c. Performs a power analysis for n = 500 conflicting pairs, expected d = 0.5, α = 0.05 and records achieved power in `data/results/validation_checks.json`.  
  d. Asserts success‑criteria thresholds: Pearson r ≥ 0.5 (SC‑007), Cohen’s d ≥ 0.5 for the primary improvement (SC‑008).  
  e. Checks parser runtime ≤ 30 min, overall pipeline ≤ 6 h, RAM ≤ 7 GB.  
  *Verification*: All pytest checks pass; `validation_checks.json` contains boolean pass/fail fields for each criterion.

- [ ] T012 **[P3] Generate figures and summary tables** – implement `code/src/analysis/visualize.py` to create:
  * `figures/fig1_baseline_alignment.png` – distribution of alignment scores for conflicting vs. neutral prompts (baseline).  
  * `figures/fig2_augmented_vs_baseline.png` – paired delta plot across conditions.  
  * `figures/fig3_effect_sizes.png` – primary vs. hold‑out effect sizes with 95 % CIs.  
  * `data/results/summary_table.csv` – mean ± SD alignment per condition, p‑values, effect sizes, Pearson r, and pass flags for SC‑007/SC‑008.  
  All visualizations read directly from the CSV/JSON result artifacts; the script uses a fixed random seed and deterministic matplotlib style.  
  *Verification*: Re‑running `visualize.py` after any upstream change yields byte‑identical PNGs and an unchanged `summary_table.csv`.

---

## Phase 3 – Reproducible results and paper handoff  

*Goal*: Document the full workflow for external replication and provide the handoff artifacts for the downstream paper pipeline.

- [ ] T013 **[P1] Write the methods‑results manuscript** – create `specs/001-llmxive-verifier-graph/research.md` that narrates:
  * Dataset construction (balanced 1 000 prompts, human annotation of all prompts).  
  * Symbolic parser design and edge‑case handling.  
  * Verifier configuration (CPU‑only 8‑bit Edit‑R1 1B).  
  * Statistical methodology (paired tests, correction, robustness hold‑out, power analysis).  
  * Quantitative results (mean ± SD alignment, effect sizes, p‑values, Pearson r) with explicit citations to artifact paths (e.g., “mean baseline alignment = 0.42 ± 0.12 (see `data/results/baseline_summary.json` line 23)”).  
  * Discussion of failure modes, null‑graph rate, skipped prompts, and whether SC‑001 – SC‑010 were met.  
  *Verification*: `code/src/verification/link_check.py` parses `research.md` and confirms each cited artifact exists and contains the referenced fields.

- [ ] T014 **[P1] Write the reproducibility quick‑start guide** – update `specs/001-llmxive-verifier-graph/quickstart.md` with the exact command sequence to reproduce the entire study from a clean checkout (see the block below). Add a CI step that runs this sequence on a fresh runner, asserts zero‑non‑zero exit codes, validates `data/results/report.json` against the schema, checks that all figures/tables are byte‑identical to the committed versions, and confirms the end‑to‑end script exits successfully.

  ```bash
  # 1️⃣ Download raw data
  python -m code.src.data.download

  # 2️⃣ Curate balanced CSV
  python -m code.src.data.curate

  # 3️⃣ Collect human scores (requires access to the annotation platform)
  python -m code.src.data.human_annotation

  # 4️⃣ Build constraint graphs (CPU only)
  python -m code.src.parser.graph_builder

  # 5️⃣ Baseline verifier (CPU‑only 8‑bit)
  python -m code.src.verifier.baseline

  # 6️⃣ Graph‑augmented verifier + controls (CPU‑only 8‑bit)
  python -m code.src.verifier.augmented

  # 7️⃣ Hold‑out robustness set
  python -m code.src.data.conflict_generator --holdout 200
  python -m code.src.verifier.baseline --subset holdout
  python -m code.src.verifier.augmented --subset holdout

  # 8️⃣ Full statistical analysis & report
  python -m code.src.analysis.report

  # 9️⃣ Validate everything
  pytest
  ```

- [ ] T015 **[P1] Paper‑stage handoff manifest** – create `specs/001-llmxive-verifier-graph/handoff.yaml` listing every artifact required by the downstream paper pipeline:

  ```yaml
  data:
    - data/results/report.json
    - data/results/summary_table.csv
  figures:
    - figures/fig1_baseline_alignment.png
    - figures/fig2_augmented_vs_baseline.png
    - figures/fig3_effect_sizes.png
  manuscript:
    - specs/001-llmxive-verifier-graph/research.md
  ```

  *Verification*: A CI step runs a short Python snippet that loads the YAML and checks that each listed path exists on disk.

---  

### Dependency & Requirement Coverage

| Spec Requirement | Task(s) | Produced Artifact |
|------------------|---------|-------------------|
| FR‑001 (balanced prompts + human scores ≥ 200) | T001, T002, T004 | `data/results/curated_prompts.csv` (1 000 prompts, all with human scores) |
| FR‑009 (human scores ≥ 200) – satisfied by the 1 000 scores | T004 | `data/results/human_validation.csv` |
| FR‑002 (CPU‑only symbolic parser) | T003, T008 | `data/results/graphs/*.json` |
| FR‑003 (baseline verifier) | T005, T007 | `data/results/baseline_*.csv` |
| FR‑004 (graph‑augmented verifier) | T006, T008 | `data/results/augmented_*.csv` |
| FR‑005 (paired statistical test) | T006, T010 | `data/results/report.json` |
| FR‑006 (robustness hold‑out) | T009, T010 | `data/results/holdout_stats.json` |
| FR‑007 (multiple‑comparison correction) | T010 | `report.json` |
| FR‑008 (runtime ≤ 6 h, RAM ≤ 7 GB) | T003, T007, T010, T011 | `validation_checks.json` |
| FR‑010 (no synthetic scores in evaluation) | T002, T004, T010 | `curated_prompts.csv` (human_score only) |
| SC‑001 – SC‑010 | T007‑T012 | various result CSV/JSON files, figures, summary table |

All tasks respect the **compute‑feasibility rule** (CPU‑only parsing, CPU‑only 8‑bit inference; if a GPU is needed the platform will automatically off‑load a real GPU run). No synthetic data are used for evaluation, and every failure mode described in the specification is explicitly handled.
