# Tasks: Does a symbolic constraint‑graph preprocessing module mitigate verifier degradation on conflicting image‑editing instructions?

**Inputs**: `specs/001-llmxive-verifier-graph/spec.md`, `plan.md`, data model, `evaluation_report.schema.yaml`, original research idea and validation report.

This implementation plan satisfies all functional requirements (FR‑001 – FR‑010) and success criteria (SC‑001 – SC‑010). Tasks are ordered to respect data flow, runtime, and memory constraints. Paths are project‑relative and write only under `data/`, `figures/`, `code/`, or `specs/`.

---

## Phase 1 – Setup and first end‑to‑end analysis  

*Goal*: Verify that a thin pipeline runs on real data (download → curation → human annotation → parser → verifier → statistics) before scaling.

- [ ] T001 **[P1] [US‑1] Download raw instruction data** – implement `code/src/data/download.py` that streams the verified InstructPix2Pix dataset via `datasets.load_dataset("timbrooks/instructpix2pix", split="train", streaming=True)`. For each row compute a SHA‑256 checksum, write the first 2 000 rows to `data/raw/prompts_sample.parquet`, and create `data/raw/checksums_manifest.json`.   <!-- FAILED-IN-EXECUTION: code/src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/data/download.py exit=1 -->
  *Verification*: Run `python -m code.src.data.download`; confirm the parquet file exists, contains ≥ 2 000 rows, each row has a non‑null `prompt`, and the manifest lists matching checksums. The script must raise on any fetch error; no synthetic fallback is permitted.

- [ ] T002 **[P1] [US‑1] Curate a balanced 1 000‑prompt CSV** – implement `code/src/data/curate.py` (and helper `code/src/data/conflict_generator.py`) to:  
  1. Select 500 neutral prompts from the raw sample.  
  2. Construct 500 **genuine conflicting** prompts by pairing two real edit instructions that contain antonymic attribute targets using an antonym dictionary (e.g., “make the sky blue” + “keep the sky dark”) and inserting an explicit temporal cue (“first … then …”).  
  3. Assign deterministic UUIDs, compute checksums, and write **to `data/results/curated_prompts.csv`** with columns `prompt_id, instruction_type, prompt_text, synthetic_score, human_score, checksum` (the `human_score` column is left **null** pending annotation).  
  *Verification*: Unit test `code/tests/test_curate.py` checks (a) exact 500/500 class balance, (b) that every row’s `checksum` matches the raw source, and (c) that `human_score` is null for all rows.

- [ ] T003 **[P2] [US‑2] Build the CPU‑only symbolic constraint‑graph parser** – implement `code/src/parser/graph_builder.py` using spaCy `en_core_web_sm` and NetworkX with rule‑based contradiction detection via an antonym dictionary and temporal‑marker heuristics. For each prompt output a JSON graph conforming to the data model at `data/results/graphs/graph_<prompt_id>.json`.  
  *Edge‑case handling*:  
  - No contradictions found → log a warning and emit a JSON with an empty `edges` list (`null` graph).  
  - Ambiguous temporal order → add an edge labeled `no-order`.  
  *Verification*: `pytest code/tests/test_graph_builder.py` must pass; a full‑set run must record total CPU time ≤ 30 min in `data/results/parser_runtime.json` and peak RAM ≤ 7 GB in `data/results/parser_ram.json`. The script must exit with non‑zero status if GPU memory is allocated.

- [ ] T004 **[P1] [US‑1] Collect real human feasibility scores for **all 1 000** prompts** – implement `code/src/data/human_annotation.py` that presents each prompt to crowd workers (or internal annotators), records ≥ 3 independent 0‑1 ratings, aggregates the mean, and writes `data/results/human_validation.csv` (`prompt_id, human_rating, annotation_source, n_raters`). Merge the aggregated rating back into `data/results/curated_prompts.csv` as the `human_score` field (overwrites the nulls).  
  *Verification*: The CSV must contain exactly 1 000 rows, each with `n_raters ≥ 3` and a non‑null `human_score`. The pipeline must raise if any `human_score` is missing or if a synthetic score is detected (enforcing FR‑010).

- [ ] T005 **[P1] [US‑1] Run baseline verifier on a small subset** – implement `code/src/verifier/baseline.py` that loads the **distilled Edit‑R1 1B** verifier (`"llmXive/EditR1-1B"`) **on CPU** with 8‑bit quantization (`bitsandbytes` `load_in_8bit=True`). Process the first 50 curated prompts (25 conflicting, 25 neutral), compute a 0‑1 feasibility score per prompt, calculate `alignment_delta = verifier_score − human_score`, and write `data/results/baseline_subset_scores.csv`. Errors or timeouts for individual prompts must be logged and skipped without aborting the run.  
  *Verification*: ≥ 90 % of rows have non‑null `verifier_score`; `alignment_delta` present for all rows with both scores. Assert `model.device == "cpu"` and that 8‑bit quantization is active; any GPU allocation causes task failure.

