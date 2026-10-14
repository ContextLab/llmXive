# Tasks: Extending “In-Context World Modeling for Robotic Control”

**Inputs**: `spec.md`, `plan.md`, existing code under `src/`, data‑model contracts, and reviewer feedback.  
The goal is to deliver a complete, reproducible study that satisfies every functional requirement (FR‑001 – FR‑007) and success criterion (SC‑001 – SC‑006).  
The tasks are organised into research phases that respect data flow and the 6‑hour CPU‑only budget.

---

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Verify that a minimal pipeline runs on a small, real subset of interaction clips and produces the required descriptor CSV.

- [X] T001 [P] [US1] **Document project layout & quickstart** – create `quickstart.md` describing a single command that runs the minimal pipeline on 50 clips.  
  - *Verification*: CI runs `bash -c "source quickstart.sh && ./run_minimal.sh"` and checks that the command finishes without error and that the file `data/descriptors_subset.csv` exists.

- [X] T002 [P] [US1] **Generate a small dataset of interaction clips** – implement `src/pipeline/generate_clips.py` to create 50 reproducible clips (`data/raw/clip_*.npz`).  
  - *Verification*: After execution, `ls data/raw/ | wc -l` equals 50 and each `.npz` contains the required arrays (`states`, `actions`, `observations`).

- [ ] T003 [P] [US1] **Extract latent statistical descriptors** – implement `src/pipeline/extract_descriptors.py` that loads each clip, runs the CPU‑only ICWM encoder (`utils/icwm_encoder.py`), computes variance, lag‑1 autocorrelation, and Welch spectral density, and writes `data/descriptors_subset.csv`.   <!-- FAILED-IN-EXECUTION: src/pipeline/extract_descriptors.py exit=1 -->
  - *Verification*: The CSV validates against `specs/001-llmxive-follow-up-extending-in-context-w/contracts/descriptor.schema.yaml` and contains no null/NaN entries.

- [X] T004 [P] [US1] **Run the minimal end‑to‑end pipeline** – add a driver `src/pipeline/run_end_to_end.py` that calls the two scripts above and prints a summary table.  
  - *Verification*: CI runs `python -m src.pipeline.run_end_to_end --subset 50` and checks that the printed table lists 50 rows with all three descriptor columns present.

---

## Phase 2 – Labeling, training, and complexity analysis  

**Goal**: Produce ground‑truth hyper‑parameter labels, train the regressor, and compute the independent task‑complexity metric.

- [ ] T005 [P] [US2] **Grid‑search optimal hyper‑parameters** – implement `src/pipeline/grid_search_labels.py` that, for each training clip, evaluates the discrete grid  
  `τ ∈ {0.5,1.0,1.5,2.0}` × `k ∈ {16,32,64}` on the ICWM policy, records success rates, selects the pair with highest rate, and breaks ties deterministically with `np.random.seed(123)`. Output `data/labels.csv`.  
  - *Verification*: `labels.csv` validates against `label.schema.yaml`; every row contains a `success_rate` ≥ 0.0 and ≤ 1.0.

- [ ] T006 [P] [US2] **Train lightweight regressor** – implement `src/pipeline/train_regressor.py` that loads `descriptors_subset.csv` + `labels.csv`, splits 80/20 (stratified by `k`), trains a 2‑layer MLP (≤ 64 hidden units, L2 regularisation) on the training split, saves `model/regressor.pt`, and writes `data/metrics.json` containing training/validation MSE and **baseline MSE** where the baseline predicts the **global‑mean temperature τ only** (ignoring k).  
  - *Verification*: The JSON reports `val_mse < 0.9 * baseline_mse` (≥ 10 % improvement).

- [X] T007 [P] [US2] **Compute task‑complexity metric** – implement `src/pipeline/compute_complexity.py` that parses each configuration’s scene description, counts distinct sub‑goals, and writes `data/complexity.csv`.  
  - *Verification*: Pearson correlation between `variance` (from `descriptors_subset.csv`) and `subgoal_count` (from `complexity.csv`) is computed and stored in `data/correlation.txt`; the file must contain `r > 0.5` and `p < 0.05`.

---

## Phase 3 – Zero‑shot calibration & statistical evaluation  

**Goal**: Apply the trained model to novel configurations, record outcomes, and demonstrate statistically significant improvement over a fixed baseline.

