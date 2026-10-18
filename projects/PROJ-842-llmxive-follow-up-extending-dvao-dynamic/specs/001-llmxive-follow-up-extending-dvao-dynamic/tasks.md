# Tasks: llmXive follow‑up – extending “DVAO: Dynamic Variance‑adaptive Advantage Optimization for Multi‑reward”

**Inputs**: `spec.md`, `plan.md`, existing code base under `code/`, data‑model contracts in `specs/001-llmxive-follow-up-extending-dvao-dynamic/contracts/`.  
**Goal**: Produce a complete, reproducible study that (1) derives a closed‑form variance‑scaling law and sample‑complexity lower bound, (2) validates it on synthetic multi‑objective tabular MDPs under strict CPU‑only resource limits, (3) performs sensitivity analyses (window size k, noise correlation ρ, reward‑distribution type), (4) demonstrates construct‑validity on a held‑out heavy‑tailed set, and (5) hands off all artifacts for paper generation.

---

## Phase 0 – Project foundation & verification

- [ ] T000 [P] **Run citation verification & checksum recording** – execute `src/verification/verify_citations.py`, pin all random seeds, compute SHA‑256 checksums for every file under `data/`, and store them in `state/artifact_hashes.yaml`.  
  *Verification*: `python -m src.verification.verify_citations && python -c "import yaml, pathlib; h=yaml.safe_load(open('state/artifact_hashes.yaml')); assert isinstance(h, dict)"`.

- [ ] T001 [P] **Create project entry point & config** – add `src/main.py` with an `if __name__ == "__main__":` CLI that loads a YAML config, and create `src/config/defaults.yaml` (default N=5, k=0.01, rho=0, distribution=linear) plus `config/small_demo.yaml` (tiny demo config).  
  *Verification*: `python src/main.py --config config/small_demo.yaml && echo "OK"`.

- [ ] T002 [S] **Run minimal end‑to‑end example** – execute the quickstart command with the small demo config, producing `data/processed/empirical_results.json`. Validate against the JSON schema using `jsonschema.validate`.  
  *Verification*: `python -m src.main --config config/small_demo.yaml && python -c "import json, jsonschema, yaml; schema=yaml.safe_load(open('specs/001-llmxive-follow-up-extending-dvao-dynamic/contracts/empirical_results.schema.yaml')); instance=json.load(open('data/processed/empirical_results.json')); jsonschema.validate(instance, schema)"`.

---

## Phase 1 – Theoretical derivation (User Story 1, P1)

- [ ] T003 [S] **Derive variance‑scaling law** – implement `src/derivation/variance_scaling.py` using **sympy** to symbolically compute `Var(A)` for a weighted advantage function with `N` independent noises `ε_i`. Export a single file `data/processed/theoretical_bound.json` containing the fields `n_range`, `variance_equation`, `sample_complexity_bound`, and `assumptions`.  
  *Verification*: `python -c "import json; d=json.load(open('data/processed/theoretical_bound.json')); assert all(k in d for k in ['variance_equation','sample_complexity_bound'])"`.

- [ ] T004 [S] **Verify derivation algebraically** – add `src/derivation/verify_symbolic.py` that loads the expression from `theoretical_bound.json`, simplifies it, and checks equality against the manually‑derived form `N*σ²`. Write a log `data/processed/derivation_verification.json` with `status: "PASS"`.  
  *Verification*: `python src/derivation/verify_symbolic.py && python -c "import json; assert json.load(open('data/processed/derivation_verification.json'))['status']=='PASS'"`.

- [ ] T005 [S] **Invert variance to sample‑complexity bound** – extend `src/derivation/sample_complexity.py` to read `theoretical_bound.json`, solve for the minimal sample count `K(N,σ,ε_target)` achieving a target error, and write the bound back into the same JSON under the key `sample_complexity_bound`.  
  *Verification*: `python src/derivation/sample_complexity.py && python -c "import json; d=json.load(open('data/processed/theoretical_bound.json')); assert 'sample_complexity_bound' in d"`.