- [ ] T006 **[P3] [US‑3] Run graph‑augmented verifier on the same subset and perform paired statistics** – implement `code/src/verifier/augmented.py` that loads the same CPU‑only 8‑bit Edit‑R1 1B model, injects the JSON graph from `data/results/graphs/graph_<prompt_id>.json` as additional context, and also runs two control conditions (`control_filler` and `control_empty`). Output `data/results/augmented_subset_scores.csv` with a `condition` column. Then run `code/src/analysis/stats.py` on the subset to (a) perform a paired t‑test (or Wilcoxon if normality fails) between baseline and graph‑augmented alignment deltas, (b) compute Cohen’s d, 95 % CI, and (c) log the results in `data/results/subset_stats.json`.  
  *Verification*: The statistical script must produce a JSON containing `p_value`, `effect_size`, `ci_95`, and a boolean `corrected`. Unit test `code/tests/test_stats.py` validates the calculations on a hand‑crafted toy dataset. The verifier must again be confirmed CPU‑only 8‑bit.

## Phase 2 – Complete the study and validate its evidence  

*Goal*: Scale all components to the full 1 000‑prompt dataset, add robustness checks, and generate the contract‑compliant report.

- [ ] T007 **[P1] [US‑1] Run baseline verifier on the full dataset** – reuse `code/src/verifier/baseline.py` (CPU‑only 8‑bit Edit‑R1 1B) on all 1 000 prompts, writing `data/results/baseline_scores.csv`. Record wall‑clock runtime and peak RAM in `data/results/baseline_runtime.json`; assert total CPU time ≤ 2 h (SC‑009) and that the CSV contains a row for every prompt (or a documented skip).  
  *Verification*: `baseline_runtime.json` reports `runtime_seconds ≤ 7200`; `baseline_scores.csv` has 1 000 rows. Verify CPU‑only execution and 8‑bit quantization.

- [ ] T008 **[P2] [US‑2] Generate graphs for the full dataset and run graph‑augmented evaluation** – execute the parser (T003) on all prompts (CPU, ≤ 30 min) to produce JSON files. Then run `code/src/verifier/augmented.py` for all three conditions (graph, filler, empty) on the full set, producing `data/results/augmented_scores.csv` (three rows per prompt).  
  *Verification*: `augmented_scores.csv` contains 3 000 rows, each with non‑null `verifier_score`; parser runtime logged ≤ 30 min and peak RAM ≤ 7 GB (as recorded in `parser_runtime.json` and `parser_ram.json`).

- [ ] T009 **[P3] [US‑3] Create and evaluate a re‑phrased hold‑out set** – using `code/src/data/conflict_generator.py`, synthesize **100 new conflicting** prompts **and 100 neutral** prompts with linguistic templates distinct from the primary set, store them in `data/results/holdout_prompts.csv` with `instruction_type` labels. Collect real human feasibility scores for these 200 prompts via the same annotation pipeline (adds to `human_validation.csv` and merges into `holdout_prompts.csv`). Parse them (T003) and evaluate both baseline and graph‑augmented conditions (CPU) to obtain `data/results/holdout_baseline_scores.csv` and `data/results/holdout_augmented_scores.csv`. Compute the effect size for the hold‑out set with `code/src/analysis/stats.py` and write `data/results/holdout_stats.json`.  
  *Verification*: All 200 hold‑out prompts have `human_score`; the effect‑size comparison reports a non‑significant drop (p ≥ 0.05) per SC‑005.

- [ ] T010 **[P3] [US‑3] Perform full statistical analysis and emit the contract‑conformant report** – extend `code/src/analysis/stats.py` / `code/src/analysis/report.py` to:  
  1. Run paired tests for (i) primary conflicting subset (baseline vs. graph), (ii) neutral subset (baseline vs. graph), (iii) graph vs. filler, (iv) graph vs. empty, (v) hold‑out robustness.  
  2. Apply Benjamini‑Hochberg correction across all hypotheses.  
  3. Compute Pearson r between verifier scores (both baseline and graph‑augmented) and human scores; assert r ≥ 0.5 for both.  
  4. Assemble `data/results/report.json` adhering to `specs/001-llmxive-verifier-graph/contracts/evaluation_report.schema.yaml`.  
  5. Produce a supplementary `data/results/report.csv` with raw and corrected statistics.  
  *Verification*: `pytest code/tests/test_evaluation_report.py` validates the JSON against the schema; `report.json` records total pipeline runtime ≤ 6 h and peak RAM ≤ 7 GB. The Pearson correlation check must pass (≥ 0.5) or the task fails.

