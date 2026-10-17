# Tasks: Evaluating LLM Fidelity in Commit-to-Documentation Translation

**Inputs**: `spec.md`, `plan.md`, existing research idea, contracts in `specs/001-evaluating-the-use-of-llms-for-automated/contracts/`, and any reviewer feedback.

The goal is to produce a reproducible, end‑to‑end pipeline that satisfies every functional and non‑functional requirement in the specification while providing an early executable result that can be run on a minimal subset of the data.

**Global constraints**:
- All generation runs **CPU-only** (NFR-001, FR-002). No GPU fallback exists anywhere in the pipeline.
- All stochastic components use the pinned seed from `code/seeds.py` (Constitution I).
- Every data‑writing step records SHA‑256 checksums in `data/metadata.yaml` and writes **new files** only (Constitution III).

---

## Phase 0 – Project scaffolding & early sanity check

- [ ] **T001** [P?] [US1] **Create quick‑start documentation and a minimal runnable entry point**
  - **Artifact(s)**: `quickstart.md`, `code/run_pipeline.py`
  - Write a short "Getting started" guide that lists required Python 3.11 packages, how to install `bitsandbytes` and `transformers`, and the command `python -m code.run_pipeline --sample 5`.
  - Implement `run_pipeline` to load a tiny hard‑coded commit pair (one synthetic example used **only** as a smoke test of plumbing, never as analysis data) and invoke the generation module (CPU-only) to produce a single output file under `data/generated/phi3-mini/sample_test.txt`.
  - **Verification**: Running the command completes in < 30 s and creates the output file; `pytest tests/quickstart_test.py` passes.

---

## Phase 1 – Power‑analysis (sample‑size justification)

