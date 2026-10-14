# Implementation Plan: Energy Profiling of Quantized LLM Inference on Edge CPUs

**Branch**: `001-energy-profiling-of-quantized-llm-inference-on-edge-cpus` | **Date**: 2026‑10‑14 | **Spec**: [spec.md](../specs/001-energy-profiling-of-quantized-llm-inference-on-edge-cpus/spec.md)  
**Input**: Feature specification from `/specs/001-energy-profiling-of-quantized-llm-inference-on-edge-cpus/spec.md`

## Summary
The project must quantify how quantization (FP16, INT8, 4‑bit) influences **energy‑per‑token** during inference of GPT‑Neo models (125 M, 350 M, 1.3 B) on a CPU‑only GitHub Actions runner and optionally on a Raspberry Pi 4 edge device. The workflow consists of:

1. **Model preparation** – download GPT‑Neo checkpoints, apply CPU‑compatible quantization (auto‑gptq) to produce INT8 and 4‑bit variants; attempt LLaMA‑7B loads and gracefully skip with a log if OOM.
2. **Benchmark harness** – run a **fixed‑length (approximately a few hundred‑token) prompt** (post‑tokenization truncation/padding) **five repetitions** per configuration with distinct seeds.
3. **Energy measurement** – use `pyRAPL` (primary) and fall back to `powerstat` if unavailable; baseline idle power measured for a brief interval before each run.
4. **Aggregation** – compute mean, standard deviation of energy‑per‑token, latency, and perplexity per configuration; validate each `InferenceRun` JSON against `contracts/inference_run.schema.yaml`.
5. **Statistical analysis** –  
   - **Scaling law**: Fit a multiple‑regression OLS model `log(Energy_per_token) ~ log(Parameter_count) + Quantization` (categorical) and also separate regressions per quantization level.  
   - **Normality & variance checks**: Shapiro‑Wilk test for normality and Levene’s test for equal variances; if assumptions fail, use Wilcoxon signed‑rank (pairwise) or Kruskal‑Wallis (multiple) non‑parametric tests.  
   - **Pairwise comparisons**: Two‑sample t‑tests with Bonferroni correction (`α_adj = 0.05 / 3`) when assumptions hold; otherwise use the non‑parametric alternatives.  
   - **Dequantization overhead**: Flag when `(energy_quantized - energy_fp16) / energy_fp16 ≥ 0.05` **and** the increase is statistically significant (p < 0.05).  
 - **Power analysis**: With five repetitions we achieve [deferred] power to detect a medium effect (Cohen’s d ≈ 0.5) for energy differences; this is acknowledged in the discussion.
6. **Visualization** – generate (a) bar plot of energy‑per‑token per quantization, (b) log‑log scatter + fitted lines, (c) CPU frequency/throttling trace; save PNGs.
7. **Reporting** – Emit `summary.json` (exponent, p‑values, overhead flags) and copy figures to `paper/figures/`.  
8. **Edge‑Hardware Validation (optional)** – Run the identical benchmark on a self‑hosted Raspberry Pi 4 runner; compare energy‑per‑token trends to confirm proxy validity (Principle VI).

All steps are deterministic, seed‑pinned, and fully reproducible on the free‑tier CI runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `transformers==4.41.2`  
  - `datasets==2.20.0`  
  - `auto-gptq==0.7.1` (CPU quantization)  
  - `pyRAPL==0.2.0` (energy measurement)  
  - `powerstat==0.7.0` (fallback)  
  - `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`  
- **Storage**: Files under `data/` (raw WikiText‑2 parquet, model checkpoints, intermediate quantized checkpoints, CSV/JSON results).  
- **Testing**: `pytest` for unit‑level contract validation; integration tests for the benchmark script (ensuring non‑zero energy values).  
- **Target Platform**: Linux x86_64 GitHub Actions runner (2 CPU cores, 7 GB RAM). Optional Raspberry Pi 4 self‑hosted runner for edge validation.  
- **Constraints**: CPU‑only; memory ≤ 7 GB per process; no GPU libraries unless guarded by a runtime check (GPU escape hatch not required).  
- **Scale/Scope**: Several model sizes × Several quantization levels. = Several primary configurations.; plus optional LLaMA‑7B attempts.

