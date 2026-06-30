# Implementation Plan: Reproduce & Validate Long-Context VLM Training with MMLongBench

**Branch**: `575-reproduce-long-context-vlm` | **Date**: 2026-07-01 | **Spec**: `specs/575-reproduce-long-context-vlm/spec.md`
**Input**: Feature specification from `specs/575-reproduce-long-context-vlm/spec.md`

## Summary

This project executes a rigorous scientific reproduction of the "generalization beyond 128K" claims made in the target paper. The primary requirement is to validate long-document VQA scores and performance retention rates at extended context lengths using a CPU-only environment with constrained RAM resources. The technical approach involves low-bit quantization of the `Qwen2.5-VL-7B` model, execution of the `yubo2333/MMLongBench-Doc` dataset evaluation pipeline, and descriptive statistical analysis of scaling trends where formal hypothesis testing is underpowered.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `transformers>=4.42.0`, `torch>=2.3.0`, `bitsandbytes>=0.43.0` (for 4-bit quantization), `matplotlib>=3.9.0`, `seaborn>=0.13.0`, `pandas>=2.2.0`, `scipy>=1.14.0`.
**Storage**: Local file system (`results/`, `data/`) for JSON/CSV artifacts; Hugging Face Hub for dataset/model caching.
**Testing**: `pytest` for unit tests; `assert`-based validation in evaluation scripts for contract enforcement.
**Target Platform**: Linux (CPU-only), constrained to < 8GB RAM.
**Project Type**: Scientific Evaluation Pipeline / Reproduction Script.
**Performance Goals**: Complete evaluation of 10 samples within 60 minutes on CPU; memory usage < 7GB peak.
**Constraints**: No GPU access; strict adherence to 4-bit quantization; explicit failure reporting if OOM occurs.
**Scale/Scope**: Single dataset split (`test` from `yubo2333/MMLongBench-Doc`); sample size `n=10` for scaling analysis.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

### Sample Size Strategy & Variance Handling

**Current Constraint**: The evaluation pipeline targets `n=10` total samples to meet the 60-minute CPU time limit. Distributed across 5 context lengths (32K, 64K, 128K, 256K, 512K), this yields `n=2` per data point.
**Implication**: This sample size is insufficient for statistical hypothesis testing (p-values) and will result in high variance for the "Generalization Retention Rate" (Claim 2) and "Scaling Trend" (Claim 3).
**Mitigation Plan**:
1. **Descriptive Only**: The paper will explicitly frame all scaling and retention results as "descriptive trends" rather than statistically significant findings.
2. **Variance Threshold**: If the standard deviation across the `n=2` points at any context length exceeds 15%, the trend will be classified as "highly variable" or "inconclusive" per Claim 3.
3. **Discussion Framing**: The Discussion section will explicitly state that the small sample size limits the power to detect subtle degradation, and that the primary goal is to detect *catastrophic* failure (OOM or >50% score drop).

### Discussion Plan

The paper's Discussion section will follow this explicit logic tree based on execution results:
1. **Discrepancy Analysis**: If the measured deviation (Claim 1) > 1.0%, the Discussion will include a dedicated subsection analyzing potential causes:
 * **Quantization Noise**: Impact of 4-bit quantization on precision.
 * **Dataset Drift**: Potential differences between the original paper's dataset version and the current `yubo2333/MMLongBench-Doc` version.
 * **Hardware Variance**: Differences in CPU instruction sets or memory bandwidth.
2. **Limitations**: A mandatory subsection will explicitly state:
 * The sample size (n=10) is too small for multiple-comparison corrections.
 * No p-values are reported; only effect sizes (slope, retention rate) and descriptive statistics (R²) are presented.
 * The "generalization" claim is interpreted as "retention of >80% performance" rather than "perfect parity."

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Writing Quality**: Plan uses active voice, concrete numbers, and avoids jargon without definition.
- [x] **Figure Quality**: All figures will be generated from `results/` JSON artifacts by the Figure-Generation-Agent; no static images.
- [x] **Citation Verification**: Bibliography will strictly use URLs validated in the research stage; no new citations introduced.
- [x] **Statistical Interpretation**: Scaling analysis will explicitly report slope, R², and "inconclusive" status if R² < 0.1, acknowledging lack of multiple-comparison correction.
- [x] **Reproducibility**: Plan mandates logging of commit hashes, data seeds, and environment versions in `results/evaluation_run.json`.
- [x] **Jargon Discipline**: Terms like "4-bit quantization" and "context length" are defined or used consistently.
- [x] **Computational Efficiency**: Hardware constraints (CPU, 7GB RAM) are explicitly stated as a core design parameter.
- [x] **Scaling Law Rigor**: Regression models will be fitted; trend classification (sublinear/superlinear/inconclusive) will be derived from data, not assumed.
- [x] **Principle I (SSoT)**: Single Source of Truth enforced; all figure data and stats derived from `results/` JSONs to prevent drift between plan and artifacts.
- [x] **Principle II (No Silent Fallbacks)**: Every failure path (OOM, Data Unavailable) is mapped to a specific Claim 5 outcome in the plan.
- [x] **Principle V (Real-Call Testing)**: Plan includes a mandatory step for real PDF compilation and artifact validation before stage advancement.
- [x] **Principle VI (Convergent Review)**: Plan acknowledges the implement↔review loop with the 12-panel as the gate for stage advancement.

