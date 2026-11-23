# Implementation Plan: Energy Profiling of Quantized LLM Inference on Edge CPUs

**Branch**: `001-energy-profiling-of-quantized-llm-infere` | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-energy-profiling-of-quantized-llm-infere/spec.md`

## Summary

Quantify how FP16, INT8, and 4‑bit quantization affect energy‑per‑token during CPU‑only inference across three parameter scales (on the order of a hundred million parameters, ≈1.3 B, optional ≈2.7 B), controlling for model size via a log‑log OLS scaling regression with quantization covariates and interactions, plus Bonferroni‑corrected pairwise comparisons. This revision repairs prior gaps (T001/T003, power claim, dataset/model mismatches) and addresses all reviewer concerns.

### Key Corrections
1. **Repetitions = 12** (FR‑003) with pinned seeds `[42, 123, 999, 2026, 777, 1111, 2222, 3333, 4444, 5555, 6666, 8888]`.
2. **Power claim (SC‑006)**: realistic power analysis ([deferred] at n=12) is computed and reported; the spec’s ≥90 % claim is flagged as infeasible. The plan now **computes and reports achieved power** and notes the limitation.
3. **Quantization stack**: `torchao` INT8/INT4 weight‑only quantization (CPU‑only) is primary; fallback `torch.quantization.quantize_dynamic` for INT8. Failures are recorded as `quantization_status: failed`. No silent FP16 substitution.
4. **Model family**: unified to the **GPT‑Neo** family for the size axis (125 M, 1.3 B, optional 2.7 B if RAM permits). The mid‑size point originally cited as “GPT‑Neo 350M” is replaced with the available sizes. Architecture differences are documented as a limitation and can be added as an optional covariate in the regression.
5. **LLaMA‑7B graceful skip**: attempts to load LLaMA‑7B without artificial memory caps; if a natural OOM occurs the event is logged as a graceful‑skip with a clear message, satisfying FR‑001 while preserving reproducibility.
6. **Energy measurement on Pi 4**: primary authoritative source is an **INA219 I²C power monitor** (accessed via the `ina219` Python library). A secondary fallback reads `/sys/class/powercap` if available. On CI (x86) the fallback is `pyRAPL`; if neither works, the system logs “Energy measurement unavailable”. Calibration of INA219 is performed with a known resistive load and stored in `data/calibration/ina219_factor.json`.
7. **Reproducibility**: All CI runs produce deterministic artefacts (except energy). The Pi 4 run‑book (`--platform pi4`) generates raw run JSONs, calibration files, and logs that are **committed to the repository**, satisfying Principle I: any fresh GitHub Actions runner can replay the exact Pi 4 measurements by checking out these artefacts.
8. **Interleaved run ordering**: runs are scheduled in a **round‑robin fashion across configurations** to decorrelate thermal and frequency effects; an Ljung‑Box autocorrelation diagnostic (`statsmodels.stats.diagnostic.acorr_ljungbox`) is performed post‑hoc and warnings emitted if significant.
9. **Statistical caveats**: scaling exponents are reported **descriptively with 95 % confidence intervals**; no formal hypothesis test on the exponent is performed due to limited degrees of freedom. Architecture is added as an optional covariate.
10. **Dequantization overhead**: computed as `(E_quant‑E_fp16)/E_fp16` per model and flagged when ≥10 % **and** statistically higher than the FP16 baseline (paired t‑test, α = 0.05). The spec wording “scaled by parameter count” is redundant and noted as such.
11. **Variance stability**: flagged when `std_energy / mean_energy > 0.15` (SC‑004).  
12. **Sensitivity analysis**: additional prompt lengths (short, medium, long tokens) are run to assess workload effects (Principle VII).

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies** (pinned in `code/requirements.txt`):
  - `torch==2.3.1` (CPU wheel)
  - `torchao==0.3.1` (INT8/INT4 weight‑only, CPU path)
  - `transformers==4.41.2`, `datasets==2.20.0`
  - `pyRAPL==0.2.0` (CI fallback)
  - `ina219==1.0.0` (Pi 4 power monitor)
  - `psutil==5.9.8`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`
  - `jsonschema`, `pytest`
