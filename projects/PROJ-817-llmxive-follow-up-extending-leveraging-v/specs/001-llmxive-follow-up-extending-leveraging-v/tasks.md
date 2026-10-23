# Tasks: Does a symbolic constraint‑graph preprocessing module mitigate verifier degradation on conflicting image‑editing instructions?

**Inputs**: `specs/001-llmxive-verifier-graph/spec.md`, `plan.md`, data model, `evaluation_report.schema.yaml`, original research idea and validation report.

This research implementation plan follows the specification and addresses all functional requirements (FR‑001 – FR‑010) and success criteria (SC‑001 – SC‑010). Tasks are ordered to respect data flow and runtime constraints. All paths are project‑relative and write only under `data/`, `figures/`, `code/`, or `specs/`.

---

## Phase 1 – Setup and first end‑to‑end analysis  

*Goal*: Verify that a thin pipeline runs on real data (download → curation → human annotation → parser → verifier → statistics) before scaling.

- [ ] T001 [US‑1] **Download raw instruction data** – implement `code/src/data/download.py` that streams the verified InstructPix2Pix dataset via   <!-- FAILED-IN-EXECUTION: code/src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/data/download.py exit=1 -->
  ```python
  from datasets import load_dataset
  ds = load_dataset("timbrooks/instructpix2pix", split="train", streaming=True)
  ```  
  For each row compute a SHA‑256 checksum, write the first 2 000 rows to `data/raw/prompts_sample.parquet`, and simultaneously generate `data/raw/checksums_manifest.json`. The script **must raise** on any fetch error; no synthetic fallback is permitted.  
  *Verification*: Run `python -m code.src.data.download`; confirm the parquet file exists, contains ≥ 2 000 rows, each row has a non‑null `prompt` and a matching checksum entry in the manifest. The script must exit with non‑zero status on failure.

- [ ] T002 [US‑1] **Curate a balanced 1 000‑prompt CSV** – implement `code/src/data/curate.py` and `code/src/data/conflict_generator.py` to (a) select 500 neutral prompts from the raw sample, (b) construct 500 conflicting prompts by compositing two real edit instructions with antonymic attribute targets and explicit temporal phrasing, (c) assign deterministic UUIDs, (d) write `data/results/curated_prompts.csv` with columns `prompt_id, instruction_type, prompt_text, synthetic_score, human_score, checksum` (human_score left **null** pending annotation).  
  *Verification*: Unit test `code/tests/test_curate.py` checks class balance (500/500), checksum provenance, and that `human_score` is null for all rows.

- [ ] T003 [US‑2] **Build the CPU‑only symbolic constraint‑graph parser** – implement `code/src/parser/graph_builder.py` using spaCy `en_core_web_sm` and networkx with rule‑based contradiction detection (antonym matching). For each prompt, output a JSON graph conforming to the data model at `data/results/graphs/graph_<prompt_id>.json`. Handle edge cases: missing contradictions → log warning and emit a null graph; ambiguous temporal order → add a `no-order` edge.  
  *Verification*: `pytest code/tests/test_graph_builder.py` must pass, the full‑set run must record total CPU time ≤ 30 min in `data/results/parser_runtime.json`, **and** record peak RAM via `psutil` in `data/results/parser_ram.json` and fail if > 7 GB. No GPU memory may be allocated.

- [ ] T004 [US‑1] **Collect real human feasibility scores for all 1 000 prompts** – implement `code/src/data/human_annotation.py` that presents each prompt to crowd workers (or internal annotators), records ≥ 3 independent 0‑1 ratings, aggregates the mean, and writes `data/results/human_validation.csv` with columns `prompt_id, human_rating, annotation_source, n_raters`. Merge the aggregated rating back into `data/results/curated_prompts.csv` as the `human_score` field (overwrites the nulls).  
  *Verification*: The CSV must contain 1 000 rows, each with `n_raters ≥ 3` and a non‑null `human_score`. The pipeline must raise if any `human_score` is missing or was generated synthetically (FR‑010). **Note:** This task deliberately exceeds the minimum of ≥ 200 scores required by FR‑009 to enable a paired analysis; the extra annotation effort is justified in the experimental design.

- [ ] T005 [US‑1] **Run baseline verifier on a small subset** – implement `code/src/verifier/baseline.py` that loads the pinned model `Qwen/Qwen2.5-1.5B-Instruct` **on CPU** with 8‑bit quantization (e.g., `bitsandbytes` `load_in_8bit=True`). Process the first 50 curated prompts (25 conflicting, 25 neutral). Compute a 0‑1 feasibility score per prompt, calculate `alignment_delta = verifier_score − human_score`, and write `data/results/baseline_subset_scores.csv`. Errors or timeouts for individual prompts must be logged and skipped without aborting the run.  
  *Verification*: At least 90 % of rows have non‑null `verifier_score`; `alignment_delta` is present for all rows with both scores. Additionally, a verification step asserts `model.device == "cpu"` and that 8‑bit quantization is active; any GPU allocation causes the task to fail.