- [ ] T006 [S] **Generate human‑readable derivation report** – extend `src/derivation/sample_complexity.py` with a `--generate-docs` flag that produces `docs/theoretical_derivation.md` containing the sympy expression, step‑by‑step algebra, assumptions, and the closed‑form bound.  
  *Verification*: `python src/derivation/sample_complexity.py --generate-docs && grep -q "Sample Complexity" docs/theoretical_derivation.md`.

---

## Phase 2 – Synthetic environment generation (User Story 2, P2)

- [ ] T007 [S] **Generate tabular MDPs** – implement `src/environment/synthetic_mdp.py` with function `generate_mdp(n_objectives, seed, rho, distribution)` creating a tabular MDP (state = 200, action = 5) and `N` reward functions as random linear combinations of state features. Support **linear**, **sparse**, **non‑convex** families. When `n_objectives > 50` the function reduces `effective_state_space_size` by a factor of 2 (as required by FR‑016) and logs the reduction.  
  *Verification*: `python -c "from src.environment.synthetic_mdp import generate_mdp; mdp=generate_mdp(60,seed=1,rho=0,distribution='linear'); assert mdp['effective_state_space_size']==100"`.

- [ ] T008 [S] **Log achieved noise correlation** – extend the generator to compute the empirical correlation matrix of injected noise and write a summary (`rho_target`, `rho_actual_mean`, `correlation_matrix_snapshot`) to `data/processed/noise_properties.json`.  
  *Verification*: `python -c "import json; d=json.load(open('data/processed/noise_properties.json')); assert 'rho_target' in d"`.

- [ ] T009 [S] **Resource‑guard for large N** – in `src/environment/runner.py` add logic: if `N>50` reduce `effective_state_space_size` by a factor of 2, enforce **2 CPU cores** (`os.sched_setaffinity`) and **≤ 7 GB RAM** (monitor via `psutil`). On limit breach exit with code 1 and print `ResourceLimitExceeded` to stderr. Log `effective_n`, `effective_state_space_size`, and `degraded_flag` to `data/processed/resource_log.json`.  
  *Verification*: `python src/environment/runner.py --n 60 --seed 0 && echo $? && grep -q "ResourceLimitExceeded" <(python src/environment/runner.py --n 60 --seed 0 2>&1)`.

- [ ] T009a [S] **Verify graceful failure (FR‑005)** – run the runner with deliberately excessive memory/CPU settings and assert exit code 1 and correct stderr message.  
  *Verification*: `python src/environment/runner.py --n 200 --seed 0 2>err.txt; grep -q "ResourceLimitExceeded" err.txt && [ $? -eq 1 ]`.

- [ ] T010 [S] **Runner orchestration script** – create `src/environment/runner.py` that loads an MDP, runs a configurable number of episodes, respects the resource guard, and writes per‑run metrics (including convergence speed) to `data/processed/empirical_results/<experiment_id>.json`.  
  *Verification*: `python src/environment/runner.py --config config/small_demo.yaml && test -f data/processed/empirical_results/run_001.json`.

---

## Phase 3 – Heuristic & baseline implementation (User Story 2, P2)

- [ ] T011 [S] **Moving‑Window variance heuristic** – implement `src/analysis/heuristic.py` with `estimate_variance(trajectory, window_frac)` that uses the last `k = int(window_frac * len(trajectory))` steps. Enforce `window_frac ∈ {0.01,0.05,0.1}`; raise `ValueError` for smaller values. Store per‑run estimates in `data/processed/heuristic_estimates/<experiment_id>.json` and also record **per‑step ratio** (`heuristic_variance / full_batch_variance`) in `data/processed/heuristic_step_ratios/<experiment_id>.json`.  
  *Verification*: `python -c "from src.analysis.heuristic import estimate_variance; import numpy as np; assert estimate_variance(np.arange(100),0.05)>0"`.

- [ ] T012 [S] **Full‑batch variance ground truth** – implement `src/analysis/full_batch_variance.py` that computes the variance of the advantage function over the entire trajectory (FR‑013) and writes `data/processed/full_batch_variance/<experiment_id>.json`.  
  *Verification*: `python -c "import json; d=json.load(open('data/processed/full_batch_variance/run_001.json')); assert 'full_batch_variance' in d"`.

