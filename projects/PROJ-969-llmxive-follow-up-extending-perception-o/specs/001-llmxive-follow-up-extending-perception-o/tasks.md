# Tasks: Does context injection reduce the MLLM “Prejudice Gap” (reasoning deficit vs. visual limitation)?

**Inputs**: `spec.md`, `plan.md`, data‑model contracts in `specs/001-llmxive-follow-up-extending-perception-o/`, and the verified open dataset `mmbench/ocean` (https://huggingface.co/datasets/mmbench/ocean).

---  

### Phase 1 – Setup and first end‑to‑end analysis  

- [ ] **T001** [S] [US‑1] Acquire and validate the primary dataset (FR‑001).   <!-- FAILED-IN-EXECUTION: code/src/data/load_dataset.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/data/load_dataset.py exit=1 -->
  *Implement `code/src/data/load_dataset.py` that streams the `mmbench/ocean` validation split via `datasets.load_dataset("mmbench/ocean", split="validation", streaming=True)`, writes normalized records to `data/raw/video_metadata.jsonl` (validated against `specs/001-llmxive-follow-up-extending-perception-o/contracts/video_metadata.schema.yaml`), computes and records a SHA‑256 checksum in `data/raw/checksums.json`, and updates `quickstart.md` with the runnable command `python -m code.src.data.load_dataset`.  
  *Verification: `pytest code/tests/test_load_dataset.py` must pass; the loader must raise on any fetch or parse error (no synthetic fallback).  

- [ ] **T002** [S] [US‑2] Build the static context knowledge base (FR‑002, FR‑009).  
  *Implement `code/src/context/knowledge_base.py` that reads the metadata from `data/raw/video_metadata.jsonl`, curates a JSON knowledge base `data/context/knowledge_base.json` mapping `(setting, culture)` to social‑norm and script lists (validated against `context_profile.schema.yaml`), includes a generic “neutral‑context” fallback profile, and logs a warning when a video lacks a specific situational tag.  
  *Verification: `pytest code/tests/test_knowledge_base.py` must pass; coverage of specific profiles vs. neutral fallback is reported in `data/derived/context_coverage.json` (target ≥ 90 %).  

- [ ] **T003** [S] [US‑3] Implement prompt templates and condition‑order randomisation (FR‑004, FR‑006, FR‑023).  
  *Create `code/src/prompts/templates.py` with three templates: (a) **baseline** (injects a neutral‑context profile so that a citation phrase is always present), (b) Context‑Grounded Chain‑of‑Thought (injects the retrieved specific profile and requires citation), and (c) noise‑control (length‑matched gibberish plus neutral‑context).  
  *Create `code/src/prompts/order.py` that deterministically permutes the three conditions per model‑video pair using `np.random.default_rng(42)` and writes `data/derived/condition_order_log.json`.  
  *Verification: `pytest code/tests/test_prompts.py` checks template integrity, equalised length, and reproducible order log.  

- [ ] **T014** [S] [US‑3] Perform a priori power analysis (FR‑019, SC‑010).  
  *Implement `code/src/analysis/power.py` to compute the required number of video samples for ≥ 80 % power to detect a moderate effect size (Cohen’s d ≈ 0.5) in a paired mixed‑effects design (α = 0.05, ICC ≈ 0.10).  
  *Write results to `data/derived/power_analysis.json`. If the required sample size exceeds the validation split, record the shortfall for escalation (no data fabrication).  
  *Verification: `pytest code/tests/test_power.py` validates the calculation against a closed‑form reference.  

- [ ] **T004** [US‑1] Run a pilot inference end‑to‑end (CPU‑only).  
  *Implement `code/src/inference/run_inference.py` that loads each model listed in `data/model_ensemble.json` (≤ 2 B parameters, CPU‑runnable, int8‑quantised), applies the three conditions in the order from `condition_order_log.json`, and processes a fixed‑seed pilot of 10 videos (≤ 10 frames per video).  
  *Outputs conform to `model_output.schema.yaml` and are written to `data/derived/pilot_outputs.jsonl`. Malformed JSON is retried twice then flagged with `valid_json=False` (FR‑010).  
  *Verification: `pytest code/tests/test_output_schema.py` validates every record; the driver is invoked via `python -m code.src.inference.run_inference --pilot`.  

---  

### Phase 2 – Complete the study and validate its evidence  

- [ ] **T005** [US‑4] Project resource usage and apply the pre‑registered fallback (FR‑007, FR‑022).  
  *From the pilot, `code/src/inference/projection.py` estimates total wall‑clock time and peak RAM for the full run. If projected runtime > 6 h **or** RAM > 7 GB, the deterministic fallback (top‑15 models + 10‑frame sampling) is applied uniformly across all conditions and recorded in `data/derived/resource_projection.json`. If the fallback still exceeds the budget, a scope‑mismatch entry is written and the pipeline halts for spec amendment.  
  *Verification: `pytest code/tests/test_projection.py` checks the projection logic and that the decision flag is deterministic.  

- [ ] **T006** [US‑1][US‑2] Execute the full inference (FR‑003, FR‑004, FR‑006).  
  *Extend `code/src/inference/run_inference.py` with `--full` to run the chosen model ensemble and video subset (as decided by T005) under batch size ≤ 20, recording per‑call timing.  
  *All outputs are written to `data/derived/outputs.jsonl` (schema‑validated). The run must complete within the 6‑hour / 7 GB budget; the final configuration (model list, video IDs, frame count) is saved in `data/derived/run_config.json`.  
  *Verification: post‑run checks confirm that the sample size meets or exceeds the requirement from `power_analysis.json` and that the invalid‑output rate ≤ 5 % (SC‑008).  

- [ ] **T007** [US‑1][US‑2] Calibrate grounding‑validity assessment (FR‑020, FR‑018, deviation #2).  
  *Implement `code/src/metrics/grounding.py` to compute cosine similarity between each model’s reasoning string and the ground‑truth behavioral evidence tags using the frozen sentence‑transformer `all‑MiniLM‑L6‑v2`.  
  *On the 30‑sample pilot (from T004), obtain two independent manual dichotomisations (valid/invalid grounding) and compute Cohen’s κ; require κ ≥ 0.8. Choose the similarity threshold that maximises agreement (default 0.70) and record the calibration details in `data/derived/threshold_calibration.json`.  
  *Flag samples with ≥ 2 contradictory behavior tags as “grounding‑uncertainty” (FR‑011) and exclude them from primary calculations.  
  *Verification: `pytest code/tests/test_grounding.py` validates similarity computation, κ calculation, and the ambiguity‑flag rule.  

- [ ] **T008** [US‑1][US‑2] Compute per‑model, per‑condition metrics and SC‑004/SC‑009 checks (FR‑008, FR‑010, FR‑018).  
  *Implement `code/src/metrics/compute_metrics.py` that reads `outputs.jsonl` and the grounding scores from T007, then writes `data/derived/metrics.jsonl` (one `MetricRecord` per model × condition, validated against `metric_record.schema.yaml`).  
  *Calculate **Prejudice Rate (PR)** using the spec definition: `#(correct rating ∧ grounding_invalid) / #(total ratings)`. Compute **Holistic‑Grounding Rate (HR)** as `#(correct rating ∧ grounding_valid) / #(total ratings)`. Compute **Integration‑Failure Rate (IR)** as `#(output does NOT cite any injected context phrase) / #samples` for **all** conditions (baseline, context, noise).  
  *Enforce SC‑004 by verifying that ≥ 95 % of model outputs in **every** condition contain a valid reasoning string **and** cite an injected context phrase (detected via fuzzy token‑overlap ≥ 0.8). Record the result in `data/derived/sc004_check.json`.  
  *If the proportion of grounding‑uncertainty samples exceeds 10 %, generate `data/derived/data_quality_supplement.json`; otherwise record the proportion and pass.  
  *Verification: `pytest code/tests/test_metrics.py` checks formulas on hand‑crafted fixtures, validates the citation detection method, and ensures the conditional SC‑004 logic holds for all conditions.  

- [ ] **T009** [US‑3] Statistical analysis with power verification (FR‑005, FR‑019, SC‑010).  
  *Implement `code/src/analysis/stats.py` to fit the primary mixed‑effects model (binary “grounding_invalid” outcome, random intercepts for video and model, fixed effect for condition) using `statsmodels.MixedLM`. Also run paired t‑test/Wilcoxon as secondary checks and compare intervention vs. noise control. Apply Bonferroni correction across the three primary contrasts.  
  *Update `data/derived/power_analysis.json` with the achieved power for the observed sample size; if achieved power < 0.80, record the shortfall and its implications (no silent drop).  
  *Verification: `pytest code/tests/test_stats.py` runs the analysis on a synthetic fixture with a known effect size to ensure correct p‑values and confidence intervals.  

- [ ] **T010** [US‑3] Sensitivity sweep and quantisation‑impact control (FR‑021, SC‑005, SC‑011).  
  *Implement `code/src/analysis/sensitivity.py` to recompute PR/HR for grounding thresholds {0.65, 0.70, 0.75} and write `data/derived/sensitivity_sweep.json`.  
  *Implement `code/src/inference/run_inference.py --quant-control` to re‑run exactly 5 models (selected by a fixed seed) at 8‑bit quantisation (and a tiny full‑precision control) for baseline and context conditions; write results to `data/derived/quantisation_impact.json` and verify that ΔPR ≤ 5 % (SC‑011).  
  *Verification: `pytest code/tests/test_sensitivity.py` and `pytest code/tests/test_quant_control.py` validate the sweep and the ΔPR bound.  

- [ ] **T011** [US‑3] Generate tables and figures from validated outputs (FR‑005, SC‑001‑SC‑012).  
  *Implement `code/src/reporting/figures.py` to produce:  
    - `figures/pr_by_model_condition.png` (PR per model & condition)  
    - `figures/hr_ir_by_model.png` (HR and IR per model)  
    - `figures/sensitivity_sweep.png` (threshold sweep)  
    - CSV tables `data/derived/metrics_table.csv` and `data/derived/stats_table.csv`.  
  *All figures are derived solely from `data/derived/*.json[l]`.  
  *Verification: `pytest code/tests/test_figures.py` ensures deterministic generation from the source artifacts.  

---  

### Phase 3 – Reproducible results and paper handoff  

- [ ] **T012** Write the methods & results markdown (`paper/results.md`).  
  *Link every numeric claim and figure to its originating artifact (`data/derived/*.json[l]` or `figures/*`). Include the dataset substitution note (mmbench/ocean vs. MM‑OCEAN), resource‑budget status, power analysis outcome, neutral‑context fallback coverage, SC‑004 status per condition, and any data‑quality supplement.  
  *Verification: `pytest code/tests/test_results_traceability.py` checks that each claim in `paper/results.md` traces to an existing artifact.  

- [ ] **T013** Implement the single orchestrator (`code/src/run_all.py`).  
  *Entry point `python -m code.src.run_all` chains the full pipeline: dataset acquisition → knowledge‑base construction → pilot inference → resource projection → full inference → grounding calibration → metric computation → statistical analysis → sensitivity & quantisation checks → figure generation → results markdown.  
  *Re‑run the documented workflow from `quickstart.md` and confirm that all `pytest` suites pass and all artifact‑validation checks succeed. Document the paper‑stage handoff (list of result files, figures, and the location of `paper/results.md`).  

---  

## Dependency & Requirement Coverage  

| Requirement | Task(s) |
|-------------|---------|
| FR‑001 | T001 |
| FR‑002, FR‑009 | T002 |
| FR‑003, FR‑004, FR‑006, FR‑010, FR‑023 | T003, T004, T006 |
| FR‑005 | T009 |
| FR‑007, FR‑022 | T005 |
| FR‑008, FR‑018 | T008 |
| FR‑011, FR‑020 | T007 |
| FR‑019 (power) | T014, T006, T009 |
| FR‑021 | T010 |
| SC‑001, SC‑002, SC‑003, SC‑004, SC‑005, SC‑006, SC‑007, SC‑008, SC‑009, SC‑010, SC‑011, SC‑012 | T001‑T013 (as indicated in each task) |

**Execution order**:  

T001 → (T002, T003, T014) → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013.  

---  

*All tasks are unchecked; the CI pipeline will mark them as completed only when the corresponding scripts, tests, and artifact validations succeed.*  