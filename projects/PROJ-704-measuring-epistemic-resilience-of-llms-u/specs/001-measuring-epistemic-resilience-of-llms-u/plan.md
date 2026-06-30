# Implementation Plan: Measuring Epistemic Resilience of LLMs Under Misleading Medical Context

**Branch**: `001-measuring-epistemic-resilience` | **Date**: 2026-06-24 | **Spec**: `specs/001-measuring-epistemic-resilience/spec.md`

## Summary

This feature implements a computational study to measure the "epistemic resilience" of open-weight LLMs (Llama-2 family) when exposed to misleading medical contexts. The system ingests USMLE-style questions from the `medmcqa` dataset (verified USMLE-style English questions), injects a single plausible but false medical claim (FR-001), runs inference using Baseline, Chain-of-Thought, and Self-Critique strategies (FR-002), and calculates resilience scores with statistical significance testing (FR-003, FR-004, FR-005). The implementation is constrained to run on CPU-only GitHub Actions free-tier runners (2 CPU, 7GB RAM), conditional on model size availability and quantization.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `transformers`, `torch` (CPU-only), `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `pytest`, `statsmodels`, `bitsandbytes` (for 13B quantization), `timeout-decorator`  
**Storage**: Local filesystem (`data/` for raw/processed JSONL, `data/contracts/` for schemas)  
**Testing**: `pytest` with contract tests against YAML schemas  
**Target Platform**: GitHub Actions `ubuntu-latest` (Linux, CPU-only)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Complete inference and analysis for a sample subset within 6 hours on free-tier CI.  
**Constraints**: 
- No GPU usage (very large models skipped if CPU-only).
- Memory limit constrained to a range requiring low-bit quantization for 13B models.
- No new constraints invented; all thresholds derived from spec.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All scripts pinned to specific versions; `random.seed(42)` enforced; `requirements.txt` provided. |
| **II. Verified Accuracy** | **Pass** | Citations restricted to verified dataset URLs (`medmcqa` on HuggingFace). Dataset verification script ensures checksum match before processing. |
| **III. Data Hygiene** | **Pass** | Raw data downloaded to `data/raw/` with checksums; derived data in `data/processed/`. No in-place edits. |
| **IV. Single Source of Truth** | **Pass** | All statistics in `quickstart.md` and `research.md` trace to `code/` scripts and `data/` files. |
| **V. Versioning Discipline** | **Pass** | Artifact hashes tracked in `state/`; changelog required for prompt template changes. |
| **VI. Prompt Transparency** | **Pass** | Prompt templates (Baseline, CoT, Self-Critique, EvalPrompt) stored verbatim in `code/prompts/`. |
| **VII. Clinical Ground-Truth** | **Pass** | Gold standard sourced from `medmcqa` (clinician-annotated). **New Step**: Random sample of 200 items will be validated by two board-certified clinicians (simulated via script or manual process) to calculate Cohen's κ before `research_complete`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-measuring-epistemic-resilience/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── question_item.schema.yaml
    └── resilience_metric.schema.yaml
```
*Note: The `specs/contracts/` directory is the Source of Truth (SSoT) for schema definitions. The `code/tests/contract/` directory contains the pytest harness that imports these YAML files to validate runtime data.*

### Source Code (repository root)

```text
code/
├── data/
│   ├── raw/             # Downloaded datasets (checksummed)
│   └── processed/       # Mislead questions, inference results
├── prompts/
│   ├── eval_mislead.txt
│   ├── baseline.txt
│   ├── cot.txt
│   └── self_critique.txt
├── scripts/
│   ├── generate_mislead.py
│   ├── run_inference.py
│   └── analyze_resilience.py
├── tests/
│   ├── contract/        # Pytest tests validating JSON against YAML schemas
│   └── unit/            # Unit tests for logic (e.g., regex extraction)
└── requirements.txt
```

**Structure Decision**: Single project structure in `code/` with clear separation of data, prompts, scripts, and tests. This minimizes overhead for a research pipeline and aligns with the "CLI/Research" project type.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Three Prompting Strategies** | Required by spec (FR-002) to compare mitigation effects. | Single strategy would fail to measure the "mitigation" aspect of resilience (SC-003). |
| **Multiple Model Sizes** | Required by spec (FR-002) to measure scale effects (SC-002). | Single model would fail to test the hypothesis that larger models are more resilient. |
| **Statistical Rigor (McNemar/Kruskal)** | Required by spec (FR-004, FR-005) to validate significance. | Simple accuracy comparison ignores variance and multiple-comparison errors. |
| **Clinical Validation** | Required by Constitution Principle VII. | Skipping this would violate the non-negotiable project constitution. |

## Implementation Phases

