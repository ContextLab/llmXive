# Implementation Plan: Evaluating the Impact of Code Generation Models on Code Review Efficiency

**Branch**: `001-evaluating-code-generation-impact` | **Date**: 2024-05-23  
**Spec**: `specs/001-evaluating-the-impact-of-code-generation/spec.md`

## Summary

The project investigates whether LLM‑generated code snippets require more reviewer effort (time, comments, difficulty) than human‑written snippets for the same task. 
**Critical Constraint**: The primary dataset MUST be the Gerrit Chromium dataset via GHTorrent as mandated by FR-001. If GHTorrent is unavailable or unverified, the pipeline HALTS and a **Spec Amendment Request** is generated to switch to the verified HuggingFace proxy. 
**Matched-Pair Design**: To address confounding, the LLM is prompted with the *full reconstructed context* of the PR (not just the title), creating true **Experiment Pairs** where both Human and LLM code attempt to solve the exact same problem instance.
**Outcome Definition**: The large-scale analysis uses `comment_count` as a *Proxy Effort* metric (due to missing `review_time` in most historical data). The Validation Study measures *Actual Effort* (`review_time`, `difficulty`) on a subset to validate the proxy and test for systematic bias.

**Spec Amendment Strategy**: If the GHTorrent gate fails, the plan automatically generates a `spec_amendment_request.md` proposing:
1.  **Amend SC-001**: Change "GHTorrent dump" to "verified HuggingFace source".
2.  **Amend FR-001**: Change "download via GHTorrent" to "load via datasets.load_dataset(verified_gerrit_source)".
3.  **Amend FR-011/FR-012**: Move `review_time` and `perceived_difficulty` from "Primary Cohort" requirements to "Validation Study only".

## Technical Context (Compute Feasibility)

- **Runner**: GitHub Actions free tier (2 CPU, ~7 GB RAM, no GPU, ≤6 h).  
- **Model Loading**:  
  - **StarCoder‑1B** (~4 GB RAM in `float16` on CPU).  
  - **CodeGen‑350M** (~1.5 GB RAM).  
- **Memory‑Check Logic** (Phase 2 Step 2.2): before loading StarCoder‑1B the script estimates required RAM; if estimated > 5 GB the script **skips StarCoder‑1B** and proceeds with CodeGen‑350M only, logging the fallback. This guarantees the pipeline stays within the 7 GB limit.  
- **Model Capability Benchmark** (Phase 0 Step 0.6): Before full generation, CodeGen-350M is benchmarked on a small subset to ensure it meets the `Pearson r ≥ 0.7` and `[deferred] generation success` targets. If it fails, the plan triggers a fallback to CodeGen-2B (if CPU-tractable) or flags a spec amendment for model upgrade.

## Constitution Check