## Project Structure

### Documentation (this feature)

```text
specs/575-reproduce-long-context-vlm/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── figure-data.schema.yaml
│ └── bibliography.schema.yaml
└── tasks.md # Phase 2 output (generated by /speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── eval/
│ ├── __init__.py
│ ├── run_cpu_eval.py # Main entry point for evaluation
│ ├── validate_results.py # Validation of retention rates
│ ├── scaling_analysis.py # Regression and trend classification
│ └── utils.py # Data loading and quantization helpers
├── models/
│ └── __init__.py # Model loading wrappers
└── lib/
 └── __init__.py # Shared utilities

results/
├── sample_results.json # Raw evaluation metrics
├── validation_report.md # Generalization analysis
├── scaling_report.json # Regression metrics
├── evaluation_run.json # Reproducibility surface metadata
└── final_report.md # Aggregated results for LaTeX insertion

data/
└── manifest.json # Dataset checksums and provenance

paper/source/
├── main.tex # LaTeX source (populated dynamically)
├── references.bib # Bibliography
└── figures/ # Generated PDFs (Figure 1, 2, 3)
```

### Paper Text Generation Strategy

The six required sections of the paper (Abstract, Introduction, Methods, Results, Discussion, References) will be populated as follows:
1. **Abstract**: Dynamically generated by selecting the "Primary Citation Claim" based on the logic in `results/final_report.md` (Claim 5 if failure, else Claim 1).
2. **Methods**: Populated with static text + dynamic insertion of `evaluation_run.json` metadata (commit hash, versions).
3. **Results**: Populated by inserting `results/sample_results.json` tables and the generated PDF figures from `paper/source/figures/`.
4. **Discussion**: Populated by inserting the "Discrepancy Analysis" and "Limitations" text derived from the `Discussion Plan` logic in this document.
5. **References**: Populated from `references.bib` (validated by Reference-Validator).

### Figure Generation Workflow

1. **Agent**: `Figure-Generation-Agent` (script: `src/eval/scaling_analysis.py`, `src/eval/validate_results.py`).
2. **Input**: `results/sample_results.json`.
3. **Process**:
 * `scaling_analysis.py` fits regression -> outputs `results/scaling_report.json` -> generates `paper/source/figures/fig1_scaling.pdf`.
 * `validate_results.py` calculates retention -> outputs `results/validation_report.md` -> generates `paper/source/figures/fig2_retention.pdf`.
 * `report_generator.py` (or inline) compares scores -> generates `paper/source/figures/fig3_delta.pdf`.
4. **Output**: Static PDFs inserted into `main.tex` via `\includegraphics`.

### Claim Defense Map

| Claim | Template / Focus | Defense Location in Paper |
|:--- |:--- |:--- |
| **Claim 1** (Reproduction) | "We evaluated... deviation of X%" | **Abstract** (Primary Claim), **Results** (Table 1), **Discussion** (Discrepancy Analysis if X>1.0%) |
| **Claim 2** (Generalization) | "Retention rate at 256K/512K was Y%" | **Results** (Figure 2), **Discussion** (Interpretation of Y < 80%) |
| **Claim 3** (Scaling) | "Trend: Z (Slope S, R² R)" | **Results** (Figure 1), **Discussion** (Limitations on n=10) |
| **Claim 4** (Feasibility) | "Evaluation on CPU/7GB RAM: Success/Fail" | **Methods** (Hardware constraints), **Abstract** (if Failure) |
| **Claim 5** (Failure) | "We encountered [OOM/Data Unavailable]" | **Abstract** (Primary Claim if triggered), **Results** (Failure Log) |

### Success Criteria Mapping

| Criterion | Measurable Outcome | Artifact Location |
|:--- |:--- |:--- |
| **SC-001** (Reproduction Deviation) | Exact % deviation reported | **Abstract**, `results/sample_results.json` |
| **SC-002** (Retention Rate) | Exact % retention reported | **Results**, `results/validation_report.md` |
| **SC-003** (Scaling Trend) | Trend classification (incl. "inconclusive") | **Results**, `results/scaling_report.json` |
| **SC-004** (Limitations) | Explicit statement of n=10 constraint | **Discussion** (Limitations subsection) |
| **SC-005** (Data Provenance) | Valid checksum in manifest | `data/manifest.json`, **Methods** |
| **SC-006** (Primary Claim) | Single unambiguous sentence | **Abstract** (first paragraph) |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Separate `scaling_analysis.py` module | Required to isolate regression logic and generate `scaling_report.json` independently of the main evaluation loop. | Inline logic in `run_cpu_eval.py` would violate the separation of concerns and make the "Descriptive Trend Analysis" difficult to validate or update. |
| Strict 4-bit Quantization Constraint | Mandatory to fit `Qwen2.5-VL-7B` into 7GB RAM on CPU. | Full precision or 8-bit quantization would exceed memory limits, causing immediate OOM failure (Claim 5). |
| Descriptive Trend Analysis | Required by Constitution Principle VIII due to small sample size (n=10). | Formal hypothesis testing (p-values) is statistically invalid with n=10; claiming significance would violate the "Statistical Interpretation Discipline". |