- [ ] T013 [S] **Statistical bias & stability analysis** – using outputs from T011, T012, and the per‑step ratio files, compute:  
    * mean bias (`heuristic_variance_mean – full_batch_variance_mean`)  
    * TOST equivalence test for bias with margin ±0.05 (FR‑015)  
    * one‑sample t‑test for bias (additional check)  
    * stability rate: percentage of steps where ratio lies in `[0.9,1.1]` (SC‑003)  
    * false‑positive rate based on the stability test (SC‑004)  
  Write results to `data/processed/bias_stability_report/<experiment_id>.json`.  
  *Verification*: `python src/analysis/bias_stability.py && test -f data/processed/bias_stability_report/run_001.json`.

- [ ] T014 [S] **Static scalarization baseline** – implement `src/analysis/baseline.py` that evaluates a fixed weight vector `w` on each trajectory and records the sample count needed to reach the Pareto‑threshold. Output to `data/processed/baseline_results/<experiment_id>.json`.  
  *Verification*: `python -c "import json; d=json.load(open('data/processed/baseline_results/run_001.json')); assert 'sample_count' in d"`.

---

## Phase 4 – Full experimental sweep (User Stories 2‑3, P2‑P3)

- [ ] T015 [S] **Run exhaustive sweep** – orchestrate runs over all combinations of  
  * `N ∈ {5,10,15,20,30,40,50}`  
  * `k ∈ {0.01,0.05,0.1}`  
  * `ρ ∈ {0,0.2,0.5}`  
  * `distribution ∈ {linear, sparse, non_convex}`  
  ensuring **≥30 independent runs per configuration** (≥50 for final analysis). Each run invokes the pipeline (T007‑T014) and writes its result JSON under `data/processed/empirical_results/`.  
  *Verification*: `python src/analysis/run_sweep.py && python -c "import pathlib, json; files=list(pathlib.Path('data/processed/empirical_results').glob('*.json')); assert len(files) >= 7*3*3*3*30"`.

- [ ] T016 [S] **Statistical validation** – in `src/analysis/statistics.py` compute:  
  * Linear regression of `sample_count` vs `N` (log‑log) → slope, `R²`.  
  * **TOST equivalence test** for the slope against the theoretical slope (margin ± 0.1) (FR‑006).  
  * Incorporate bias TOST results from T013.  
  * One‑sample t‑test for heuristic bias (additional check).  
  * Binomial test for false‑positive rate (SC‑004).  
  * Noise sanity‑check (FR‑014) confirming ≤5 % relative error.  
  Write `data/processed/statistical_report.json` conforming to `statistical_report.schema.yaml`.  
  *Verification*: `python src/analysis/statistics.py && python -c "import json, yaml, jsonschema; schema=yaml.safe_load(open('specs/001-llmxive-follow-up-extending-dvao-dynamic/contracts/statistical_report.schema.yaml')); instance=json.load(open('data/processed/statistical_report.json')); jsonschema.validate(instance, schema)"`.

---

## Phase 5 – Pareto oracle & distance computation

- [ ] T017 [S] **Pareto oracle implementation** – add `src/analysis/pareto_oracle.py` that computes the weighted‑sum Pareto frontier with step 0.01, returns the distance of the final policy to this frontier, and writes `pareto_frontier_distance` into each entry of the corresponding `empirical_results` JSON file.  
  *Verification*: `python src/analysis/pareto_oracle.py && python -c "import json, pathlib; f=next(pathlib.Path('data/processed/empirical_results').glob('*.json')); d=json.load(open(f)); assert 'pareto_frontier_distance' in d"`.

---

## Phase 6 – Held‑out validation & construct validity (User Stories 4‑5, P4‑P5)

- [ ] T018 [S] **Generate heavy‑tailed held‑out set** – sample reward noise from a Student‑t distribution (df = 3) to create `data/derived/heavy_tailed_set.json` and a separate validation split `data/derived/heavy_tailed_validation.json`.  
  *Verification*: `python -c "import json; d=json.load(open('data/derived/heavy_tailed_set.json')); assert len(d)>0"`.