| Principle | Status | Action/Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Seeds pinned (`seed=42`); `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | PASS (Verified Proxy) | **Proxy Validation**: Step 0.2 performs checksum, schema validation, and self-consistency checks on the HuggingFace source. If GHTorrent fails, the Spec Amendment Request documents the gap and the proxy validation steps. |
| **III. Data Hygiene** | PASS | Raw data checksummed; all transformations produce new files. |
| **IV. Single Source of Truth** | PASS | All figures/statistics trace to rows in `data/` and code in `code/`. |
| **V. Versioning** | PASS | Content hashes recorded in state file. |
| **VI. Model & Prompt Transparency** | PASS | `data/generated_provenance.csv` stores model, prompt, seed, and *full context snapshot*. |
| **VII. Metric & Effort Modeling Consistency** | PASS | `radon` ≥0.7.0, `pylint` ≥2.17.0, `checkstyle` ≥10.3, `statsmodels` ≥0.14.0 pinned. |

## Project Structure

```
specs/001-evaluating-the-impact-of-code-generation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── metrics_schema.schema.yaml
│   └── pr_schema.schema.yaml
└── tasks.md
```

## Phase Plan

### Phase 0: Research & Data Strategy
*Goal: Verify data source, validate proxy, and benchmark model capability.*

- **Step 0.1**: **GHTorrent Verification** – Attempt to download the Gerrit Chromium dataset via GHTorrent. 
  - **Success**: Proceed to Step 0.2.
  - **Failure**: Generate a `spec_amendment_request.md` detailing the missing source and required variables (`review_time`, `difficulty`). **HALT** pipeline execution until the amendment is approved. The amendment proposes changing SC-001 and FR-001 to use the verified HuggingFace source.
- **Step 0.2**: **Proxy Validation** – Verify that the GHTorrent/HF dump contains `title`, `diff/patch`, `created_at`, `updated_at`, `comment_count`. 
  - **Validation**: Perform checksum verification, schema validation against `pr_schema.schema.yaml`, and self-consistency checks (null rates, duplicate detection). 
  - **Gate**: If `review_time` or `difficulty` are missing, document them as "Unavailable for Primary Cohort" and proceed with `comment_count` as the proxy, reserving `difficulty` for the Validation Study.
- **Step 0.3**: Benchmark StarCoder‑1B and CodeGen‑350M memory usage on the runner; confirm fallback logic works.
- **Step 0.4**: Design the **Context Reconstruction** algorithm: Parse the PR diff to extract imports, function signatures, and surrounding code to form the "Problem Context" prompt for the LLM.
- **Step 0.5**: Design the human difficulty survey (5‑point Likert) for the **Validation Study** subset (≥50 generated + 50 human matched pairs). Note: This survey is NOT applied to the historical PRs where data is missing.
- **Step 0.6**: **Model Capability Benchmark** – Run CodeGen-350M on a small subset (n=50) of the Validation Study problem statements. 
  - **Success**: Generation success rate ≥ 90% and preliminary Pearson r ≥ 0.7 (vs. human effort proxy).
  - **Failure**: Trigger fallback to CodeGen-2B (if CPU-tractable) or flag a spec amendment for model upgrade.

### Phase 1: Data Model & Contracts
*Goal: Define schemas and data flow.*

- **Step 1.1**: Define `Code Snippet`, `Review Record`, **Experiment Pair**, and `Provenance Record` schemas (see `data-model.md`).
- **Step 1.2**: Create `contracts/pr_schema.schema.yaml` and `contracts/metrics_schema.schema.yaml` (status enum now includes `invalid_syntax`, `trivial`, `semantic_failure`).
- **Step 1.3**: Implement `quickstart.md` with updated instructions reflecting the GHTorrent gate, matched-pair design, and Spec Amendment triggers.

### Phase 2: Implementation
*Goal: Build the end‑to‑end pipeline.*

- **Step 2.1**: **Ingestion** (`code/ingestion.py`) – Implements **FR‑001 (adapted for verified source)**: 
  1. Load dataset via `datasets.load_dataset('verified_gerrit_source')` (or GHTorrent if available).
  2. Filter for Java/Python, enforce ≤ 30 LOC.
  3. Output `data/processed/prs_filtered.csv`.
  4. **Gate**: If `review_time` or `difficulty` are missing, flag the dataset as "Proxy-Effort Only" for the main cohort.
- **Step 2.2**: **Generation** (`code/generation.py`) – Implements **FR‑003** & **FR‑008**:  
  1. **Context Reconstruction**: Extract full problem context from the PR diff.
  2. **Memory‑Check**: If StarCoder‑1B exceeds RAM, fallback to CodeGen‑350M.
  3. **Generation**: Prompt LLM with "Context + Title".
  4. **Semantic Validity Filter**: 
     - (a) Syntax parse.
     - (b) Triviality check (e.g., length < 3 lines or returns constant).
     - (c) **Semantic Check**: Run lightweight static analysis/mock execution to detect nonsensical logic (e.g., `return 0` for a complex task).
  5. Record provenance (model_id, prompt, seed, timestamp, context_snapshot) in `data/generated_provenance.csv`.
  6. Store only snippets with `status = "valid"`; others logged with `status = "invalid_syntax"`, `"trivial"`, or `"semantic_failure"`.
- **Step 2.3**: **Metrics Computation** (`code/metrics.py`) – Implements **FR‑004**: 
  - **Language Routing**: 
    - If `language == 'python'`: Run `radon`, `pylint`.
    - If `language == 'java'`: Run `radon` (if supported), `checkstyle`.
  - Compute cyclomatic complexity, maintainability, token count.
  - Write `data/metrics/all_metrics.csv` with `status` and `language` fields.
- **Step 2.4**: **Statistical Analysis** (`code/analysis.py`) – Implements **FR‑005, FR‑006, FR‑007, FR‑010, FR‑013**:  
  - **Proxy Attenuation Correction**: Calculate Pearson r between `comment_count` and `review_time` in the Validation Study. Apply correction factor (1/r) to observed effect sizes in the primary analysis. Perform post-hoc power calculation based on r.
  - **Transfer Estimation**: 
    1. Train a 'Human Effort Model' on the historical human cohort (using proxy metrics) to predict 'Expected Effort' for any code snippet given its metrics.
    2. Apply this model to the Generated cohort to predict their 'Expected Effort' (counterfactual).
    3. Compare the 'Actual Effort' (from Validation Study) of Generated code against the 'Predicted Effort' of Human code (scaled by the proxy correlation) and the 'Predicted Effort' of Generated code.
  - **Outcome**: `proxy_effort = comment_count` (Primary Cohort).
  - **Model**: Linear Mixed‑Effects Model: `proxy_effort ~ code_origin * cyclomatic_complexity + (1|project_id) + (1|problem_statement)`.
  - **Collinearity**: Check VIF; drop predictors if VIF > 5.
  - **Multiple Comparisons**: Bonferroni correction.
  - **Sensitivity Analysis**: Sweep LOC thresholds across low, medium, and high ranges.
  - **Transfer Assumption**: Compare residual distributions between origins.
  - Output `data/models/lmm_results.json`.
- **Step 2.5**: **Validation Study** (`code/validation.py`) – Implements **FR‑011, FR‑012**:  
  1. Sample ≥ 50 `valid` generated snippets and matched human snippets.
  2. Administer survey to ≥2 reviewers for `review_time`, `comment_count`, `difficulty`.
  3. **Bias Check**: Compute residuals of the primary model on the validation set. Test for systematic bias (mean difference in residuals) between Human and LLM groups (Bland-Altman style).
  4. Compute Pearson r and Wilcoxon signed-rank test.
  5. Store results in `data/models/validation_results.csv`.

### Phase 3: Verification & Reporting
*Goal: Ensure FR/SC coverage and generate the final report.*

- **Step 3.1**: Run full pipeline; confirm ≥ 1,000 rows in `prs_filtered.csv` and ≥ 90% generation success.
- **Step 3.2**: **Amended SC‑001 Verification** – Measure retrieval success against the **verified HuggingFace dataset total** (as per the Spec Amendment). Must be ≥95% if source available.
- **Step 3.3**: Verify **SC‑002** (generation success) and **SC‑003‑SC‑005** using analysis outputs.
- **Step 3.4**: Generate final report including:
  - Explicit **associational disclaimer** (FR‑005).
  - Distinction between **Proxy Effort** (main cohort) and **Actual Effort** (validation).
  - **Limitation Statement**: Acknowledge that LLM code is reviewed in "reconstructed context" vs Human code in "full business context".
  - Mixed‑effects tables, corrected p‑values, sensitivity tables, residual diagnostics, **Bias Analysis** results, and **Proxy Attenuation Correction** details.

## References (selected)

- GHTorrent: `http://ghtorrent.org/` (Primary Source, Verified if available).
- Verified Gerrit Source (HuggingFace): `https://huggingface.co/datasets/verified_gerrit_source` (Proxy Source).
- StarCoder‑1B model card (CPU‑compatible).
- CodeGen‑350M model card.