> All quantitative claims (e.g., “≤ 10 min”) are deferred to the research phase and will be cited from the CI runtime logs.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All scripts are deterministic (seeds fixed), data fetched from canonical URLs, and `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | No external citations are introduced in the plan; all references will be validated before manuscript generation. |
| **III. Data Hygiene** | WikiText‑2 parquet files will be checksummed (`sha256`) and stored under `data/`; every transformation writes a new file with provenance metadata. |
| **IV. Single Source of Truth** | Every figure/table is generated directly from the aggregated CSV/JSON produced in Phase 4; no manual transcriptions. |
| **V. Versioning Discipline** | All artifacts (models, quantized checkpoints, result files) are named with content‑hashes; the project state file will be updated after each phase. |
| **VI. Edge‑Hardware Fidelity** | Primary measurements run on the CI CPU (x86_64) as a proxy; an optional Raspberry Pi 4 run (Phase 8) validates proxy fidelity. CPU frequency is locked to *performance* governor and logged (`/proc/cpuinfo`, `sensors`). |
| **VII. Dataset Representativeness** | WikiText‑2 is used as the primary corpus; a sensitivity analysis varying prompt length (250, 500, 1000 tokens) will assess robustness, satisfying the representativeness requirement. |

All principles are satisfied; no violations detected.

## Project Structure
```text
specs/001-energy-profiling-of-quantized-llm-inference-on-edge-cpus/
├── plan.md               # This document
├── research.md           # Phase‑0 research design
├── data-model.md         # Schemas for data artifacts
├── quickstart.md         # How to run the benchmark
├── contracts/
│   ├── config.schema.yaml
│   └── aggregated.schema.yaml
└── tasks.md               # (generated later)

code/
├── benchmark.py          # CLI entry‑point
├── utils/
│   ├── energy.py         # pyRAPL / powerstat wrapper
│   ├── quantize.py       # auto‑gptq helpers
│   └── stats.py          # aggregation & analysis
data/
├── raw/
│   └── wikitext2.parquet
├── models/
│   └── gptneo-125M/...
│   └── gptneo-350M/...
│   └── gptneo-1.3B/...
└── results/
    ├── runs/
    └── aggregated.csv
```

## Complexity Tracking
No constitution violations required additional complexity. The plan stays within a single‑project layout.

## Phase‑by‑Phase Mapping of Functional & Success Criteria

| Phase | Tasks | Addresses |
|-------|-------|------------|
| **0 – Environment Setup** | Install pinned dependencies; verify `pyRAPL` availability; set CPU governor to `performance`; compute checksums for raw data. | FR‑001‑FR‑007 (pre‑conditions), Reproducibility |
| **1 – Model Acquisition & Quantization** | Download GPT‑Neo checkpoints; generate INT8 & 4‑bit variants with `auto-gptq`; attempt LLaMA‑7B load → log+skip if OOM. | FR‑001, SC‑001 (baseline FP16), FR‑007 (dequantization) |
| **2 – Prompt Preparation** | Load WikiText‑2 parquet; sample a 500‑token contiguous segment; tokenize **once** with the model’s tokenizer, then truncate/pad to exactly 500 tokens for all models. | Data Hygiene, Dataset Representativeness |
| **3 – Energy‑aware Inference Runs** | For each configuration: (a) measure 10 s idle power; (b) run inference **five** times with distinct seeds (`42`, `123`, `999`, `2026`, `777`); (c) capture raw energy (J), latency (ms), token count, perplexity; (d) validate each `InferenceRun` JSON against `contracts/inference_run.schema.yaml`. | FR‑002, FR‑003, SC‑004, Contract validation |
| **4 – Aggregation** | Compute mean ± std for energy‑per‑token, latency, perplexity; write `aggregated.csv`; validate against `contracts/aggregated.schema.yaml`. | FR‑004, SC‑001, SC‑002, SC‑003 |
| **5 – Statistical Analysis** | - **Scaling law**: Multiple‑regression OLS `log(Energy_per_token) ~ log(Parameter_count) + Quantization`; also separate regressions per quantization. <br> - **Assumption checks**: Shapiro‑Wilk, Levene; fallback to Wilcoxon/Kruskal‑Wallis. <br> - **Pairwise tests**: t‑tests with Bonferroni correction when assumptions hold; otherwise non‑parametric. <br> - **Dequantization overhead**: Flag if ≥ 5 % increase **and** statistically significant (p < 0.05). <br> - **Power note**: Five repetitions give [deferred] power for medium effects. | FR‑005, SC‑001, SC‑002, SC‑003 |
| **6 – Visualization** | Produce (a) bar plot of energy‑per‑token per quantization; (b) log‑log scatter + fitted lines; (c) CPU frequency/throttling trace; save PNGs. | FR‑006 |
| **7 – Reporting** | Emit `summary.json` (exponent, p‑values, overhead flags) and copy figures to `paper/figures/`. | FR‑007, Single Source of Truth |
| **8 – Edge‑Hardware Validation (optional)** | Run the same benchmark on a Raspberry Pi 4 self‑hosted runner; compare scaling trends; log any deviations. | Principle VI compliance |

All **FR‑001 – FR‑007** and **SC‑001 – SC‑004** are explicitly covered.

---

