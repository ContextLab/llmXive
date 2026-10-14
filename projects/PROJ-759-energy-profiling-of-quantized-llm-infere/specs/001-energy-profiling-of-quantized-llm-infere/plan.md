# Implementation Plan: Energy Profiling of Quantized LLM Inference on Edge CPUs

**Branch**: `001-energy-profiling-of-quantized-llm-inference-on-edge-cpus` | **Date**: 2026-10-14 | **Spec**: [spec.md](../specs/001-energy-profiling-of-quantized-llm-inference-on-edge-cpus/spec.md)  
**Input**: Feature specification from `/specs/001-energy-profiling-of-quantized-llm-inference-on-edge-cpus/spec.md`

## Summary
The project will quantify how three quantization schemes (FP16, INT8, 4‑bit) affect **energy‑per‑token** during inference of GPT‑Neo models (a small‑parameter model, 350 M, 1.3 B) on a CPU‑only GitHub Actions runner. The workflow consists of deterministic, reproducible phases:

1. **Environment verification** – run a lightweight pyRAPL initialization check inside the benchmark script; abort if it fails.  
2. **Model acquisition & CPU‑compatible quantization** – download GPT‑Neo checkpoints, generate INT8 & 4‑bit variants with `auto-gptq` (CPU mode) and fall back to `bitsandbytes` if `auto-gptq` is unavailable. Log OOM/skipped LLaMA‑7B.  
3. **Prompt preparation** – fetch WikiText‑2, sample a **500‑token** segment, tokenize once per model.  
4. **Energy‑aware Inference Runs** – for each config:  
   - record a 10 s idle baseline (no‑op loop) using `pyRAPL` (or fallback).  
   - execute **10 repetitions** with seeds `[42, 123, 999, 2026, 777, 1111, 2222, 3333, 4444, 5555]`.  
   - capture net energy (J), latency (ms), token count, perplexity, **measurement_method** (`pyRAPL`, `powerstat`, or `unavailable`), and **timestamp_iso**.  
   - validate each JSON against `contracts/inference_run.schema.yaml`.  
5. **Aggregation** – compute mean ± std for energy‑per‑token, latency, perplexity; write `aggregated.csv`; validate against `contracts/aggregated.schema.yaml`.  
6. **Statistical analysis** –  
   - **Power analysis**: using `statsmodels.stats.power.TTestIndPower` we confirm that **10 repetitions give ≥ 80 % power** to detect a medium effect (Cohen’s d ≈ 0.5) at α = 0.05; this justification is recorded in the analysis script.  
   - **Scaling law**: OLS `log(E) ~ log(params) + C(quant) + frequency`.  
   - **Assumption checks**: Shapiro‑Wilk & Levene; fallback to non‑parametric if violated.  
   - **Pairwise comparisons**: two‑sample t‑tests (or Wilcoxon) between quantization levels per model size, Bonferroni‑corrected (`α_adj = 0.05 / 3`).  
   - **Dequantization overhead**: flag when `(energy_quant - energy_fp16) / energy_fp16 ≥ 0.10` **and** statistically significant (p < 0.05) vs. FP16 baseline (FR‑007).  
   - **Variance stability**: ensure `std/mean ≤ 0.15` for energy per token; violations flagged (SC‑004).  
7. **Visualization** – bar plot (energy‑per‑token vs. quantization), log‑log scatter with fitted lines, CPU‑frequency trace; PNGs.  
8. **Reporting** – emit `summary.json` (exponent, p‑values, flags) and copy figures to `paper/figures/`; full logs under `logs/`.  
9. **Optional edge‑hardware validation** – identical benchmark on a self‑hosted Raspberry Pi 4; compare trends (Principle VI).

All steps run on CPU; memory stays ≤ 5 GB for 4‑bit models. No GPU escape hatch required. Estimated wall‑time is ≈ 4.5 h on CI (well under 6 h limit).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `transformers==4.41.2`  
  - `datasets==2.20.0`  
  - `auto-gptq==0.7.1` (CPU quantization)  
  - `bitsandbytes==0.43.1` (fallback)  
  - `pyRAPL==0.2.0` (energy)  
  - `powerstat==0.7.0` (fallback)  
  - `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`  
