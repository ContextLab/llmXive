# Research: Reproduce & Validate SU-01 Olympiad Reasoning

## Dataset Strategy

The project relies on the specific datasets referenced in the paper: `imo.jsonl` and `usamo2026.jsonl`. These files are expected to be present in the `external/SU-01` git submodule. 

**Critical Constraint**: No external datasets will be used as proxies for the specific datasets required by the paper. Substituting `usamo_2025` for `usamo_2026` or using a generic math dataset would invalidate the comparison to the paper's results due to differences in problem distribution and difficulty. If the specific local files are missing, the pipeline will skip inference and log a `MISSING_DATASET` warning. **No external fallbacks are available or permitted.**

| Dataset Name | Source Type | Verified URL / Loader | Usage in Plan |
| :--- | :--- | :--- | :--- |
| **SU-01 (Code)** | Git Submodule | `external/SU-01` (Local) | Primary source for `su01-eval` scripts and local metadata. |
| **IMO Problems (imo25)** | Local (Expected) | `su01-eval/unverifiable_bench/mo/metadata/imo25.jsonl` | Inference target. **If missing:** Skip inference for this dataset. Log `MISSING_DATASET` warning. Do not substitute. |
| **USAMO Problems (usamo2026)** | Local (Expected) | `su01-eval/unverifiable_bench/mo/metadata/usamo2026.jsonl` | Inference target. **If missing:** Skip inference for this dataset. Log `MISSING_DATASET` warning. Do not substitute. |
| **USAMO 2025 (External)** | *Not Used* | N/A | **Removed from plan.** Using this as a proxy for USAMO 2026 introduces construct validity threats. |
| **IMO (External)** | *Not Used* | N/A | **Removed from plan.** No verified external source exists for the specific IMO problems required. |

**Dataset Fit Analysis**:
- The `SU-01` codebase expects `imo25.jsonl` and `usamo2026.jsonl`.
- **Gap**: No verified external URL exists for these specific files.
- **Mitigation**: The plan strictly relies on the local submodule. If these files are missing, the pipeline will log a `MISSING_DATASET` warning and skip the inference step for that dataset. The report will explicitly state that the validation of the paper's claims is **impossible** for the missing datasets. This is a "fail fast" on data availability to preserve scientific integrity.

## Model & Method Strategy

### Model Selection
- **Primary**: The `SU-01` 30B model (if weights are present in `external/SU-01/models/`).
- **Fallback**: If weights are missing, the pipeline **will not** use a dummy generator or a small model (e.g., TinyLlama) to "validate reasoning." 
  - **Reasoning**: A dummy generator produces noise; a 1B model lacks the capacity for Olympiad reasoning. Validating "gold-medal" performance with these is a category error.
  - **Action**: If weights are missing, the inference step is skipped. The pipeline proceeds to validate the **code structure** and **evaluation logic** only. The report will state "Performance Claim Unverifiable."

### Evaluation Method
1.  **Inference**: Run `direct_gen.py` with a subset size of 2-5 problems **only if** the model weights are present and memory constraints are met.
2.  **Verification**: Run `eval_verifiable_answer.py` to parse outputs and compare against ground truth.
3.  **Metrics**: Calculate `pass_rate`, `avg_tokens`, and `timeout_count`.
4.  **Statistical Rigor**:
    -   **Sample Size**: The sample size (2-5 problems) is **too small for statistical significance** regarding "gold-medal" claims. The report will explicitly state that metrics are **qualitative indicators** of pipeline functionality, not quantitative proof of performance.
    -   **Multiple Comparisons**: Not applicable (single pipeline run).
    -   **Causal Claims**: None. The study is a reproduction, not a causal experiment.
    -   **Verdict Logic**:
        -   If model runs and passes: "Pipeline Validated" (but not "Gold-Medal Reproduced" due to n=2).
        -   If model missing: "Pipeline Validated, Performance Claim Unverifiable".
        -   If pipeline fails: "Failed".

## Computational Feasibility & Rationale

- **Memory**: The large-scale model cannot run in 7GB RAM.
    - *Decision*: If 30B weights are detected, the script will abort with a specific error message recommending a CPU-only smaller model or skipping inference. The pipeline will then proceed to validate the *code* structure only.
    - *Fallback*: **No fallback to small model for reasoning validation.** The pipeline skips inference and logs "Performance Claim Unverifiable".
- **Runtime**: The time limit is sufficient for 2-5 problems on a small model (if available) or logic validation.
- **Dependencies**:
    - `torch`: Pinned to `cpu` version only (`torch==2.3.0+cpu` via `--index-url`).
    - `transformers`: Latest stable.
    - `accelerate`: Latest stable.

## Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Missing Model Weights** | High | Medium | Plan includes explicit check; degrades to "Code Validation" mode. Report explicitly states "Performance Claim Unverifiable". |
| **Missing Dataset Files** | Medium | High | Plan checks for local files; if missing, logs warning and skips inference. Report states "Data Missing, Validation Impossible". |
| **Memory Overflow** | High (if 30B) | High | Script detects model size; if >7GB, forces skip of inference. |
| **CUDA Import Errors** | Medium | High | Dependency installation script explicitly pins CPU-only wheels. |

## Constitution Check (Research Phase)

- **Principle I (SSoT)**: The plan documents exact dependency pins and fallback logic without inventing new constraints.
- **Principle II (No Silent Fallbacks)**: Explicitly addresses the 7GB RAM limit and 30B model incompatibility. No silent fallback to dummy models for performance claims.
- **Principle V (Real-Call Testing)**: Distinguishes between "Pipeline Logic Validation" and "Real-Call Testing". The current scope is limited to the former.
- **Data Integrity**: Only uses local files. No external proxies for specific datasets.