- [ ] T019 [S] **Run heuristic on heavy‑tailed set & compare to bound** – execute the full pipeline on the held‑out set, compute empirical sample complexity, compare against the theoretical bound, and flag deviations >10 % in `data/processed/heavy_tailed_validation_report.json`.  
  *Verification*: `python src/analysis/run_heavy_tailed.py && python -c "import json; d=json.load(open('data/processed/heavy_tailed_validation_report.json')); assert d['deviation_percent'] <= 10"`.

- [ ] T020 [S] **Construct‑validity across reward families** – add `scripts/validate_construct_validity.py` that loads each reward‑distribution type (linear, sparse, non‑convex, heavy‑tailed), runs the full sweep (re‑using T015), aggregates results, and writes `data/processed/construct_validity_results.json` conforming to `construct_validity_results.schema.yaml`.  
  *Verification*: `python scripts/validate_construct_validity.py && python -c "import json; d=json.load(open('data/processed/construct_validity_results.json')); assert all(v['pass_criteria_met'] for v in d)"`.

- [ ] T021 [S] **Descriptive‑statistics comparison to published LLM‑reward stats** – compute mean, variance, skewness of generated rewards and compare to published RLHF reward statistics (e.g., OpenAI logs). Store results in `data/processed/llm_reward_stats_comparison.json`.  
  *Verification*: `python src/analysis/compare_llm_stats.py && python -c "import json; d=json.load(open('data/processed/llm_reward_stats_comparison.json')); assert 'llm_reference' in d"`.

- [ ] T022 [S] **Generate regression & Pareto‑distance plots** – using `matplotlib`, produce `figures/regression_slope.png`, `figures/pareto_distance.png`, and record the file paths in `docs/final_report.md`. Verify that the PNG files exist.  
  *Verification*: `python src/analysis/plot_results.py && test -f figures/regression_slope.png && test -f figures/pareto_distance.png`.

---

## Phase 7 – Reporting & reproducibility hand‑off (User Story 6, P6)

- [ ] T023 [S] **Assemble final research report** – generate `docs/final_report.md` that (a) summarizes the derived bound, (b) presents tables/figures derived directly from the JSON artifacts (`empirical_results`, `statistical_report`, `construct_validity_results`, `llm_reward_stats_comparison`), (c) discusses resource‑guard behavior, (d) lists limitations, and (e) hyperlinks all underlying data files.  
  *Verification*: `python src/report/generate_report.py && grep -q "data/processed/empirical_results" docs/final_report.md`.

- [ ] T024 [S] **End‑to‑end reproducibility script** – create `run_full_pipeline.sh` that runs (T000 → T001 → T002 → T003‑T006 → T007‑T010 → T011‑T014 → T015 → T016 → T017‑T022 → T023) in sequence, exits with non‑zero code on any failure, and logs a summary to `logs/pipeline_summary.log`.  
  *Verification*: `bash run_full_pipeline.sh && echo $?` should be `0`.

- [ ] T025 [P] **Final CI verification** – CI runs `run_full_pipeline.sh`, then executes `scripts/check_report_links.py` to ensure every figure/table reference in `final_report.md` resolves to an existing file.  
  *Verification*: `python scripts/check_report_links.py && echo "CI passed"`.

---

## Phase 8 – Pending reviewer‑raised issues (merged)

- The earlier duplicate tasks T087 and T089 have been merged into T008 and T020 respectively.

---

### Dependency & requirement mapping (updated)

| Requirement | Implementing Task(s) |
|-------------|----------------------|
| FR‑001, FR‑002 | T003, T004, T005 |
| FR‑003, FR‑014, FR‑016, FR‑012 | T007, T008, T009 |
| FR‑004, FR‑013 | T011, T012 |
| FR‑005, FR‑016 | T009, T009a |
| FR‑006, FR‑007, FR‑009, FR‑010 | T015, T016, T020 |
| FR‑018, FR‑019 | T014 |
| FR‑015 | T013 (TOST bias test) |
| FR‑017 | T017 |
| SC‑001‑SC‑007 | T004, T016, T021 |
| Resource limits (2 CPU, ≤ 7 GB) | T009 |
| Validation independence (held‑out set) | T018, T019 |
| Additional support tasks | T023, T024, T025 |

All tasks respect data‑flow ordering, resource constraints, and the single‑source‑of‑truth principle.

*All tasks are unchecked (`[ ]`).* 