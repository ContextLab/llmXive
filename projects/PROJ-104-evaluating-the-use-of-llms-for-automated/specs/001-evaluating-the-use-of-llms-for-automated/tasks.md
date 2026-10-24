# Tasks: Evaluating LLM Fidelity in Commit-to-Documentation Translation

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-evaluating-the-use-of-llms-for-automated/contracts/`, and any reviewer feedback.

The goal is to deliver a fully reproducible, end‑to‑end pipeline that satisfies every functional and non‑functional requirement in the specification while providing an early executable result that can be run on a minimal subset of the data.

---

## Phase 0 – Project scaffolding & sanity check

- [X] T001 [US1] **Create quick‑start documentation and a minimal runnable entry point** – `docs/quickstart.md`, `code/run_pipeline.py`  
  - Write a “Getting started” guide that lists required Python 3.11 packages, how to install `bitsandbytes` and `transformers`, and the command `python -m code.run_pipeline --sample 5`.  
  - Implement `run_pipeline` to load a tiny hard‑coded commit pair (synthetic smoke‑test only) and invoke the generation module (CPU‑only) to produce a single output file under `data/generated/phi3-mini/sample_test.txt`.  
  - **Verification**: Running the command completes in < 30 s, creates the output file, and `pytest tests/test_quickstart.py` passes.

- [X] T002 [P] [US1] **Monte‑Carlo power analysis for the Friedman test** – `code/power_analysis.py`, `results/power_report.md`  
  - Simulate paired precision scores for three models under varying effect sizes (seeded with `code/seeds.py`).  
  - Estimate power for n = 500 with a medium effect (Cohen’s f = 0.25).  
  - Write `results/power_report.md` containing the numeric power estimate and an `exploratory: true` flag if power < 0.8.  
  - **Verification**: Test asserts that the file exists, contains a numeric power estimate, and that the `exploratory` flag matches the computed power.

- [ ] T013 **Data hygiene (checksums) and reproducibility (pinned seeds) utilities** – `code/data_hygiene.py`, `code/seeds.py`, `data/metadata.yaml`, `tests/test_hygiene_and_seeds.py`  
  - `data_hygiene.py` computes SHA‑256 checksums for every file under `data/` after it is written and records them in `data/metadata.yaml` with provenance notes. Enforce that raw files are never overwritten; each transformation writes a new file with a distinct name.  
  - `seeds.py` defines a global seed `SEED = 42`; all stochastic components import this seed. Document the seed policy in `docs/quickstart.md`.  
  - **Verification**: Test asserts that each file under `data/` has a matching checksum entry, that raw files retain their original checksum across runs, and that `SEED` is imported by every stochastic script; re‑running T002 twice yields identical power estimates.  

---

## Phase 1 – Data acquisition & pairing (User Story 1)

- [ ] T003 [P1] [US1] **Extract ≥ 500 (commit_message, documentation_diff) pairs from the five target repositories** – `code/data_extraction.py`, `data/raw/commit_pairs.csv`   <!-- FAILED-IN-EXECUTION: code/data_extraction.py exit=1 -->
  - Clone the repositories `pandas`, `requests`, `scikit-learn`, `flask`, `django` into `data/tmp/repos/`.  
  - Use the GitHub REST API (`GET /repos/{owner}/{repo}/commits`) with `since=2 years ago`, handling pagination and rate‑limit retries, and a personal‑access‑token supplied via `GITHUB_TOKEN` (fails loudly if missing).  
  - For each commit, fetch the full diff with `git show <sha>` and retain only commits that modify files ending in `.md` or `.rst`.  
  - Isolate the documentation‑only portion of each diff, discarding unrelated code hunks.  
  - Record `commit_hash`, `commit_message`, `repository_name`, `doc_diff`, and ISO‑8601 `timestamp` per the `CommitPair` schema.  
  - After extraction, **verify** that the CSV contains **≥ 500 rows**; abort with a clear error if the threshold is not met.  
  - **Verification**: CSV contains ≥ 500 rows, each row validates against `commitpair.schema.yaml` (`pytest tests/contract/test_commitpair_schema.py`), a log reports the number of skipped commits, and a SHA‑256 checksum entry for the CSV is added to `data/metadata.yaml`.

- [ ] T004 [P1] [US1] **Create a human‑annotated gold‑standard intent dataset (50 samples) and compute inter‑annotator agreement** – `code/gold_annotation.py`, `data/gold/annotations.json`  
  - Randomly sample 50 commit pairs from `data/raw/commit_pairs.csv` using the global seed defined in `code/seeds.py`.  
  - Export the sampled rows to `data/gold/sample_for_annotation.csv`.  
  - Provide a minimal HTML/JS annotation interface (served locally via `python -m http.server`) that allows two independent annotators to label **technical‑intent** entities in the human documentation diffs. The interface writes each annotator’s results to `data/gold/annotator_<id>.csv`.  
  - After both annotators finish, run `gold_annotation.py` to (a) read the two CSVs, (b) compute Cohen’s κ, (c) **require** κ ≥ 0.6 (abort with informative error if lower), (d) merge the annotations (conflicts resolved automatically and logged in `data/gold/conflicts.log`), and (e) produce `data/gold/annotations.json` with fields `sample_id`, `intent_entities`, and `kappa`.  
  - **Verification**: JSON parses, contains `kappa` in [0, 1] and ≥ 0.6; a test asserts this condition. No fallback is permitted.

---

## Phase 2 – Model selection justification & limitation discussion (User Story 2)

- [ ] T005 [P2] [US2] **Document the rationale for selecting three CPU‑friendly LLMs and acknowledge scale limitation** – `docs/model_selection_and_limitations.md`  
  - Explain that Phi‑3‑mini (≈ 3 B), Gemma‑2‑2b (≈ 2 B), and Llama‑3.2‑3B (≈ 3 B) are the largest open‑source models that can reliably run in 4‑bit quantization on the GitHub Actions free‑tier runner (≈ 7 GB RAM).  
  - Cite the reviewer concern that model scale is limited and state that the experiment isolates **architectural** differences within a comparable‑size regime; any observed gaps should be interpreted accordingly.  
  - Include a table of model parameters, quantization settings, and expected per‑commit latency.  
  - **Verification**: The markdown file exists, contains the required explanatory paragraphs and table, and `pytest tests/test_model_selection.py` checks that each listed model has ≤ 3 B parameters and that the limitation discussion is present.

---

## Phase 3 – Model inference (User Story 2)

- [ ] T006 [P2] [US2] **CPU‑only generation pipeline for the three LLMs with success‑rate measurement** – `code/generation.py`, `data/generated/phi3-mini/`, `data/generated/gemma2-2b/`, `data/generated/llama3.2-3b/`, `data/generated/generation_success_rates.csv`  
  - Load each model in 4‑bit quantization via `bitsandbytes` on `device="cpu"` (no GPU fallback).  
  - Prompt format:  
    ```
    Commit message: <commit_message>
    Pre‑change documentation context: <prev_doc_snippet>
    Generate updated documentation:
    ```  
  - Use deterministic decoding (`do_sample=False`), `max_new_tokens=200`, and enforce a hard timeout of 60 s per commit.  
  - Retry up to 2 times on failure; after the third failure write a `generation_failed` entry in `data/generated/<model_id>/log.txt`.  
  - Write each successful output to `data/generated/<model_id>/<commit_hash>_<model_id>.txt`.  
  - After processing the full dataset, compute per‑model success rate = `n_success / n_input` and store in `data/generated/generation_success_rates.csv`.  
  - **Verification**: Generation time per commit ≤ 60 s on the CPU runner, all three models achieve `success_rate ≥ 0.90` (test fails otherwise), and SHA‑256 checksums for all generated files are recorded in `data/metadata.yaml`.

---

## Phase 4 – Entity extraction (User Story 3)

- [ ] T007 [P3] [US3] **Surface‑entity regex extraction** – `code/entity_extraction_surface.py`, `data/intermediate/surface_entities/`  
  - Apply regexes **only** for the three surface patterns required by the spec:  
    1. File paths (`[a-zA-Z0-9_./-]+\\.(py|md|rst)`)  
    2. Function signatures (`def [a-zA-Z_][a-zA-Z0-9_]*\\(`)  
    3. Version numbers (`\\d+\\.\\d+\\.\\d+`)  
  - For each extracted token, verify existence in the repository’s current codebase using `git grep -w`.  
  - Produce an `EntitySet` JSON per sample (`{sample_id}.json`) with `type: "surface"` and `verified: true/false`.  
  - **Verification**: For a 50‑sample audit subset, at least 95 % of surface entities from human diffs are verified; a test asserts this proportion.

- [ ] T008 [P3] [US3] **Technical‑intent extraction with calibrated zero‑shot classifier** – `code/entity_extraction_intent.py`, `data/intermediate/intent_entities/`  
  - Primary method: zero‑shot NLI classifier (`facebook/bart-large-mnli`) run deterministically (seeded) and calibrated on the gold‑standard annotations from T004. Use the confidence threshold that maximises F1 on the held‑out validation split.  
  - For each generated intent entity, extract any technical noun‑phrase (function/class/module names) and verify against the repository codebase (same `git grep` approach). Flag `verified: false` for hallucinated intent terms.  
  - **Verification**: On the 50‑sample gold set, precision ≥ 0.75 and recall ≥ 0.70 against human‑annotated intent entities; every generated intent entity includes a boolean `verified` field; tests validate these metrics.

---

## Phase 5 – Fidelity scoring (User Story 3)

- [ ] T009 [P3] [US3] **Compute precision/recall and hallucination rate per sample** – `code/fidelity_scoring.py`, `data/processed/fidelity_metrics.csv`  
  - Load the human `EntitySet` (surface + intent) and the generated `EntitySet` for each `(commit_hash, model_id)` pair.  
  - Calculate `precision_intent`, `recall_intent`, `precision_surface`, `recall_surface`.  
  - Hallucination rate = (number of generated entities with `verified: false`) / (total generated entities).  
  - Write one row per sample to `data/processed/fidelity_metrics.csv conforming to `fidelity.schema.yaml`.  
  - Record the CSV checksum in `data/metadata.yaml`.  
  - **Verification**: CSV passes schema validation (`pytest tests/contract/test_fidelity_schema.py`) and contains exactly `N_samples × 3` rows (three models per sample).

---

## Phase 6 – Statistical analysis (User Story 3)

- [ ] T010 [P3] [US3] **Normality testing, Friedman/ANOVA, Holm‑Bonferroni correction, and exploratory flag handling** – `code/statistical_analysis.py`, `results/statistics.json`  
  - Perform Shapiro‑Wilk tests on the paired differences of each metric. If any p < 0.05, use the Friedman chi‑square test; otherwise run repeated‑measures ANOVA.  
  - Apply Holm‑Bonferroni correction across the three primary metrics (intent precision, surface precision, hallucination rate).  
  - Include effect‑size reporting (Kendall’s W for Friedman, η² for ANOVA).  
  - Propagate the `exploratory` flag from `results/power_report.md`; if `exploratory: true`, add `"exploratory": true` to the JSON and note that results are framed as exploratory.  
  - **Verification**: JSON contains keys `p_values`, `significant`, `effect_sizes`, and `exploratory` (matching the power report); a test asserts their presence and consistency.

---

## Phase 7 – Visualization & reporting (User Story 3)

- [ ] T011 [P3] [US3] **Generate figures and a markdown summary** – `code/visualization.py`, `results/figures/intent_precision_bar.png`, `results/figures/surface_confusion_matrix.png`, `results/summary.md`  
  - Bar chart of mean intent precision per model (95 % CI).  
  - Heatmap confusion matrix for surface‑entity preservation vs. hallucination per model.  
  - Assemble `results/summary.md` that references the figure files, includes a concise table of key metrics, and states the exploratory status when applicable.  
  - **Verification**: PNG files exist, are ≥ 300 px wide, non‑empty; `summary.md` contains Markdown image links to each figure; a test checks file existence and non‑zero size.

---

## Phase 8 – Contract validation, CI, and reproducibility utilities

- [ ] T012 [P?] **Run contract tests against all schemas and integrate full pipeline in GitHub Actions** – `tests/contract/test_schemas.py`, `.github/workflows/research.yml`  
  - Execute `pytest -m contract` after the pipeline finishes to ensure every artifact (`commit_pairs.csv`, generated outputs, entity sets, fidelity metrics) validates against its definition in `contracts/project.schema.yaml`.  
  - Add a GitHub Actions workflow that caches model weights, installs dependencies, runs the full pipeline (`python -m code.run_pipeline --full`), then executes `pytest`. Enforce CPU‑only execution (no `--gpu` flag).  
  - **Verification**: CI run completes with “Validate contracts” passing; workflow badge shows “All checks passed”.