- **Storage**: `data/` (raw WikiText‑2 parquet + checksum, model caches, results CSV/JSON); `logs/`; `figures/`.
- **Testing**: `pytest` – contract tests for all three schemas plus `tests/test_pyrapl_load.py` (verifies pyRAPL fallback). Quick‑start sanity test included.
- **Target Platform**: GitHub Actions free‑tier runner (CPU‑only) for pipeline; self‑hosted Raspberry Pi 4 for authoritative energy measurement.
- **Constraints**: CPU‑only; ≤6 h CI job; ≤7 GB RAM; no GPU needed.

## Constitution Check

| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | Pi 4 run‑book commits raw run JSONs, calibration files, and logs; any fresh CI runner can replay measurements, satisfying Principle I. |
| II. Verified Accuracy | Only verified HF URLs are cited; no invented dataset/model URLs. |
| III. Data Hygiene | WikiText‑2 parquet checksummed; all transformations write new files with provenance. |
| IV. Single Source of Truth | Every figure/statistic derived programmatically from `data/results/aggregated.csv` and `summary.json`. |
| V. Versioning Discipline | Artifact hashes recorded in project state; `updated_at` bumped on each change. |
| VI. Edge‑Hardware Fidelity | INA219 provides true Pi 4 power readings; CPU frequency logged per run; Pi 4 run is authoritative. |
| VII. Dataset Representativeness | Sensitivity analysis varies prompt length (250/500/1000 tokens) to assess workload effects. |

## Project Structure

```text
specs/001-energy-profiling-of-quantized-llm-infere/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/
│   ├── config.schema.yaml
│   ├── inference_run.schema.yaml
│   └── aggregated.schema.yaml
code/
├── benchmark.py          # CLI: config generation, model load/skip, runs
├── quantize.py           # torchao INT8/INT4 (fallback: quantize_dynamic)
├── energy.py             # INA219, sysfs fallback, pyRAPL CI fallback, unavailable chain
├── aggregate.py          # mean/std aggregation → aggregated.csv
├── analyze.py            # OLS scaling, t‑tests, power, flags → summary.json
├── plots.py              # figures
└── utils/ (paths, stats, logging via llmxive_toolkit)
tests/
├── contract/             # schema validation
└── test_pyrapl_load.py   # pyRAPL availability test (T001 repair)
data/
├── raw/ (wikitext‑2 parquet + sha256)
├── configs/              # one JSON per Configuration, schema‑valid
└── results/ (runs/*.json, aggregated.csv, summary.json)
logs/ (benchmark.log, model_load.log, pi4_*.log)
figures/
```

## Phase‑by‑Phase Task List (8–15 tasks)