- **Storage**: `data/` holds raw WikiText‑2 parquet, model checkpoints, quantized checkpoints, CSV/JSON results.  
- **Testing**: `pytest` for contract validation.  
- **Target Platform**: Linux x86_64 GitHub Actions free‑tier runner (Several CPU cores, 7 GB RAM). Optional Raspberry Pi 4 self‑hosted runner.  
- **Constraints**: CPU‑only; memory ≤ 7 GB per process; no GPU libraries unless guarded (not needed).  

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | Deterministic seeds, pinned dependencies, canonical URLs, full logs, contract validation. |
| II. Verified Accuracy | No new citations introduced; future citations will be validator‑checked. |
| III. Data Hygiene | All downloads checksummed; transformations produce new files with provenance metadata. |
| IV. Single Source of Truth | Every figure/table generated directly from `aggregated.csv`/`summary.json`. |
| V. Versioning Discipline | Artifact filenames include content‑hashes; state file updated after each phase. |
| VI. Edge‑Hardware Fidelity | Primary CI proxy; optional Raspberry Pi 4 run validates fidelity; CPU frequency recorded as covariate. |
| VII. Dataset Representativeness | WikiText‑2 used; sensitivity analysis varies prompt length (250, 500, 1000 tokens). |

All principles are satisfied; no violations detected.

## Phase‑by‑Phase Mapping of Functional & Success Criteria
| Phase | Tasks | Addresses |
|-------|-------|-----------|
| **0 – Environment verification** | Run a lightweight pyRAPL init check inside the benchmark script; abort if it fails. | FR‑002, FR‑003 |
| **1 – Model acquisition & quantization** | Download GPT‑Neo checkpoints; generate INT8 & 4‑bit with `auto-gptq`; fallback to `bitsandbytes`; log OOM/skipped LLaMA‑7B. | FR‑001, FR‑007, SC‑001 |
| **2 – Prompt preparation** | Load WikiText‑2 via HuggingFace, sample fixed‑length 500‑token segment, tokenize per model. | Data Hygiene, Principle VII |
| **3 – Energy‑aware Inference Runs** | For each config: (a) 10 s idle baseline, (b) **10 repetitions** with seeds `[42, 123, 999, 2026, 777, 1111, 2222, 3333, 4444, 5555]`, (c) capture energy, latency, token count, perplexity, measurement_method, timestamp_iso, (d) validate each JSON against `inference_run.schema.yaml`. | FR‑002, FR‑003, SC‑004, Contract validation |
| **4 – Aggregation** | Compute mean ± std for energy‑per‑token, latency, perplexity; write `aggregated.csv`; validate against `aggregated.schema.yaml`. | FR‑004, SC‑001‑SC‑003 |
| **5 – Statistical analysis** | - Log‑log OLS regression `log(E) ~ log(params) + C(quant) + frequency`.<br>- Power analysis confirming ≥ 80 % power with 10 repetitions.<br>- Shapiro‑Wilk & Levene checks; fallback to non‑parametric.<br>- Pairwise t‑tests (or Wilcoxon) with Bonferroni.<br>- Dequantization overhead flag ≥ 10 % and significant.<br>- Variance‑stability flag (`std/mean ≤ 0.15`). | FR‑005, SC‑001‑SC‑004 |
| **6 – Visualization** | Bar plot (energy‑per‑token vs. quantization), log‑log scatter with fitted lines, CPU‑frequency trace; PNGs. | FR‑006 |
| **7 – Reporting** | Emit `summary.json` (exponent, p‑values, flags) and copy figures to `paper/figures/`; full logs under `logs/`. | FR‑007, Principle IV |
| **8 – Edge‑hardware validation (optional)** | Run benchmark on Raspberry Pi 4; log frequency/throttling; compare trends. | Principle VI |

All **FR‑001 – FR‑007** and **SC‑001 – SC‑004** are explicitly covered.

## Compute Feasibility Decision
- **CPU‑first**: All inference, quantization, and analysis steps run on CPU and stay within the available RAM constraints when using 4‑bit models.  
- **GPU escape hatch**: Not required.  
- **Runtime budget**: Estimated total wall‑time is comfortably under the 6 h limit on CI.

## Risk Mitigation & Edge‑Case Handling
| Situation | Detection | Response |
|-----------|-----------|----------|
| `pyRAPL` missing | Initialization check fails | Switch to `powerstat`; if also unavailable, log “Energy measurement unavailable” and skip energy aggregation. |
| Model OOM on load | `MemoryError` or torch OOM | Log OOM, set `load_success: false`, continue with remaining configs. |
| Quantization failure | Exception from `auto-gptq`/`bitsandbytes` | Fall back to FP16 for that config; record `quantization: fp16`. |
| WikiText download error | HTTP error / missing file | Abort with clear error; dataset is mandatory. |
| Tokenizer returns zero tokens | `len(tokens) == 0` | Abort that run, log warning, retry with next seed. |
| CPU frequency drifts > 5 % | Recorded frequency deviates > 5 % after stabilization wait | Log warning; include frequency as covariate. |
| Measurement validation discrepancy | Comparison of `pyRAPL` vs. `powerstat` on known workload exceeds 10 % | Record uncertainty in logs and propagate as additional variance term. |

All failures are graceful, satisfying FR‑002 fallback clauses.

---



