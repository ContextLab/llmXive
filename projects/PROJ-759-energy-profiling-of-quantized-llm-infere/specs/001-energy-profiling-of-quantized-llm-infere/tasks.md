# Tasks: Energy Profiling of Quantized LLM Inference on Edge CPUs

**Inputs**: `spec.md`, `plan.md`, existing project layout, reviewer feedback, and the data‑model contracts in `specs/001-energy-profiling-of-quantized-llm-infere/contracts/`.

---

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Verify that a minimal CPU‑only inference run can be executed, measured for energy, and stored in the canonical schema.

- [ ] T001 [P1] Establish a reproducible environment, document the runnable command in `quickstart.md`, and verify that the `pyRAPL` (or fallback `powerstat`) library loads on the GitHub Actions runner.  
  *Path*: `code/quickstart.md`  
  *Verification*: `pytest -k test_pyrapl_load` passes; the quickstart command `python -m code.benchmark --config data/configs/125M_4bit.json --dry-run` prints “pyRAPL available”.

- [ ] T002 [P1] Download the WikiText‑2 dataset (streaming) and store it under `data/raw/wikitext2.parquet`. Record the SHA‑256 checksum in `data/raw/README.md`.  
  *Path*: `code/utils/data_loader.py` → writes to `data/raw/wikitext2.parquet`  
  *Verification*: `pytest -k test_wikitext2_download` confirms file exists and checksum matches.

- [ ] T003 [P1] Acquire GPT‑Neo checkpoints for the three model sizes (125 M, 350 M, 1.3 B) and generate INT8 and 4‑bit variants using `auto‑gptq`. For each variant create a **Configuration** JSON file under `data/configs/` and a corresponding entry in `contracts/config.schema.yaml`.
  *Path*: `code/utils/quantize.py` → writes `data/configs/gptneo-125M_fp16.json`, `..._int8.json`, `..._4bit.json`, etc.  
  *Verification*: each JSON validates against `contracts/config.schema.yaml`; OOM attempts for 7 B models are logged in `logs/model_load.log` and marked `load_success: false`.

- [ ] T004 [P1] Implement the primary inference‑benchmark script `code/benchmark.py` that (a) measures a 10 s idle baseline, (b) runs **five** repetitions per configuration with distinct seeds (42, 123, 999, 2026, 777)—noting that the spec's example test uses 3 repetitions for validation purposes, (c) repeats the process for prompt lengths of 250, 500, and 1000 tokens to satisfy Constitution Principle VII, (d) records raw energy (J), latency (ms), token count, and perplexity, and (e) writes one `InferenceRun` JSON per repetition under `data/results/runs/`. If energy measurement is unavailable (per FR-002), the script MUST log the event and skip writing the JSON for that run to avoid schema violations.  
  *Path*: `code/benchmark.py` → outputs `data/results/runs/<config_id>_<length>_run0.json` … `run4.json`  
  *Verification*: `pytest -k test_inference_run_schema` validates each JSON against `contracts/inference_run.schema.yaml`; a quick sanity check on the 125 M 4‑bit config confirms non-zero energy and latency < 10 min.

---

## Phase 2 – Complete the study and validate its evidence  

- [ ] T005 [P2] Aggregate the `InferenceRun` records for **every** successful configuration into a single `AggregatedMetric` CSV (`data/results/aggregated.csv`), including a breakdown by prompt length. Compute mean ± std for energy‑per‑token, latency, perplexity, and set the `dequantization_overhead_flag` and `variance_stability_flag` according to the thresholds in the spec.  
  *Path*: `code/utils/aggregate.py` → writes `data/results/aggregated.csv`  
  *Verification*: `pytest -k test_aggregated_schema` validates each row against `contracts/aggregated.schema.yaml`; the `variance_stability_flag` is true for all configurations where `std/mean ≤ 0.15`.

