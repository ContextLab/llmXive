# Tasks: Evaluating LLM Fidelity in Commit-to-Documentation Translation

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-evaluating-the-use-of-llms-for-automated/contracts/`, and any reviewer feedback.

The goal is to deliver a fully reproducible, end‑to‑end pipeline that satisfies every functional and non‑functional requirement in the specification while providing an early executable result that can be run on a minimal subset of the data.

---

## Phase 0 – Project scaffolding & early sanity check

- [ ] T001 [P?] [US1] **Create quick‑start documentation and a minimal runnable entry point** – `quickstart.md`, `code/run_pipeline.py`  
  - Write a short “Getting started” guide that lists required Python 3.11 packages, how to install `bitsandbytes` and `transformers`, and the command `python -m code.run_pipeline --sample 5`.  
  - Implement `run_pipeline` to load a tiny hard‑coded commit pair (synthetic smoke‑test only) and invoke the generation module (CPU‑only) to produce a single output file under `data/generated/phi3-mini/sample_test.txt`.  
  - **Verification**: Running the command completes in < 30 s, creates the output file, and `pytest tests/quickstart_test.py` passes.

- [ ] T002 [P?] [US1] **Monte‑Carlo power analysis for the Friedman test** – `code/power_analysis.py`, `results/power_report.md`  
  - Simulate paired precision scores for three models under varying effect sizes (seeded with `code/seeds.py`).  
  - Estimate power for n = 500 with a medium effect (Cohen’s f = 0.25).  
  - Write `results/power_report.md` containing the numeric power estimate and an `exploratory: true` flag if power < 0.8.  
  - **Verification**: Test asserts that the file exists, contains a numeric power estimate, and that the `exploratory` flag matches the computed power.

---

## Phase 1 – Data acquisition & pairing (Priority P1)

- [ ] T003 [P1] [US1] **Extract ≥ 500 (commit_message, documentation_diff) pairs from the five target repositories** – `code/data_extraction.py`, `data/raw/commit_pairs.csv`  
  - Clone the repositories `pandas`, `requests`, `scikit-learn`, `flask`, `django` at the default branch into a temporary `data/tmp/repos/` directory.  
  - Use the GitHub REST API (`GET /repos/{owner}/{repo}/commits`) with `since=2 years ago` and a personal‑access‑token supplied via the environment variable `GITHUB_TOKEN` (fails loudly if missing).  
  - For each commit, fetch the full diff with `git show <sha>` and retain only those that modify files ending in `.md` or `.rst`.  
  - Parse the diff to isolate the documentation‑only portion (exclude code hunks).  
  - Record `commit_hash`, `commit_message`, `repository_name`, `doc_diff`, and ISO‑8601 `timestamp` per the `CommitPair` schema.  
  - Write the result to `data/raw/commit_pairs.csv` **without overwriting** any existing file; if the file already exists, abort with an error to avoid accidental data loss.  
  - **Verification**: CSV contains ≥ 500 rows, each row validates against `commitpair.schema.yaml` (`pytest tests/contract/test_commitpair_schema.py`), a log reports the number of skipped commits, and a SHA‑256 checksum entry for the CSV is added to `data/metadata.yaml`.

- [ ] T004 [P1] [US1] **Create a human‑annotated gold‑standard intent dataset (50 samples) and compute inter‑annotator agreement** – `code/gold_annotation.py`, `data/gold/annotations.json`  
  - Randomly sample 50 commit pairs from `data/raw/commit_pairs.csv` using the pinned seed in `code/seeds.py`.  
  - Export the sampled rows to `data/gold/sample_for_annotation.csv`.  
  - Provide a simple HTML/JS annotation interface (served locally via `python -m http.server`) that allows two independent annotators to label **technical‑intent** entities in the human documentation diffs. The interface writes each annotator’s results to `data/gold/annotator_<id>.csv`.  
  - After both annotators finish, run `gold_annotation.py` to (a) read the two CSVs, (b) compute Cohen’s κ, (c) merge the annotations (conflicts resolved by a senior reviewer automatically flagged in `conflicts.log`), and (d) produce `data/gold/annotations.json` with fields `sample_id`, `intent_entities`, and `kappa`.  
  - **Verification**: JSON parses, contains `kappa` in [0, 1], and a test asserts `kappa ≥ 0.6`. If κ < 0.6, the pipeline records `"fallback_used": true` in `data/gold/annotations.json` for downstream intent‑extraction tasks.

---

## Phase 2 – Model selection justification (Priority P2)

- [ ] T015 [P2] [US2] **Document the rationale for choosing three small‑scale CPU‑friendly LLMs and note the limitation regarding model size** – `docs/model_selection.md`  
  - Explain that Phi‑3‑mini (≈ 3 B), Gemma‑2‑2b (≈ 2 B), and Llama‑3.2‑3B are the largest open‑source models that can reliably run in 4‑bit quantization on the GitHub Actions free‑tier runner (≈ 7 GB RAM).  
  - Cite the reviewer concern that model scale is limited, and state that results will be interpreted as “behavior of comparable‑size models” rather than “scale‑driven trends”.  
  - Include a table of model parameters, quantization settings, and expected per‑commit latency.  
  - **Verification**: The markdown file exists and a test (`tests/test_model_selection.py`) checks that each listed model has `max_params` ≤ 3 B and that the explanatory paragraph is present.

---

## Phase 3 – Model inference (Priority P2)

- [ ] T005 [P2] [US2] **CPU‑only generation pipeline for the three LLMs, with success‑rate measurement** – `code/generation.py`, `data/generated/phi3-mini/`, `data/generated/gemma2-2b/`, `data/generated/llama3.2-3b/`, `data/generated/generation_success_rates.csv`  
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

## Phase 4 – Entity extraction (Priority P3)

- [ ] T006 [P3] [US3] **Surface‑entity regex extraction & AST verification** – `code/entity_extraction_surface.py`, `data/intermediate/surface_entities/`  
  - Apply expanded regexes for file paths, function signatures (including multi‑line), class definitions, imports, version numbers, and variable assignments.  
  - For each extracted token, verify existence in the repository’s current codebase using both `git grep -w` and an AST walk of all Python files.  
  - Produce an `EntitySet` JSON per sample (`{sample_id}.json`) with `type: "surface"` and `verified: true/false`.  
  - **Verification**: For a 50‑sample audit subset, at least 95 % of surface entities from human diffs are verified; a test asserts this proportion.

- [ ] T007 [P3] [US3] **Technical‑intent extraction with fallback and codebase verification** – `code/entity_extraction_intent.py`, `data/intermediate/intent_entities/`  
  - Primary method: zero‑shot NLI classifier (`facebook/bart-large-mnli`) run deterministically (seeded) and calibrated on the gold‑standard annotations from T004. Use the confidence threshold that maximises F1 on the validation split.  
  - If the gold‑standard κ < 0.6 (recorded in `data/gold/annotations.json`) **or** the classifier fails on a sample, fall back to a deterministic keyword‑heuristic extractor (keywords: because, fix, improve, handle, prevent).  
  - For each generated intent entity, extract any technical noun‑phrase (function/class/module names) and verify against the repository codebase (same `git grep` + AST approach). Flag `verified: false` for hallucinated intent terms.  
  - Output an `EntitySet` JSON per sample with `type: "intent"` and the `verified` flag.  
  - **Verification**: On the 50‑sample gold set, precision ≥ 0.75 and recall ≥ 0.70 against human‑annotated intent entities; every generated intent entity includes a boolean `verified` field; tests validate these metrics.

---

## Phase 5 – Fidelity scoring (Priority P3)

- [ ] T008 [P3] [US3] **Compute precision/recall and hallucination rate per sample** – `code/fidelity_scoring.py`, `data/processed/fidelity_metrics.csv`  
  - Load the human `EntitySet` (surface + intent) and the generated `EntitySet` for each `(commit_hash, model_id)` pair.  
  - Calculate `precision_intent`, `recall_intent`, `precision_surface`, `recall_surface`.  
  - Hallucination rate = (number of generated entities with `verified: false`) / (total generated entities).  
  - Write one row per sample to `data/processed/fidelity_metrics.csv` conforming to `fidelity.schema.yaml`.  
  - Record the CSV checksum in `data/metadata.yaml`.  
  - **Verification**: CSV passes schema validation (`pytest tests/contract/test_fidelity_schema.py`) and contains exactly `N_samples × 3` rows (three models per sample).

---

## Phase 6 – Statistical analysis (Priority P3)

- [ ] T009 [P3] [US3] **Normality testing, Friedman/ANOVA, Holm‑Bonferroni correction, and exploratory flag handling** – `code/statistical_analysis.py`, `results/statistics.json`  
  - Perform Shapiro‑Wilk tests on the paired differences of each metric. If any p < 0.05, use the Friedman chi‑square test; otherwise run repeated‑measures ANOVA.  
  - Apply Holm‑Bonferroni correction across the three primary metrics (intent precision, surface precision, hallucination rate).  
  - Include effect‑size reporting (Kendall’s W for Friedman, η² for ANOVA).  
  - Propagate the `exploratory` flag from `results/power_report.md`; if `exploratory: true`, add `"exploratory": true` to the JSON and note that results are framed as exploratory.  
  - **Verification**: JSON contains keys `p_values`, `significant`, `effect_sizes`, and `exploratory` (matching the power report); a test asserts their presence and consistency.

---

## Phase 7 – Visualization & reporting

- [ ] T010 [P3] [US3] **Generate figures and a markdown summary** – `code/visualization.py`, `results/figures/intent_precision_bar.png`, `results/figures/surface_confusion_matrix.png`, `results/summary.md`  
  - Bar chart of mean intent precision per model (95 % CI).  
  - Heatmap confusion matrix for surface‑entity preservation vs. hallucination per model.  
  - Assemble `results/summary.md` that references the figure files, includes a concise table of key metrics, and states the exploratory status when applicable.  
  - **Verification**: PNG files exist, are ≥ 300 px wide, non‑empty; `summary.md` contains Markdown image links to each figure; a test checks file existence and non‑zero size.

---

## Phase 8 – Contract validation & CI integration

- [ ] T011 [P?] [US?] **Run contract tests against all schemas (sequential, post‑pipeline)** – `tests/contract/test_schemas.py`, `pytest.log`  
  - Execute `pytest -m contract` after all data‑generation tasks have completed.  
  - Ensure every artifact (`commit_pairs.csv`, generated outputs, entity sets, fidelity metrics) validates against its corresponding definition in `contracts/project.schema.yaml`.  
  - **Verification**: `pytest.log` shows 0 failures; CI step “Validate contracts” succeeds.

- [ ] T012 [P?] [US?] **Add GitHub Actions workflow to automate the full pipeline** – `.github/workflows/research.yml`  
  - Workflow caches model weights, installs dependencies, runs the full pipeline (`python -m code.run_pipeline --full`), then executes `pytest`.  
  - Enforce CPU‑only execution (no `--gpu` flag).  
  - **Verification**: Pushing to the repository triggers the workflow; the final job “Validate contracts” passes and the badge shows “All checks passed”.

---

## Phase 9 – Data hygiene & reproducibility utilities

- [ ] T013 [P?] [US?] **Data hygiene: SHA‑256 checksums and no in‑place modification** – `code/data_hygiene.py`, `data/metadata.yaml`, `tests/test_data_hygiene.py`  
  - Utility computes SHA‑256 checksums for every file under `data/` after it is written and records them in `data/metadata.yaml` with provenance notes.  
  - Enforce that raw files are never overwritten; each transformation writes a new file with a distinct name.  
  - **Verification**: Test asserts that each file under `data/` has a matching checksum entry and that no checksum for a raw file changes between two consecutive runs.

- [ ] T014 [P?] [US?] **Reproducibility: pinned seeds for all stochastic components** – `code/seeds.py`, `tests/test_seeds.py`  
  - Define a single global seed (`SEED = 42`).  
  - All stochastic modules (power analysis, dataset sampling, LLM generation, zero‑shot classifier, bootstrap resampling) import and use this seed.  
  - Document the seed policy in `quickstart.md`.  
  - **Verification**: Test checks that `code/seeds.py` exposes `SEED` and that each stochastic script imports it; re‑running T002 twice yields identical power estimates.

---

## Phase 10 – Discussion of model‑scale limitation (new)

- [ ] T016 [P2] [US2] **Explicitly discuss the impact of limited model scale on the research question** – `docs/limitations_and_future_work.md`  
  - Summarize the reviewer concern that all three selected models are of comparable small size, limiting the ability to draw conclusions about “how different LLM architectures differ” with respect to scale.  
  - Explain that the current experiment isolates architectural differences *within* the small‑scale regime and that any observed performance gaps should be interpreted as architecture‑specific rather than size‑driven.  
  - Propose a concrete future‑work plan: (a) acquire larger open‑source models (e.g., Llama‑3‑8B, Mistral‑7B) and repeat the pipeline on a subset of the data, (b) perform a scaling analysis, and (c) discuss resource constraints and possible use of Kaggle‑free GPU for larger models.  
  - **Verification**: The markdown file exists, contains the three required sections (reviewer concern, interpretation, future‑work plan), and a test (`tests/test_limitations.py`) checks for the presence of the phrase “future‑work plan”.

---

## Dependencies & Requirement Coverage

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| **FR‑001** (≥ 500 commit‑doc pairs) | T003 |
| **FR‑002** (3 LLMs, CPU‑only) | T005 |
| **FR‑003** (entity taxonomy) | T006, T007 |
| **FR‑004** (precision/recall per category) | T008 |
| **FR‑005** (Friedman/ANOVA) | T009 |
| **FR‑006** (codebase verification of all generated terms) | T006, T007 |
| **FR‑007** (exclude samples lacking human diff) | T003 |
| **FR‑008** (human‑annotated gold standard, κ ≥ 0.6) | T004 |
| **NFR‑001** (≤ 60 s per commit, CPU‑only) | T005 |
| **SC‑001** (≥ 500 valid pairs) | T003 |
| **SC‑002** (≥ 90 % generation success) | T005 |
| **SC‑003** (precision/recall & hallucination metrics) | T006, T007, T008 |
| **SC‑004** (statistical significance) | T002, T009 |
| **SC‑005** (hallucination rate) | T006, T007, T008 |
| **Constitution I** (pinned seeds) | T014 |
| **Constitution III** (data hygiene) | T013 |
| **US‑1, US‑2, US‑3** | Reflected in task tags and verification steps |

All tasks are ordered to respect data flow: extraction → gold‑standard annotation → model selection justification → generation → entity extraction → scoring → statistical analysis → visualization → hygiene/reproducibility → validation → CI → discussion of limitations. No task writes outside the `data/`, `code/`, `results/`, `tests/`, `docs/`, or `.github/` directories.
