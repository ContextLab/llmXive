# Tasks: Density‑Supervision Study for d‑OPSD Diffusion LLMs  

**Inputs**: `spec.md`, `plan.md`, the research question “How does the density of future contextual information …”, and the reviewer‑provided constraints.  

The following checklist implements the full experimental pipeline, from data acquisition to statistical validation and reproducible hand‑off.  All tasks are unchecked; completed work must be re‑opened if any requirement is violated.

---

## Phase 1 – Setup & first end‑to‑end run  

- [X] **T001** [US‑1] **Create a reproducible entry‑point and quick‑start guide**
  - Implement a CLI script `code/run_experiments.py` that parses a YAML config and triggers the full pipeline.  
  - Add usage instructions (command line, required env vars, seed control) to `docs/quickstart.md`.  
  - **Verification**: Running the command `python -m code.run_experiments --config configs/quickstart.yaml` prints “Pipeline initialized” and creates the directory `outputs/` without errors.

- [ ] **T002** [US‑1] **Download & stream the GSM8K test split and the bigbench logical subset**   <!-- FAILED-IN-EXECUTION: code/data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data.py exit=1 -->
  - Add `code/data.py` with functions `load_gsm8k(split="test", streaming=True)` and `load_bigbench_lite()` that use `datasets.load_dataset`.  
  - Store raw streamed files (if any) under `data/raw/`.  
  - **Verification**: After execution, `data/raw/manifest.txt` lists the two dataset identifiers and the total size reported ≤ 7 GB; the loader raises an exception if download fails.

- [ ] **T003** [US‑1] **Load a ≤ 100 M‑parameter discrete diffusion model from HuggingFace**  
  - Implement `code/model.py::load_diffusion_model(model_id="hf://author/lightdiff-100m")` returning a CPU‑compatible `torch.nn.Module`.  
  - Save the model checkpoint path in `outputs/model_checkpoint.json`.  
  - **Verification**: `torch.cuda.is_available()` is **False** on the runner, yet a forward pass on a dummy batch completes in ≤ 2 s and logs “Model loaded on CPU”.

- [ ] **T004** [US‑1] **Run fixed‑density baseline experiments for ρ ∈ {0.1,0.3,0.5,0.7,0.9}**   <!-- FAILED-IN-EXECUTION: code/data.py exit=1; code/run_experiments.py exit=1 -->
  - Extend `code/trainer.py` to accept a `rho_teacher` argument and a `seed`.  
  - For each ρ and three random seeds, execute the training loop (max 10 epochs, batch 32) and write a result row to `data/results/fixed_baselines.csv` with columns `run_id, rho_teacher, seed, final_accuracy, runtime_seconds, timeout`.  
  - **Verification**: The CSV contains 15 rows, all `timeout` fields are `false`, and each `final_accuracy` is a number in `[0,1]`.

---

## Phase 2 – Adaptive scheduler & robust runtime  

- [ ] **T005** [US‑2] **Implement entropy‑based adaptive scheduler**  
  - Add `code/scheduler.py::AdaptiveScheduler` that computes prediction entropy per batch, clamps it to `[0, ln(N)]`, and maps it linearly to a new `rho_teacher` within `[0.0,1.0]`.  
  - Integrate the scheduler into `trainer.py` when `adaptive=True`.  
  - Produce a time‑series file `data/results/adaptive_density_time_series.json` (list of `{step, rho_teacher}` pairs).  
  - **Verification**: Running an adaptive run creates the JSON file with at least 20 distinct `rho_teacher` values and no NaN entries.

- [ ] **T006** [US‑2] **Add hard 6‑hour wall‑clock timeout with checkpointing**  
  - In `trainer.py`, check elapsed wall‑clock time before each epoch; if `>21600 s` abort training, save the latest model state to `outputs/checkpoints/timeout_{run_id}.pth`, and set `timeout=true` in the result record.  
  - Ensure the timeout flag propagates to the CSV/JSON result files.  
  - **Verification**: Manually invoke a long‑running run with `max_epochs=100`; after ~6 h the process exits cleanly, and the checkpoint file exists.

- [ ] **T007** [US‑2] **Execute adaptive training runs (3 seeds) and store results**  
  - Use the same hyper‑parameters as the fixed runs except `adaptive=True`.  
  - Write each run’s summary to `data/results/adaptive_runs.json` (array of `TrainingRun` objects conforming to `training_result.schema.yaml`).  
  - **Verification**: The JSON validates against `contracts/training_result.schema.yaml` (no schema errors) and contains three entries with `adaptive=true`.

---

## Phase 3 – Statistical validation & sensitivity analysis  