- [ ] T006 [P3] Perform the statistical analysis required by FR‑005 and Constitution Principle VII:  
  1. Fit a multiple‑regression OLS model `log(Energy_per_token) ~ log(Parameter_count) + Quantization`.  
  2. Conduct a sensitivity analysis of energy‑per‑token across the three prompt lengths (250, 500, 1000).  
  3. Conduct assumption checks (Shapiro‑Wilk, Levene) and fall back to non‑parametric tests when needed.  
  4. Run pairwise t‑tests (Bonferroni‑corrected) or Wilcoxon tests between quantization levels.  
  5. Compute the dequantization‑overhead flag (≥ **10 %** increase & significant per FR-007).  
  6. Produce a `summary.json` containing the fitted exponent, p‑values, and flags.  
  *Path*: `code/stats/analysis.py` → writes `data/results/summary.json`  
  *Verification*: `pytest -k test_analysis_output` confirms JSON keys exist and that at least one quantization comparison yields a p‑value < 0.05 (or a clear “non‑significant” flag).

- [ ] T007 [P3] Generate the required visualizations and store them under `paper/figures/`:  
  * a) Bar plot of mean energy‑per‑token for each quantization level (grouped by model size).  
  * b) Log‑log scatter of energy‑per‑token vs. parameter count with fitted regression lines per quantization.  
  * c) A sensitivity plot showing energy‑per‑token as a function of prompt length.  
  * d) CPU frequency/throttling trace captured during a representative run.  
  *Path*: `code/visualization/plotting.py` → writes `paper/figures/energy_bar.png`, `paper/figures/energy_loglog.png`, `paper/figures/energy_sensitivity.png`, `paper/figures/cpu_trace.png`.  
  *Verification*: `pytest -k test_figures_exist` checks that all four PNG files are present and non‑empty.

- [ ] T008 [P2] Validate the complete pipeline end‑to‑end by re‑executing the workflow from `quickstart.md` on a fresh runner: the command `bash run_all.sh` must (a) download data, (b) quantize models, (c) run benchmarks (including sensitivity lengths), (d) aggregate, (e) analyse, and (f) produce the figures and `summary.json`.  
  *Path*: `run_all.sh` (or equivalent CI script).  
  *Verification*: CI logs contain “Pipeline completed successfully” and the artifact hashes in `state/project_state.yaml` match the newly generated files.

---

## Phase 3 – Reproducible results and paper handoff  

- [ ] T009 [P3] Write a concise methods/results handoff document `paper/methods_results.md` that (a) describes each artifact path, (b) cites the exact version numbers from `requirements.txt`, (c) reports the fitted scaling exponent and whether it is sub‑linear (< 1), (d) lists all significant quantization effects and prompt length sensitivity results, and (e) notes any configurations that were skipped due to OOM.  
  *Path*: `paper/methods_results.md`  
  *Verification*: Manual reviewer check; the file must reference `data/results/aggregated.csv`, `summary.json`, and the four PNGs.

- [ ] T010 [optional] Edge‑hardware validation on a self‑hosted Raspberry Pi 4 runner. Replicate the full benchmark for the 125 M and 350 M models (FP16, INT8, 4‑bit) and store results under `data/edge_results/`. Compare the trends to the x86 CI results and add a short note in `paper/methods_results.md` about fidelity.  
  *Path*: `code/edge_benchmark.py` → writes `data/edge_results/*.json` and `data/edge_results/aggregated_edge.csv`.  
  *Verification*: `pytest -k test_edge_consistency` asserts that the direction of energy‑per‑token change across quantizations matches the main experiment (signs of differences are identical).

---

## Dependencies & Requirement Coverage  

| Specification | Satisfied by Task(s) |
|---------------|----------------------|
| FR‑001 | T003 (model download & quantization) |
| FR‑002 | T004 (energy measurement wrapper & unavailability handling) |
| FR‑003 | T004 (five repetitions with distinct seeds) |
| FR‑004 | T005 (aggregation of means/stds) |
| FR‑005 | T006 (log‑log OLS, t‑tests, Bonferroni) |
| FR‑006 | T007 (visualization generation) |
| FR‑007 | T006 (dequantization‑overhead flag ≥ 10%) |
| SC‑001 | T006 (energy‑per‑token comparison to FP16) |
| SC‑002 | T006 (pairwise significance, α = 0.05 / 3) |
| SC‑003 | T006 (log‑log exponent reporting) |
| SC‑004 | T005 (std/mean ≤ 0.15 flag) |
| Principle VII | T004, T005, T006, T007 (Prompt length sensitivity analysis) |

All tasks respect data flow ordering (e.g., T005 runs after T004) and write only to project‑owned directories (`data/`, `code/`, `paper/`). No task fabricates data; every measurement relies on real dataset downloads and real energy counters (`pyRAPL` or `powerstat`).