- [ ] T006 [US‑3] **Run graph‑augmented verifier on the same subset and perform paired statistics** – implement `code/src/verifier/augmented.py` that loads the same CPU‑only 8‑bit model, injects the JSON graph from `data/results/graphs/graph_<prompt_id>.json` as additional context, and also runs two control conditions (`control_filler` and `control_empty`). Output `data/results/augmented_subset_scores.csv` with a `condition` column. Then run `code/src/analysis/stats.py` on the subset to (a) perform a paired t‑test (or Wilcoxon if normality fails) between baseline and graph‑augmented alignment deltas, (b) compute Cohen’s d, 95 % CI, and (c) log the results in `data/results/subset_stats.json`.  
  *Verification*: The statistical script must produce a p‑value, effect size, and CI; unit test `code/tests/test_stats.py` validates the calculations on a hand‑crafted toy dataset. The verifier must again be confirmed CPU‑only 8‑bit.

*Checkpoint*: Executing `python -m code.src.cli.run_all --subset 50` completes end‑to‑end, producing the CSV/JSON artifacts above with real model outputs and human scores.

---

## Phase 2 – Complete the study and validate its evidence  

*Goal*: Scale all components to the full 1 000‑prompt dataset, add robustness checks, and generate the contract‑compliant report.

- [ ] T007 [US‑1] **Run baseline verifier on the full dataset** – reuse `code/src/verifier/baseline.py` (CPU‑only 8‑bit) on all 1 000 prompts, writing `data/results/baseline_scores.csv`. Record wall‑clock runtime and peak RAM in `data/results/baseline_runtime.json`; assert total CPU time ≤ 2 h (SC‑009) and that the CSV contains a row for every prompt (or a logged skip).  
  *Verification*: The runtime file reports `runtime_seconds ≤ 7200`; the CSV has 1 000 rows (or documented skips). Verify CPU‑only execution and 8‑bit quantization as in T005.

- [ ] T008 [US‑2] **Generate graphs for the full dataset and run graph‑augmented evaluation** – execute the parser (T003) on all prompts (CPU, ≤ 30 min) to produce JSON files. Then run `code/src/verifier/augmented.py` for all three conditions (graph, filler, empty) on the full set, producing `data/results/augmented_scores.csv` (three rows per prompt).  
  *Verification*: `augmented_scores.csv` contains 3 000 rows, each with non‑null `verifier_score`; parser runtime logged ≤ 30 min and peak RAM ≤ 7 GB (as recorded in `data/results/parser_runtime.json` and `parser_ram.json`).

- [ ] T009 [US‑3] **Create and evaluate a re‑phrased hold‑out conflict set** – using `code/src/data/conflict_generator.py`, synthesize 100 *new* conflicting prompts with linguistic templates distinct from the primary set, store them in `data/results/holdout_prompts.csv`. Collect real human feasibility scores for these 100 prompts via the same annotation pipeline (adds to `human_validation.csv` and merges into the hold‑out CSV). Parse them (T003) and evaluate both baseline and graph‑augmented conditions (CPU) to obtain `data/results/holdout_baseline_scores.csv` and `data/results/holdout_augmented_scores.csv`. Compute the effect size for the hold‑out set with `code/src/analysis/stats.py` and write `data/results/holdout_stats.json`.  
  *Verification*: All 100 hold‑out prompts have `human_score`; the effect‑size comparison reports a non‑significant drop (p ≥ 0.05) per SC‑005.

- [ ] T010 [US‑3] **Perform full statistical analysis and emit the contract‑conformant report** – extend `code/src/analysis/stats.py` / `code/src/analysis/report.py` to (a) run paired tests for (i) primary conflict subset (baseline vs. graph), (ii) neutral subset (baseline vs. graph), (iii) graph vs. filler, (iv) graph vs. empty, (v) hold‑out robustness, (b) apply Benjamini‑Hochberg correction across all hypotheses, (c) compute **Pearson r** between verifier scores (both conditions) and human scores and verify r ≥ 0.5, (d) assemble `data/results/report.json` adhering to `specs/001-llmxive-verifier-graph/contracts/evaluation_report.schema.yaml`, and (e) produce a supplementary `data/results/report.csv` with every test’s raw and corrected statistics.  
  *Verification*: `pytest code/tests/test_evaluation_report.py` validates the JSON against the schema; the CSV contains rows for all tests; total pipeline runtime ≤ 6 h and peak RAM ≤ 7 GB (recorded in `report.json`). The Pearson correlation check must pass (≥ 0.5) or the task fails.