| # | Task | Addresses |
|---|------|-----------|
| T1 | Fetch WikiText‑2 (test split) via `datasets.load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split="test")`; write parquet to `data/raw/`, record SHA‑256; sample 250/500/1000‑token prompts. | Data Hygiene, Principle VII, edge case (download/0‑token) |
| T2 | Emit a collection of schema‑valid `data/configs/*.json` (covering multiple sizes and precisions, e.g., 3 sizes × 3 precisions) + LLaMA‑7B attempt configs. Validate against `config.schema.yaml`. | FR‑001, Key Entities |
| T3 | Implement `code/quantize.py`: torchao INT8/INT4; fallback `quantize_dynamic` for INT8; on failure record `quantization_status: failed`. | FR‑001, FR‑007 |
| T4 | Model loading with natural memory‑budget detection; attempt LLaMA‑7B load, log graceful‑skip on OOM. Use GPT‑Neo 125 M, 1.3 B, optional 2.7 B; `gpt2-medium` removed. | FR‑001, SC‑005, SC‑007 |
| T5 | Implement `code/energy.py`: idle baseline; primary INA219 reading; secondary `/sys/class/powercap`; CI fallback to pyRAPL; else log “Energy measurement unavailable”. | FR‑002, edge case (pyRAPL failure) |
| T6 | Implement `code/benchmark.py` run loop: Multiple seeded repetitions per config, **interleaved round‑robin ordering** across configurations, capture energy, latency, token count, perplexity, CPU frequency, timestamp. Per‑run JSON validated against `inference_run.schema.yaml`; `--dry-run` mode. Autocorrelation diagnostic added. | FR‑002, FR‑003, SC‑004, US‑1/US‑2, T001 repair |
| T7 | Add `tests/test_pyrapl_load.py` (pyRAPL import/init check, passes when fallback engages) and contract tests for all three schemas; fix quickstart commands. | T001 repair, Constitution I |
| T8 | Implement `code/aggregate.py`: mean/std of energy‑per‑token, latency, perplexity per config **excluding** runs where `measurement_method` is `"unavailable"`; log omissions; write `aggregated.csv` validated against `aggregated.schema.yaml`. | FR‑004, SC‑001 |
| T9 | Implement `code/analyze.py`: OLS `log(E_tok) ~ log(params) + C(quant) + cpu_freq` (architecture optional covariate); report exponents with 95 % CI (descriptive only); pairwise t‑tests with Bonferroni; dequantization‑overhead flag (≥10 % & p<0.05); variance‑stability flag (std/mean ≤ 0.15); **achieved power** via `TTestIndPower`; if <3 size points, report deterministic slope only. | FR‑005, FR‑007, SC‑001–SC‑004, SC‑006 (honest reporting) |
| T10 | Implement `code/plots.py`: bar plot energy‑per‑token vs quantization; log‑log energy vs parameter scatter with fitted lines; CPU‑frequency trace; PNGs to `figures/`. | FR‑006 |
| T11 | Emit `data/results/summary.json` (exponents, corrected p‑values, flags, achieved power, measurement‑authority labels); checksum all artefacts. | Principle IV, V |
| T12 | Raspberry Pi 4 run‑book (`--platform pi4`): authoritative energy measurement, throttling/frequency logging; compare Pi 4 vs CI in `summary.json`. | FR‑002, Principle VI |
| T13 | Sensitivity analysis: rerun primary configs at 250/500/1000‑token prompts; report energy‑per‑token variation. | Principle VII |

**Coverage**: FR‑001 (T2‑T4), FR‑002 (T5, T6, T12), FR‑003 (T6), FR‑004 (T8), FR‑005 (T9), FR‑006 (T10), FR‑007 (T9); SC‑001 (T8/T9), SC‑002 (T9), SC‑003 (T9), SC‑004 (T6/T9), SC‑005 & SC‑007 (T4), SC‑006 (T9, honest power report).

## Compute Feasibility Decision

- **CPU‑first**: all components run on the 2‑core/7 GB GitHub Actions runner. GPT‑Neo‑1.3 B FP16 ≈ 2.6 GB; INT4 ≈ 0.7 GB – fits RAM. Estimated wall‑time ≈ 4–5 h.
- **GPU escape hatch**: not required; all methods have faithful CPU forms.
- **Data**: WikiText‑2 (HF), GPT‑Neo checkpoints (HF) are openly downloadable; no gated data.

## Risk Mitigation & Edge Cases

| Situation | Detection | Response |
|-----------|-----------|----------|
| INA219 unavailable | ImportError / I²C read failure | Fall back to sysfs powercap; if also unavailable, log “Energy measurement unavailable”. |
| torchao INT4 fails on an operator | Exception during quantized forward | Record `quantization_status: failed`; exclude config from energy comparisons, log. |
| Model OOM | MemoryError / pre‑check estimate > budget | Log `load_success: false` to `logs/model_load.log`, continue. |
| WikiText download failure / 0 tokens | HTTP error; `len(tokens)==0` | Abort with clear error; log warning; skip run. |
| LLaMA‑7B loads within budget (unlikely) | Pre‑check passes | Natural OOM will be triggered if memory exceeds; graceful‑skip logged per FR‑001. |
| Frequency drift | `/proc/cpuinfo` deviation after stabilization wait | Log warning; include frequency as covariate. |
| Autocorrelation in runs | Autocorrelation statistic > 0.2 | Emit warning; consider re‑ordering or discarding affected runs. |