- [ ] **T008** [US‑3] **Perform paired t‑test (adaptive vs. fixed ρ=0.5)**  
  - Implement `code/analysis.py::run_paired_t_test(adaptive_file, fixed_file)` that extracts the three adaptive accuracies and the three fixed‑ρ=0.5 accuracies, computes a paired‑samples t‑test (SciPy), and writes `outputs/statistics/paired_t_test.json`.  
  - The JSON must contain `t_statistic`, `p_value`, and `df`.  
  - **Verification**: The file validates against `statistical_result.schema.yaml` (t_test_result fields present) and `p_value` is a number between 0 and 1.

- [ ] **T009** [US‑3] **Fit quadratic regression to the five fixed‑density accuracies**  
  - Use NumPy’s `polyfit` (degree 2) on the (ρ, accuracy) pairs from `fixed_baselines.csv`.  
  - Save coefficients `[a,b,c]` and the computed peak density `-b/(2a)` to `outputs/statistics/quadratic_fit.json`.  
  - **Verification**: The JSON contains a three‑item `quadratic_coefficients` array and a `peak_density` scalar within `[0,1]`.

- [ ] **T010** [US‑3] **Run sensitivity sweep around the identified peak density**  
  - For offsets `+0.05, -0.05, +0.10, -0.10`, invoke the trainer with the corresponding fixed ρ (clamped to `[0,1]`) using a single seed.  
  - Compute accuracy change per 0.01 density and store the four slopes in `outputs/statistics/sensitivity_analysis.json` under keys `plus_0.05`, `minus_0.05`, `plus_0.1`, `minus_0.1`.  
  - **Verification**: All four slope values are numeric and the file validates against the `sensitivity_slopes` schema.

- [ ] **T011** [US‑3] **Generate summary tables and plots**  
  - Create `outputs/figures/accuracy_vs_rho.png` (scatter + quadratic curve) and `outputs/figures/rho_over_time.png` (adaptive density time‑series).  
  - Produce a CSV summary `outputs/summary/results_table.csv` aggregating final accuracies, t‑test outcome, peak density, and sensitivity slopes.  
  - **Verification**: Both PNG files are readable image files; the CSV contains the columns `run_type, rho, final_accuracy, ...` and matches the numbers present in the JSON artifacts.

---

## Phase 4 – Reproducibility, validation & paper hand‑off  

- [ ] **T012** [US‑3] **Validate all output artifacts against their JSON‑schemas**  
  - Add a pytest module `tests/contract/test_contracts.py` that loads each JSON file in `outputs/` and validates it with `jsonschema.validate` against the corresponding schema in `specs/001-llmxive-follow-up-extending-learning-fro/contracts/`.  
  - The test suite must pass with zero failures.  
  - **Verification**: Running `pytest -q` yields `12 passed` (one test per artifact) and no schema errors.

- [ ] **T013** [US‑3] **Write the methods & results report linking to generated artifacts**  
  - Draft `docs/results.md` that describes the experimental setup, lists the fixed‑density and adaptive configurations, presents the key quantitative findings (paired‑test p‑value, peak density, sensitivity slopes), and embeds the figures from `outputs/figures/`.  
  - Include explicit file‑path references (e.g., `outputs/statistics/quadratic_fit.json`) so reviewers can locate raw numbers.  
  - **Verification**: The markdown renders without broken image links and contains a bullet list of all artifact paths.

- [ ] **T014** **Re‑run the entire pipeline from the quick‑start command to ensure end‑to‑end reproducibility**  
  - Starting from a clean checkout, execute `python -m code.run_experiments --config configs/quickstart.yaml`.  
  - Confirm that *all* files listed in `docs/results.md` are regenerated and pass the schema tests in T012.  
  - **Verification**: After the run, `git status` shows no untracked output files, and the final log prints “Pipeline completed successfully, all artifacts validated”.

---  

### Dependency Mapping  

| Requirement | Satisfied by Task(s) |
|-------------|----------------------|
| FR‑001 – dataset download | T002 |
| FR‑002 – lightweight diffusion model | T003 |
| FR‑003 – fixed‑density training | T004 |
| FR‑004 – adaptive scheduler | T005 |
| FR‑005 – 6‑hour timeout | T006 |
| FR‑006 – **paired** t‑test | T008 |
| FR‑007 – sensitivity analysis | T010 |
| FR‑008 – quadratic fit | T009 |
| US‑1 – baseline convergence | T004, T007 |
| US‑2 – adaptive scheduler | T005, T007 |
| US‑3 – statistical validation | T008‑T012 |
| SC‑001‑SC‑006 – measurable outcomes | T004‑T011, T013‑T014 |

All tasks respect the data‑flow ordering: data acquisition → model loading → baseline runs → adaptive run → analysis → validation → documentation.  

---  