- [ ] T011 **[P3] [US‑3] Independent validation checks** – add a test suite `code/tests/validation/` that:  
  a. Confirms all `alignment_delta` calculations match source CSVs.  
  b. Repeats the statistical analysis with both t‑test and Wilcoxon to ensure consistent conclusions.  
  c. Performs a power analysis for n = 500 conflicting pairs, d = 0.5, α = 0.05 and records achieved power in `data/results/validation_checks.json`.  
  d. Asserts success‑criteria thresholds: Pearson r ≥ 0.5 for both baseline and graph (SC‑007) and Cohen’s d ≥ 0.5 for the primary improvement (SC‑008).  
  e. Checks parser runtime ≤ 30 min, overall pipeline ≤ 6 h, RAM ≤ 7 GB.  
  *Verification*: All pytest checks pass; `validation_checks.json` contains boolean pass/fail fields for each criterion.

- [ ] T012 **[P3] Generate figures and summary tables** – implement `code/src/analysis/visualize.py` to create:  
  * `figures/fig1_baseline_alignment.png` – distribution of alignment scores for conflicting vs. neutral prompts (baseline).  
  * `figures/fig2_augmented_vs_baseline.png` – paired delta plot across conditions.  
  * `figures/fig3_effect_sizes.png` – primary vs. hold‑out effect sizes with 95 % CIs.  
  * `data/results/summary_table.csv` – mean ± SD alignment per condition, p‑values, effect sizes, Pearson r, and SC‑007/SC‑008 pass flags.  
  All numbers are read directly from the CSV/JSON result artifacts; figure generation is deterministic (fixed random seed, matplotlib style).  
  *Verification*: Re‑running the visualization script after any upstream change yields byte‑identical PNGs and CSV rows.

## Phase 3 – Reproducible results and paper handoff  

*Goal*: Document the full workflow for external replication and provide the handoff artifacts for the paper pipeline.

- [ ] T013 **[P1] Write the methods‑results manuscript** – create `specs/001-llmxive-verifier-graph/research.md` that narrates the experimental design, dataset construction, parser implementation, verifier configurations, statistical methodology, and results. Every quantitative statement must cite a concrete artifact path (e.g., “mean baseline alignment = 0.42 ± 0.12 (see `data/results/baseline_summary.json` line 23)”). Include discussion of failure modes, null‑graph rate, skipped prompts, power limitations, and whether the success‑criteria thresholds were met.  
  *Verification*: `code/src/verification/link_check.py` parses `research.md` and confirms each cited artifact exists and contains the referenced fields.

- [ ] T014 **[P1] Write the reproducibility quick‑start guide** – update `specs/001-llmxive-verifier-graph/quickstart.md` with the exact command sequence to reproduce the entire study from a clean checkout, and add a CI step that runs this sequence on a fresh runner, asserting zero‑non‑zero exit codes and that `data/results/report.json` validates against the schema, all figures/tables match the committed versions (byte‑identical), and the end‑to‑end script exits successfully.  

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

- [ ] T015 **[P1] Paper‑stage handoff manifest** – create `specs/001-llmxive-verifier-graph/handoff.yaml` listing the exact artifacts required by the downstream paper pipeline:

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

  *Verification*: A CI step runs `python -c "import yaml, sys; yaml.safe_load(open('specs/001-llmxive-verifier-graph/handoff.yaml'))"` and checks that every listed path exists.

---


### Dependency & Requirement Coverage

| Spec Requirement | Task(s) | Produced Artifact |
|------------------|---------|-------------------|
| FR‑001 (balanced 1 000 prompts) | T001, T002 | `data/results/curated_prompts.csv` |
| FR‑009 (≥ 200 human scores) – satisfied by collecting **all 1 000** | T004 | `data/results/human_validation.csv` |
| FR‑002 (CPU‑only symbolic parser) | T003, T008 | `data/results/graphs/*.json` |
| FR‑003 (baseline verifier) | T005, T007 | `data/results/baseline_*.csv` |
| FR‑004 (graph‑augmented verifier) | T006, T008 | `data/results/augmented_*.csv` |
| FR‑005 (paired statistical test) | T006, T010 | `data/results/report.json` |
| FR‑006 (robustness hold‑out) | T009, T010 | `data/results/holdout_stats.json` |
| FR‑007 (multiple‑comparison correction) | T010 | `report.json` |
| FR‑008 (runtime ≤ 6 h, RAM ≤ 7 GB) | T003, T007, T010, T011 | `validation_checks.json` |
| FR‑010 (no synthetic scores in evaluation) | T002, T004, T010 | `curated_prompts.csv` (human_score only) |
| SC‑001 – SC‑010 | T007‑T012 | various result CSV/JSON files, figures |

All tasks respect the **compute‑feasibility rule**: only the verifier inference uses a real model (CPU‑only 8‑bit; if the runner lacks CUDA the platform will off‑load to a free Kaggle GPU automatically). No synthetic data are used for evaluation, and every failure mode described in the specification is explicitly handled.  