- [X] **T002** [P?] [US1] **Monte‑Carlo power analysis for the Friedman test**
  - **Artifact(s)**: `code/power_analysis.py`, `results/power_report.md`
  - **Justification (spec‑rooted)**: the spec's "Assumption about statistical validity" requires that, if power for the Friedman test is low, results be framed as exploratory rather than definitive; this task operationalizes that assumption and supports the interpretation of SC‑004 / FR‑005. It is therefore a spec‑mandated validity check, not scope expansion.
  - Simulate paired precision scores for three models under varying effect sizes using the pinned seed from `code/seeds.py` (T014); estimate the probability of detecting a medium effect (Cohen's d ≈ 0.5) with 500 samples.
  - If estimated power < 0.8, set the flag `exploratory: true` in `power_report.md` and record the estimated power; downstream statistical reporting (T009) must honor this flag.
  - **Verification**: A test asserts that `results/power_report.md` exists, contains a numeric power estimate for n=500, and contains an `exploratory` flag whose value is `true` exactly when the estimated power is < 0.8 (both branches are executable and tested).

---

## Phase 2 – Data acquisition & pairing (Priority P1)

- [ ] **T003** [P1] [US1] **Extract ≥ 500 (commit_message, documentation_diff) pairs** <!-- FAILED-IN-EXECUTION: code/data_extraction.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_extraction.py exit=-1 (TIMEOUT) -->
  - **Artifact(s)**: `code/data_extraction.py`, `data/raw/commit_pairs.csv`
  - Clone the five target repositories (`pandas`, `requests`, `scikit-learn`, `flask`, `django`) at the latest tag, walk the last 2 years of history, and select commits that modify `.md` or `.rst` files.
  - For each qualifying commit, record `commit_hash`, `commit_message`, `repository_name`, `doc_diff`, and ISO‑8601 `timestamp` according to `commitpair.schema.yaml`. Commits with no documentation change are excluded (FR‑007: every retained pair has a ground‑truth human diff).
  - Compute and record the SHA‑256 checksum of `commit_pairs.csv` in `data/metadata.yaml` (see T013); the file is written once and never modified in place.
  - **Verification**: `data/raw/commit_pairs.csv` contains ≥ 500 rows, each row passes schema validation (`pytest tests/contract/test_commitpair_schema.py`), a log entry confirms the number of skipped commits (e.g., "no documentation change"), and `data/metadata.yaml` contains the file's checksum.

- [ ] **T004** [P1] [US1] **Gold‑standard intent annotation via two deterministic automated annotators** <!-- FAILED-IN-EXECUTION: code/gold_annotation.py exit=1 -->
  - **Artifact(s)**: `data/gold_standard/annotations.json`, `code/gold_annotation.py`
  - Randomly sample 50 commit pairs from `commit_pairs.csv` using the pinned seed (T014).
  - Run **two independent deterministic annotator agents** (fixed prompts, pinned seeds, temperature 0) that each label technical‑intent entities in the sampled pairs using the rubric in the spec. Determinism makes this step fully executable end‑to‑end without live human annotators while preserving the two‑rater design required to compute agreement.
  - Compute inter‑annotator Cohen's κ between the two annotators. If κ ≥ 0.6, store the merged annotations; otherwise record `kappa` and the fallback decision, and the pipeline uses the rule‑based intent extractor as primary (see T007).
  - **Verification**: The JSON file includes `sample_id`, `intent_entities`, `kappa`, and `fallback_used`; a test asserts the file parses, `kappa` is a number in [0, 1], and `fallback_used` is `true` exactly when `kappa < 0.6`.

---

## Phase 3 – Model inference (Priority P2)

- [ ] **T005** [P2] [US2] **CPU-only generation pipeline for three LLMs, with success-rate measurement**
  - **Artifact(s)**: `code/generation.py`, `data/generated/phi3-mini/`, `data/generated/gemma2-2b/`, `data/generated/llama3.2-3b/`, `data/generated/generation_success_rates.csv`
  - Load each model in 4‑bit quantization (`bitsandbytes`) on `device="cpu"`. **No GPU fallback**: the pipeline is CPU-only per NFR-001 and FR-002. Prompt format:

    ```
    Commit message: <commit_message>
    Pre‑change documentation context: <prev_doc_snippet>
    Generate updated documentation:
    ```

  - Enforce `max_new_tokens=200`, `timeout=60 s`, deterministic decoding (`do_sample=False`). Retry up to 2 × on failure; on the third failure write a `generation_failed` entry in `data/generated/<model_id>/log.txt`.
  - **Success-rate measurement (SC‑002)**: after generation, compute per‑model success rate = successful generations / total input pairs and write `data/generated/generation_success_rates.csv` with columns `model_id, n_input, n_success, success_rate`.
  - Compute and record SHA‑256 checksums of all generated output files in `data/metadata.yaml` (T013).
  - **Verification**: After processing the sample, each model produces a distinct `.txt` file named `{commit_hash}_{model_id}.txt` with a corresponding entry in `data/generated/<model_id>/metadata.csv`; generation time per commit ≤ 60 s on the CPU runner; and `generation_success_rates.csv` shows `success_rate >= 0.90` for **each** of the three models (a test fails if any model is below 0.90).

---

## Phase 4 – Entity extraction (Priority P3)

- [ ] **T006** [P3] [US3] **Surface‑entity regex extraction & AST verification**
  - **Artifact(s)**: `code/entity_extraction_surface.py`, `data/intermediate/surface_entities/`
  - Apply expanded regexes for file paths, function signatures, version numbers, class names, variable assignments, and import statements (see plan).
  - For each extracted surface token, verify existence in the repository's current codebase via two methods: (a) `git grep -w` and (b) parsing all Python files with `ast` to locate definitions/uses.
  - Mark `verified: true` if both checks succeed; otherwise flag as a potential hallucination (FR‑006, surface portion).
  - Write each sample's EntitySet as a **new** JSON file (`{sample_id}.json`); record checksums in `data/metadata.yaml` (T013).
  - **Verification**: For a 50‑sample audit subset, `entity_extraction_surface.py` produces a JSON file per sample and a log summarising verification rates; a test asserts that at least 95 % of surface entities from human diffs are verified.

- [ ] **T007** [P3] [US3] **Technical‑intent extraction with codebase verification of intent terms**
  - **Artifact(s)**: `code/entity_extraction_intent.py`, `data/intermediate/intent_entities/`
  - Primary method: zero‑shot NLI classifier (`facebook/bart-large-mnli`), run deterministically with the pinned seed (T014), calibrated on the gold‑standard (T004) to achieve κ ≥ 0.6. Use a confidence threshold that maximises F1 on the validation split.
  - Fallback: deterministic rule‑based heuristic (keyword list + noun‑phrase chunking) if κ < 0.6 or the classifier fails on a sample.
  - **Intent‑term codebase verification (FR‑006, intent portion)**: for every generated intent entity, extract its technical noun‑phrase terms (function/class/module identifiers, file names) and verify each against the repository codebase using the same `git grep -w` + AST checks as T006. Terms not found by either check are flagged `verified: false` and counted as hallucinated intent entities; this feeds the hallucination metrics in T008.
  - Output JSON per sample containing `entities` with `type: intent`, `source: human` or `generated`, and a `verified` field for generated intent entities.
  - **Verification**: Run on the 50‑sample gold set; a test confirms precision ≥ 0.75 and recall ≥ 0.70 against the annotated intent entities, and that every generated intent entity carries a boolean `verified` field derived from codebase checks.

---

## Phase 5 – Fidelity scoring (Priority P3)

- [ ] **T008** [P3] [US3] **Compute precision/recall and hallucination rate per sample**
  - **Artifact(s)**: `code/fidelity_scoring.py`, `data/processed/fidelity_metrics.csv`
  - Compare human `EntitySet` (surface + intent) with generated `EntitySet` for each `(commit_hash, model_id)`.
  - Calculate `precision_intent`, `recall_intent`, `precision_surface`, `recall_surface`.
  - Hallucination rate = (# generated surface **and** intent entities not verified in codebase, per T006/T007) / (total generated entities).
  - Conform to `fidelity.schema.yaml`. Write to a new file and record its checksum in `data/metadata.yaml` (T013).
  - **Verification**: The CSV passes schema validation (`pytest tests/contract/test_fidelity_schema.py`) and contains exactly `N_samples × 3` rows (where N_samples = number of commit pairs used).

---

## Phase 6 – Statistical analysis (Priority P3)

- [ ] **T009** [P3] [US3] **Normality testing, Friedman/ANOVA, Holm‑Bonferroni correction**
  - **Artifact(s)**: `code/statistical_analysis.py`, `results/statistics.json`
  - Perform Shapiro‑Wilk test on each metric's paired differences. If any p < 0.05 → use Friedman test (`scipy.stats.friedmanchisquare`); else run repeated‑measures ANOVA (`statsmodels`).
  - Apply Holm‑Bonferroni correction across the three metrics (intent precision, surface precision, hallucination rate).
  - Honor the `exploratory` flag from T002: if power < 0.8, `statistics.json` carries `"exploratory": true` and the summary (T010) frames results as exploratory associations.
  - Store per‑model means, p‑values, and significance flags in `statistics.json`.
  - **Verification**: A test asserts that the JSON contains keys `p_values`, `significant`, and `exploratory` (with `exploratory` consistent with T002's power report).

---

## Phase 7 – Visualization & reporting

- [ ] **T010** [P3] [US3] **Generate figures and a markdown summary**
  - **Artifact(s)**: `code/visualization.py`, `results/figures/intent_precision_bar.png`, `results/figures/surface_confusion_matrix.png`, `results/summary.md`
  - Bar chart of mean intent precision per model (with 95 % CI).
  - Confusion matrix heatmap for surface‑entity preservation vs. hallucination per model.
  - Write `summary.md` that references the exact figure files, includes a concise table of key metrics, and states the exploratory status when T002's power is < 0.8.
  - **Verification**: The PNG files exist, are ≥ 300 px wide, and `summary.md` contains a Markdown image link to each; a test checks that the figure files are non‑empty.

---

## Phase 8 – Data hygiene, reproducibility, contract validation & CI integration

- [ ] **T013** [P?] [US?] **Data hygiene: checksums and no in‑place modification**
  - **Artifact(s)**: `code/data_hygiene.py`, `data/metadata.yaml`, `tests/test_data_hygiene.py`
  - Provide a shared utility that computes SHA‑256 checksums of every file under `data/` and records them (with derivation notes) in `data/metadata.yaml`; every pipeline stage (T003, T005, T006, T007, T008) calls it after writing outputs.
  - Enforce the no‑in‑place‑modification rule: all transformations write new filenames; raw files are never rewritten.
  - **Verification**: `pytest tests/test_data_hygiene.py` asserts that every file under `data/` has a matching checksum entry in `data/metadata.yaml` and that no raw file's checksum has changed between two consecutive pipeline runs.

- [ ] **T014** [P?] [US?] **Reproducibility: pinned seeds for all stochastic components**
  - **Artifact(s)**: `code/seeds.py`, `tests/test_seeds.py`
  - Define a single pinned seed (`SEED = 42`) consumed by: the Monte‑Carlo power analysis (T002), dataset sampling (T004), LLM generation (T005, `do_sample=False`), the zero‑shot classifier (T007), and any bootstrap resampling (T009).
  - Document the seed policy in `quickstart.md`.
  - **Verification**: `pytest tests/test_seeds.py` asserts that `code/seeds.py` exposes `SEED` and that each stochastic module imports it (static check on imports/usage); re-running T002 twice yields identical power estimates.

- [ ] **T011** [US?] **Run contract tests against all schemas (sequential, post‑pipeline)**
  - **Artifact(s)**: `tests/contract/test_schemas.py`, `pytest.log`
  - This task MUST run **after** T003–T010 (and T013/T014) because it validates contracts against the artifacts those tasks produce; it is not parallel‑safe.
  - Execute `pytest -m contract`. All schemas (`commitpair`, `generatedoutput`, `entityset`, `fidelity`) must pass.
  - **Verification**: `pytest.log` shows 0 failures; the CI step `Validate contracts` succeeds.

- [ ] **T012** [US?] **Add GitHub Actions workflow to automate the full pipeline (post‑pipeline task)**
  - **Artifact(s)**: `.github/workflows/research.yml`
  - This task is a **post‑pipeline** step: it is executed only after T003–T011 are complete and their artifacts exist, so CI never runs on incomplete data. It is not parallel‑safe.
  - The workflow caches model weights, installs dependencies, runs the pipeline end‑to‑end **CPU-only** (`python -m code.run_pipeline --full`), then executes `pytest`. No GPU fallback step exists (NFR‑001).
  - **Verification**: Pushing to the repository triggers the workflow; the final job `Validate contracts` passes and the workflow badge shows "All checks passed".

---

## Dependencies & Requirement Coverage

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| **FR‑001** (≥500 commit‑doc pairs) | T003 |
| **FR‑002** (3 LLMs, CPU‑only) | T005 (CPU-only, no GPU fallback) |
| **FR‑003** (entity taxonomy) | T006, T007 |
| **FR‑004** (precision/recall per category) | T008 |
| **FR‑005** (Friedman/ANOVA) | T009 (with T002 power justification per the spec's statistical-validity assumption) |
| **FR‑006** (codebase verification of ALL generated technical terms — surface **and** intent) | T006 (surface), T007 (intent) |
| **FR‑007** (exclude samples lacking human diff) | T003 (filter) |
| **FR‑008** (gold‑standard with κ ≥ 0.6) | T004 (deterministic two‑annotator design with documented fallback) |
| **NFR‑001** (≤60 s per commit, CPU‑only runner) | T005 (CPU-only, 60 s timeout, no GPU fallback) |
| **SC‑001** | T003 |
| **SC‑002** (≥90 % generation success per model) | T005 (`generation_success_rates.csv`, asserted ≥ 0.90) |
| **SC‑003** | T006, T007, T008 |
| **SC‑004** | T002 (power/exploratory framing), T009 |
| **SC‑005** | T006, T007, T008 |
| **Constitution I (Reproducibility, pinned seeds)** | T014 |
| **Constitution III (Data Hygiene, checksums)** | T013 |
| **US‑1, US‑2, US‑3** | Referenced in task tags and verification steps |

All tasks are ordered to respect data flow: extraction → annotation → generation → extraction → scoring → analysis → visualization → hygiene/reproducibility → validation → CI. T011 and T012 are strictly sequential post‑pipeline tasks. No task creates or modifies platform‑owned state outside the `data/`, `code/`, `results/`, `tests/`, and `.github/` directories.