- [ ] T011 [US‑3] **Run independent validation checks** – add a test suite `code/tests/validation/` that (a) confirms all alignment‑delta calculations match the source CSVs, (b) repeats the statistical analysis with both t‑test and Wilcoxon to ensure consistent conclusions, (c) performs a power analysis for n = 500 conflicting pairs, d = 0.5, α = 0.05 and records achieved power in `data/results/validation_checks.json`, (d) asserts the success‑criteria thresholds: Pearson r ≥ 0.5 for both baseline and graph (SC‑007) and Cohen’s d ≥ 0.5 for the primary improvement (SC‑008), (e) checks that parser runtime ≤ 30 min and overall pipeline ≤ 6 h, RAM ≤ 7 GB.  
  *Verification*: All pytest checks pass; `validation_checks.json` contains boolean pass/fail fields for each criterion.

- [ ] T012 [US‑3] **Generate figures and summary tables** – implement `code/src/analysis/visualize.py` to create:  
  * `figures/fig1_baseline_alignment.png` – distribution of alignment scores for conflicting vs. neutral prompts (baseline).  
  * `figures/fig2_augmented_vs_baseline.png` – paired delta plot across conditions.  
  * `figures/fig3_effect_sizes.png` – primary vs. hold‑out effect sizes with 95 % CIs.  
  * `data/results/summary_table.csv` – mean ± SD alignment per condition, p‑values, effect sizes, Pearson r, and SC‑007/SC‑008 pass flags.  
  All numbers are read directly from the CSV/JSON result artifacts; figure generation is deterministic (fixed random seed, matplotlib style).  
  *Verification*: Re‑running the visualization script after any upstream change yields byte‑identical PNGs and CSV rows.

---

## Phase 3 – Reproducible results and paper handoff  

*Goal*: Document the full workflow for external replication and provide the handoff artifacts for the paper pipeline.

- [ ] T013 [US‑1] **Write the methods‑results manuscript** – create `specs/001-llmxive-verifier-graph/research.md` that narrates the experimental design, dataset construction, parser implementation, verifier configurations, statistical methodology, and results. Every quantitative statement must cite a concrete artifact path (e.g., “mean baseline alignment = 0.42 ± 0.12 (see `data/results/baseline_summary.json` line 23)”). Include discussion of failure modes, null‑graph rate, skipped prompts, power limitations, and whether the success‑criteria thresholds were met.  
  *Verification*: A script `code/src/verification/link_check.py` parses `research.md` and confirms that each cited artifact exists and contains the referenced fields.

- [ ] T014 [US‑1] **Write the reproducibility quick‑start guide** – update `specs/001-llmxive-verifier-graph/quickstart.md` with the exact command sequence to reproduce the entire study from a clean checkout (see below). Add a CI step that runs this full sequence on a fresh runner and asserts zero‑non‑zero exit codes.  
  *Verification*: A fresh run on a clean runner reproduces `data/results/report.json` that validates against the schema, all figures/tables match the committed versions (byte‑identical), and the end‑to‑end script exits successfully.

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
  python -m code.src.data.conflict_generator --holdout 100
  python -m code.src.verifier.baseline --subset holdout
  python -m code.src.verifier.augmented --subset holdout

  # 8️⃣ Full statistical analysis & report
  python -m code.src.analysis.report

  # 9️⃣ Validate everything
  pytest
  ```

- [ ] T015 [US‑1] **Paper‑stage handoff manifest** – create `specs/001-llmxive-verifier-graph/handoff.yaml` listing the exact artifacts required by the downstream paper pipeline:

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

| Spec Requirement | Task(s) | Artifact |
|------------------|---------|----------|
| FR‑001 (balanced 1 000 prompts) | T001, T002 | `data/results/curated_prompts.csv` |
| FR‑009 (human scores) – resolved to **all 1 000** | T004 | `data/results/human_validation.csv` |
| FR‑002 (CPU‑only symbolic parser) | T003, T008 | `data/results/graphs/*.json` |
| FR‑003 (baseline verifier) | T005, T007 | `data/results/baseline_*.csv` |
| FR‑004 (graph‑augmented verifier) | T006, T008 | `data/results/augmented_*.csv` |
| FR‑005 (paired statistical test) | T006, T010 | `data/results/report.json` |
| FR‑006 (robustness hold‑out) | T009, T010 | `data/results/holdout_stats.json` |
| FR‑007 (multiple‑comparison correction) | T010 | `report.json` |
| FR‑008 (runtime ≤ 6 h, RAM ≤ 7 GB) | T003, T007, T010, T011 | `validation_checks.json` |
| FR‑010 (no synthetic scores in evaluation) | T002, T004, T010 | `curated_prompts.csv` (human_score only) |
| SC‑001 – SC‑010 | T007‑T012 | various result CSV/JSON files, figures |

All tasks respect the **compute feasibility rule**: only the verifier inference uses a real GPU‑offload mechanism **only when the runner lacks CUDA**; otherwise they run CPU‑only 8‑bit as mandated. No synthetic data are used for evaluation, and every failure mode described in the specification (null graphs, verifier crashes, ambiguous temporality) is explicitly handled.