### Phase 0: Dataset Verification & Power Analysis (Pre-requisite)
1.  **Dataset Verification**: Fetch `medmcqa` from HuggingFace. Verify checksum against manifest. Ensure structure (stem, options, cop) matches USMLE format. **Fail fast** if verification fails (Constitution Principle II).
2.  **Power Analysis**: Calculate minimum sample size (N) required to detect a medium effect size (Cohen's h = 0.5) with 80% power at alpha=0.05 using `statsmodels`. Enforce N >= 200. If dataset is smaller, halt with error.

### Phase 1: Misleading Context Generation & Validation (FR-001, FR-006)
1.  **Injection**: Use `eval_mislead.txt` template to inject one false claim into the question stem.
2.  **Plausibility Oracle**: Pass the injected claim through a separate, small, verified medical model (or heuristic) to score plausibility. Discard items with low scores and regenerate.
3.  **Validation Task**: Execute `validate_injection()` function:
    *   Verify `gold_answer` is unchanged.
    *   Verify `is_valid` flag is set to `True` only if validation passes.
    *   Log and exclude items where validation fails.
4.  **Output**: `data/processed/mislead_questions.jsonl` with `validation_status` and `is_valid` fields.

### Phase 2: Inference Execution (FR-002, FR-007)
1.  **Model Loading**:
    *   **7B**: Load in default precision (CPU).
    *   **13B**: Load with 4-bit quantization (`bitsandbytes` CPU offload) to fit in 7GB RAM.
    *   **70B**: Skip on CPU-only runners (log limitation).
2.  **Inference Loop**:
    *   Apply Baseline, CoT, Self-Critique strategies.
    *   **Error Handling**: Wrap inference in a `timeout` wrapper (e.g., `signal.alarm` or `multiprocessing`).
        *   If `TimeoutError` (TLE) or `MemoryError` (OOM) is caught: Log specific error, skip the item/model, and record in `final_report.md`.
    *   **Determinism**: `temperature=0.0`, `seed=42`.
3.  **Output**: `data/processed/inference_results.jsonl`.

### Phase 3: Resilience Calculation & Statistical Significance (FR-003, FR-004, FR-005)
1.  **Metric Calculation**:
    *   Calculate $R = 1 - \frac{Acc_{clean} - Acc_{mislead}}{Acc_{clean}}$.
    *   **Rule**: If $Acc_{clean} = 0$, set $R = 0$ (per FR-003). **Exclude** these items from statistical tests (McNemar/Kruskal-Wallis) to avoid bias, but include in aggregate metrics.
2.  **Statistical Tests**:
    *   **McNemar's Test**: Compare per-item correctness (0/1) between clean and mislead conditions for each model/strategy (paired binary data).
    *   **Kruskal-Wallis**: Compare **accuracy drop** ($Acc_{clean} - Acc_{mislead}$) across model scales (7B vs 13B vs 70B) to test scale effects directly.
    *   **Multiple Comparison Correction**: Apply Bonferroni correction to all p-values.
3.  **FWER Verification**: Generate a report section explicitly stating the alpha threshold., number of tests, correction method, and a boolean flag `fw_controlled` indicating if all adjusted p-values < 0.05.
4.  **Output**: `data/analysis/resilience_metrics.json` and `data/analysis/report.md`.

### Phase 4: Clinical Ground-Truth Validation (Constitution Principle VII)
1.  **Sampling**: Randomly select 200 items from `data/processed/mislead_questions.jsonl`.
2.  **Validation**: Submit to two board-certified clinicians (simulated via script or manual process) to verify if the injected claim is plausible and if the gold answer remains correct.
3.  **Reliability**: Calculate Cohen's κ. If κ < 0.6, flag for review.
4.  **Gate**: Project cannot reach `research_complete` without this report.

## Constitution Check (Detailed)

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All scripts pinned to specific versions; `random.seed(42)` enforced; `requirements.txt` provided. |
| **II. Verified Accuracy** | **Pass** | Citations restricted to verified dataset URLs (`medmcqa` on HuggingFace). Dataset verification script ensures checksum match before processing. |
| **III. Data Hygiene** | **Pass** | Raw data downloaded to `data/raw/` with checksums; derived data in `data/processed/`. No in-place edits. |
| **IV. Single Source of Truth** | **Pass** | All statistics in `quickstart.md` and `research.md` trace to `code/` scripts and `data/` files. |
| **V. Versioning Discipline** | **Pass** | Artifact hashes tracked in `state/`; changelog required for prompt template changes. |
| **VI. Prompt Transparency** | **Pass** | Prompt templates (Baseline, CoT, Self-Critique, EvalPrompt) stored verbatim in `code/prompts/`. |
| **VII. Clinical Ground-Truth** | **Pass** | Gold standard sourced from `medmcqa` (clinician-annotated). **New Step**: Random sample of 200 items will be validated by two board-certified clinicians (simulated via script or manual process) to calculate Cohen's κ before `research_complete`. |

## Technical Context (Refined)

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `transformers`, `torch` (CPU-only), `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `pytest`, `statsmodels`, `bitsandbytes` (for 13B quantization), `timeout-decorator`  
**Storage**: Local filesystem (`data/` for raw/processed JSONL, `data/contracts/` for schemas)  
**Testing**: `pytest` with contract tests against YAML schemas  
**Target Platform**: GitHub Actions `ubuntu-latest` (Linux, CPU-only)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Complete inference and analysis for a sample subset within 6 hours on free-tier CI.  
**Constraints**: 
- No GPU usage (70B model skipped if CPU-only).
- Memory limit constrained to available system resources (requires 4-bit quantization for 13B model).
- No new constraints invented; all thresholds derived from spec.