- [X] T013 [P] [US3] **Generate novel interaction clips** – implement `src/pipeline/generate_novel_clips.py` to create a set of unseen clips (`data/raw_novel/clip_*.npz`) matching the size used in the validation protocol.  
  - *Verification*: After execution, `ls data/raw_novel/ | wc -l` equals the expected number (e.g., 200) and each file contains the required arrays.

- [~] T014 [P] [US3] **Extract latent descriptors for novel clips** – implement `src/pipeline/extract_descriptors_novel.py` that processes `data/raw_novel/` with the ICWM encoder and writes `data/descriptors_novel.csv`.  
  - *Verification*: The CSV validates against the descriptor schema and contains no null entries.

- [ ] T008 [P] [US3] **Zero‑shot validation pipeline** – implement `src/pipeline/validate_autocwm.py` that loads the trained regressor, predicts `τ` and `k` for every novel clip using `data/descriptors_novel.csv`, runs the ICWM policy with those hyper‑parameters, also runs the fixed baseline (`τ=1.0, k=32`), and writes `data/validation_results.csv`.   <!-- FAILED-IN-EXECUTION: code/src/pipeline/validate_autocwm.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/pipeline/validate_autocwm.py exit=1 -->
  - *Verification*: The CSV validates against `validation_results.schema.yaml`; each row contains boolean `auto_success` and `baseline_success`.

- [ ] T009 [P] [US3] **Statistical significance testing** – implement `src/pipeline/stats_test.py` that reads `validation_results.csv` and performs **both** a paired t‑test and a Wilcoxon signed‑rank test (Bonferroni‑adjusted α = 0.025). Results are saved to `reports/stats_report.txt`.  
  - *Verification*: The report contains `p_ttest < 0.05` **and** `p_wilcoxon < 0.05`.

- [ ] T015 [P] [US3] **Compute and assert success‑rate lift** – implement `src/pipeline/compute_lift.py` that calculates the absolute success‑rate difference between Auto‑ICWM and the fixed baseline from `validation_results.csv`, verifies that the lift is ≥ 5 % (0.05), and writes the result to `reports/lift_report.txt`.  
  - *Verification*: CI checks that `reports/lift_report.txt` contains the line `lift_ok = True` and that the reported lift value meets the ≥ 0.05 threshold.

- [ ] T016 [P] [US3] **Validate SC‑002 success‑rate lift requirement** – read `reports/lift_report.txt` (produced by T015) and assert that the reported lift value is ≥ 0.05; the task fails if `lift_ok` is false or the value is below the threshold, ensuring SC‑002 is explicitly enforced.  
  - *Verification*: CI runs this task and succeeds only when `lift_ok = True` and lift ≥ 0.05.

- [ ] T010 [P] [US3] **Resource‑budget monitoring** – add `src/pipeline/monitor_resources.py` that wraps the full pipeline (T002‑T015) and logs total wall‑clock time and peak RAM (using `psutil`). Output `reports/resource_report.txt`.  
  - *Verification*: The report shows `runtime ≤ 6h` and `peak_ram ≤ 7GB`.

---

## Phase 4 – Reproducibility, documentation, and handoff  

**Goal**: Produce a self‑contained, reproducible artefact set and a concise methods/results write‑up for the paper‑stage handoff.

- [ ] T011 [P] [US3] **Write methods & results summary** – create `docs/methods.md` that (a) describes each pipeline stage, (b) links to the exact output files (`descriptors_subset.csv`, `labels.csv`, `model/regressor.pt`, `validation_results.csv`, `stats_report.txt`, `lift_report.txt`), and (c) reports the numeric values for SC‑001 – SC‑006 (correlation, success‑rate lift, p‑values, runtime, RAM, MSE improvement).  
  - *Verification*: CI runs a script that parses `methods.md` and checks that every referenced file exists and that the reported numbers match the latest artifact contents.

- [ ] T012 [P] [US3] **Full reproducibility script** – create `run_all.sh` (executable) that sequentially runs T002‑T015 in a single CI job, then runs the verification steps from T011. The script must be idempotent; re‑running it must produce identical SHA‑256 hashes for all generated artefacts.  
  - *Verification*: CI executes `bash run_all.sh` twice; after the second run, a diff of the hash manifest (`state/hash_manifest.txt`) must be empty.