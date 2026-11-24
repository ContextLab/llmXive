# Implementation Plan: Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation

**Branch**: `001-prompt-engineering-code-translation` | **Date**: 2024-05-21 | **Spec**: `specs/001-prompt-engineering-code-translation/spec.md`
**Input**: Feature specification from `/specs/001-prompt-engineering-code-translation/spec.md`

## Summary

This project evaluates four prompt engineering strategies (Zero-shot Basic, Zero-shot+Style, Few-shot, Few-shot+Style) for translating Python code to JavaScript using the CodeLlama model via the HuggingFace Inference API. The implementation involves downloading and preprocessing a corpus of ≥100 code snippets, executing translations, validating functional correctness via empirical I/O pair extraction (executing the original Python code with fixed synthetic inputs to establish ground truth, then testing the LLM-generated JavaScript against the same inputs), measuring code quality (cyclomatic complexity, lines of code), and performing statistical analysis (GLMM, Repeated Measures ANOVA) to determine significant differences between conditions. The entire pipeline is designed to run within the constraints of a GitHub Actions free-tier runner (limited CPU, constrained RAM, time limits) using CPU-tractable methods and API-based inference.

## Technical Context

**Language/Version**: Python 3.x (recent version)  
**Primary Dependencies**: `datasets`, `pandas`, `requests`, `scikit-learn`, `statsmodels`, `node`, `npm`  
**Storage**: Local CSV/JSON files in `data/`, version-controlled prompts in `data/prompts/`  
**Testing**: `pytest` for unit tests; integration tests via execution scripts; statistical validation via `statsmodels`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research pipeline / Data processing / Statistical analysis  
**Performance Goals**: Total runtime ≤ 6 hours; Memory footprint ≤ 7 GB; API timeout handling (with a reasonable timeout threshold per request)  
**Constraints**: No GPU; No local LLM training; API rate limit handling (exponential backoff); Data chunking for RAM limits  
**Scale/Scope**: 100 code snippets × 4 conditions = 400 API requests; wall-clock time estimated at several hours with 2-worker parallelization

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | ✅ PASS | All seeds pinned in `code/`; datasets fetched from canonical HF URLs; `requirements.txt` pins versions; `package-lock.json` pins Node.js deps; scripts runnable end-to-end. |
| **II. Verified Accuracy** | ✅ PASS | Only URLs from `# Verified datasets` block cited; Reference-Validator agent will check titles; no hallucinated sources. |
| **III. Data Hygiene** | ✅ PASS | **Checksum Generation Step**: A dedicated script `code/utils/checksum_artifacts.py` will generate SHA-256 hashes for all raw data files in `data/raw/` and write them to `state/` before any transformation. No data is modified in place; transformations write new files. PII scan enforced. |
| **IV. Single Source of Truth** | ✅ PASS | All statistics trace to `data/evaluation/` CSV; no hand-typed numbers in paper; derived files documented. |
| **V. Versioning Discipline** | ✅ PASS | **State Update Mechanism**: The `code/utils/update_state.py` script will compute content hashes of all artifacts in `data/` and `code/`. If hashes change, it updates the `updated_at` timestamp in `state/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e.yaml` and invalidates stale review records. |
| **VI. Prompt Specification Integrity** | ✅ PASS | Prompts stored in `data/prompts/` as version-controlled text; exact text logged with model ID and seed; changelog required for modifications. |
| **VII. Evaluation Transparency** | ✅ PASS | Correctness via empirical I/O pair extraction (Python execution with fixed synthetic inputs + JS validation); stats (GLMM, RM-ANOVA) with fixed lib version; p-values, CIs, and observed power included with raw data. |

## Project Structure

### Documentation (this feature)

```text
specs/001-prompt-engineering-code-translation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── ingestion/
│   ├── download_datasets.py
│   └── preprocess_corpus.py
├── execution/
│   ├── run_inference.py
│   └── api_client.py
├── evaluation/
│   ├── extract_io_pairs.py          # Extract I/O pairs from Python code
│   ├── run_js_validation.py         # Test JS against extracted I/O pairs
│   ├── compute_quality.py
│   └── statistical_analysis.py
├── utils/
│   ├── logging.py
│   ├── timeout_utils.py
│   ├── checksum_artifacts.py        # For Principle III
│   └── update_state.py              # For Principle V
└── main.py

tests/
├── contract/
├── integration/
└── unit/

data/
├── raw/
├── processed/
├── prompts/             # All prompt templates stored here
│   ├── zero_shot_basic.txt
│   ├── zero_shot_style.txt
│   ├── few_shot_basic.txt
│   └── few_shot_style.txt
└── evaluation/

requirements.txt
package.json             # For Node.js dependencies
package-lock.json       # For Node.js version pinning
```

**Structure Decision**: Single-project structure with modular directories for ingestion, execution, and evaluation to ensure separation of concerns and reproducibility. Prompts are strictly located in `data/prompts/` to satisfy Constitution Principle VI.

## Implementation Phases

### Phase 0: Ingestion & Preprocessing (FR-001)
**Input**: HuggingFace datasets (CodeTrans, BigCode)  
**Output**: `data/processed/corpus.csv` (CodeSnippet entities, conforming to `dataset.schema.yaml`)  
**Acceptance**: ≥100 valid Python/JavaScript pairs; memory footprint ≤ 7 GB; dataset checksummed and recorded in `state/`

**Tasks**:
1. Download CodeTrans test set and supplemental sources via HF `datasets` library with streaming to avoid RAM overflow.
2. Filter for valid Python-to-JavaScript pairs (both fields non-empty, code syntactically valid).
3. Sample to N≥100 (or expand post-hoc if time permits).
4. Write to `data/processed/corpus.csv` with columns: `id`, `python_source`, `source_dataset_id`, `dataset_url`. Output CSV conforms to `dataset.schema.yaml`.
5. Compute SHA-256 checksum via `checksum_artifacts.py` and record in `state/`.

### Phase 1: Prompt Specification & Setup (FR-006)
**Input**: Prompt templates (user-provided or derived from literature)  
**Output**: `data/prompts/` directory with four `.txt` files  
**Acceptance**: Four distinct prompt templates stored; exact text logged with each API request

**Tasks**:
1. Define four prompt templates:
   - `zero_shot_basic.txt`: Simple instruction to translate Python to JavaScript.
   - `zero_shot_style.txt`: Instruction + explicit style specs (e.g., "use ES6 syntax, avoid var").
   - `few_shot_basic.txt`: Instruction + A small number of example Python/JS pairs (sampled from corpus).
   - `few_shot_style.txt`: Instruction + examples + style specs.
2. Store each as plain text in `data/prompts/`.
3. Version-control with commit message documenting the condition and rationale.

### Phase 2: Model Inference (FR-002)
**Input**: `data/processed/corpus.csv`, `data/prompts/*.txt`  
**Output**: `data/evaluation/raw_outputs/` with subdirectories per condition, each containing generated JavaScript files  
**Acceptance**: 400 translation outputs (100 snippets × 4 conditions); deterministic execution with pinned seed; metadata logged (prompt, model, seed, timestamp)  
**Constraints**: 30-second timeout per request; exponential backoff for rate limits (3 retries); fallback to smaller sample or local quantized model if API unavailable

**Tasks**:
1. Load corpus and prompts.
2. For each snippet and condition:
   - Construct the full prompt (instruction + optional examples + optional style specs).
   - Call HuggingFace Inference API with CodeLlama-7B, seed=42, temperature=0.0 (deterministic).
   - Log: prompt text, model version, seed, timestamp, raw response.
   - Store generated JavaScript to `data/evaluation/raw_outputs/<condition>/<snippet_id>.js`.
   - Handle timeouts (log and skip); handle rate limits (retry with exponential backoff).
   - If API is unavailable after retries, fall back to a smaller sample (N=50) or local quantized model.
3. Produce `data/evaluation/raw_outputs/metadata.csv` with columns: `snippet_id`, `condition_name`, `prompt_text`, `model_version`, `seed`, `timestamp`, `response_status` (success/timeout/rate_limit/failed).

**Fallback Trigger (Automatic)**:
- After Phase 2 completes [deferred] of requests (N=25 snippets × 4 conditions = 100 requests), record wall-clock elapsed time.
- If elapsed time > 1.5 hours, extrapolate to full N=100; if extrapolated time > 5.5 hours (leaving 0.5h buffer), abort Phase 2 and re-run with N=50.
- If API remains unavailable after 3 retries per request, immediately trigger fallback to local Ollama 7B.
- Log the decision and fallback trigger time in metadata.csv for transparency.

**Fallback Model Equivalence Verification**:
- If fallback to Ollama 7B is triggered, generate outputs for a random sample of N=10 snippets under BOTH CodeLlama (HF API, if available) and Ollama 7B.
- Compute correctness (pass rate) and quality metrics (complexity, lines of code) for both models on the same N=10 subset.
- If metrics differ by >10% (absolute difference), flag as non-equivalent and exclude Ollama-generated outputs from the main analysis.
- If equivalent, include Ollama outputs in the main analysis but add a `model_source` column to translation_result.csv (HF_API or Ollama_local) and stratify results by model source in Phase 6 analysis.
- Report: 'Fallback model equivalence [was/was not] verified (N=10 subset). Results are [combined / stratified by model source] accordingly.'

### Phase 3: I/O Pair Extraction & Validation (FR-003)
**Input**: `data/processed/corpus.csv` (original Python code)  
**Output**: `data/evaluation/io_pairs.csv` (ground-truth input-output pairs)  
**Acceptance**: For each snippet, ≥5 valid I/O pairs extracted; test coverage ≥80%

**Tasks**:
1. **Test Case Generation**: For each Python snippet, generate 10 fixed test cases covering:
   - Boundary conditions: empty inputs (empty list, empty string), single elements.
   - Typical cases: integers 1–100, strings of length 1–50, lists of 1–10 elements.
   - Mixed types: combinations of the above.
2. **I/O Pair Extraction**: Execute each snippet with all 10 test inputs:
   - Record input and output for each execution that completes without error.
   - A snippet is included in validation only if ≥5 I/O pairs are successfully extracted.
   - Exclude snippets where Python execution fails (syntax error, runtime error, timeout).
3. **Ground Truth Definition**: The extracted I/O pairs are treated as GROUND TRUTH by definition (the original Python code is assumed correct). **Limitation**: If the original Python code contains a logic error, the extracted I/O pairs will encode that error, and JavaScript code that reproduces the error will be marked as "correct." This limitation applies equally to all conditions and does not affect the validity of comparing prompt conditions.
4. **Optional Human Verification** (if time permits): A subset of N=10 I/O pairs can be independently verified by a human reviewer to check for obvious logic errors in the original Python code. Results of this review are reported separately as a sensitivity analysis.
5. **Exclusion Independence**: Conduct a chi-square contingency test: exclusion (≥5 I/O pairs extracted vs. <5) vs. prompt condition (4 levels).
   - If p ≥ 0.05, exclusion is independent; proceed to Phase 4 validation with full sample.
   - If p < 0.05, exclusion is condition-dependent (a design compromise); Phase 4 validation proceeds but results are framed as exploratory, not causal.
   - Report: 'Exclusion was [independent/dependent] of condition (χ² = [value], p = [value]). Results are [reported in aggregate / treated as exploratory] accordingly.'
6. Store I/O pairs in `data/evaluation/io_pairs.csv` with columns: `snippet_id`, `input_json`, `expected_output_json`, `extraction_status` (success/timeout/failed).

### Phase 4: JavaScript Validation (FR-003)
**Input**: `data/evaluation/raw_outputs/`, `data/evaluation/io_pairs.csv`  
**Output**: `data/evaluation/validation_results.csv` (TranslationResult entities, conforming to `translation_result.schema.yaml`)  
**Acceptance**: Binary pass/fail status for each snippet-condition pair; timeout handling (log and skip)

**Tasks**:
1. For each generated JavaScript file and corresponding I/O pairs:
   - Execute the JavaScript with the same inputs via Node.js.
   - Compare output to expected output (from `io_pairs.csv`).
   - Record pass/fail status (pass if all I/O pairs match; fail otherwise).
   - Handle timeouts (Node.js test runner timeout = 10 seconds per test).
2. Produce `data/evaluation/validation_results.csv` with columns: `snippet_id`, `condition_name`, `test_pass_status` (pass/fail/timeout/skipped), `execution_time`, `model_source` (HF_API or Ollama_local, if fallback used).

### Phase 5: Code Quality Metrics (FR-004)
**Input**: `data/evaluation/raw_outputs/`  
**Output**: `data/evaluation/quality_metrics.csv`  
**Acceptance**: Cyclomatic complexity and lines of code for each translation

**Tasks**:
1. For each generated JavaScript file:
   - Compute cyclomatic complexity using ESLint complexity plugin.
   - Count lines of code.
2. Produce `data/evaluation/quality_metrics.csv` with columns: `snippet_id`, `condition_name`, `complexity_score`, `lines_of_code`.

### Phase 6: Statistical Analysis (FR-005)
**Input**: `data/evaluation/validation_results.csv`, `data/evaluation/quality_metrics.csv`  
**Output**: `data/evaluation/statistical_summary.csv` (StatisticalSummary entities, conforming to `statistical_summary.schema.yaml`)  
**Acceptance**: p-values, confidence intervals, effect sizes, and observed power for each comparison; Bonferroni correction applied

**Tasks**:
1. **Snippet Difficulty Analysis** (Confounder Check):
   - Compute a 'snippet difficulty score' as the proportion of conditions under which a snippet FAILS correctness (0 = all pass, 1 = all fail).
   - Fit a logistic regression with difficulty score as a predictor of pass/fail status.
   - If the difficulty coefficient is significant (p < 0.05), snippet difficulty is a confounder.
   - If significant, report results stratified by difficulty (easy vs. hard snippets); if not significant, report aggregate results.
   - Report: 'Snippet difficulty [was/was not] a significant predictor of pass/fail status (β = [value], p = [value]). Results are [stratified by difficulty / reported in aggregate] accordingly.'

2. **Correctness Analysis**:
   - Fit a Generalized Linear Mixed Model (GLMM) with binomial link function.
   - Predictor: prompt condition (4 levels).
   - Outcome: pass/fail (binary).
   - Random effect: snippet (to account for within-subject correlation).
   - Compute post-hoc comparisons (all pairs vs. Zero-shot Basic) with Bonferroni correction.
   - Extract p-values, confidence intervals, effect sizes (Cohen's h).

3. **Quality Analysis**:
   - Fit Repeated Measures ANOVA for complexity and lines of code.
   - Predictor: prompt condition (4 levels).
   - Outcome: complexity score / lines of code.
   - Random effect: snippet.
   - Compute post-hoc comparisons with Bonferroni correction.

4. **Model Source Stratification** (if fallback used):
   - If Ollama 7B fallback was used and equivalence was verified, stratify results by `model_source` (HF_API vs. Ollama_local) and report both combined and stratified analyses.
   - If equivalence was NOT verified, exclude Ollama-generated outputs from the main analysis and report results for HF_API only.

5. **Power Analysis**:
   - Conduct post-hoc power analysis for each comparison using the observed effect size and sample size.
   - Compute observed power for each comparison.
   - If observed power < 0.80, add a power_limitation row to the summary: 'power_limitation: [comparison], observed_power=[value], effect_size=[value]. Study is [adequately powered / underpowered] for this comparison.'
   - If observed effect sizes are small (Cohen's f < 0.15), frame results as exploratory and explicitly acknowledge the power limitation.

6. Produce `data/evaluation/statistical_summary.csv` with columns: `metric`, `comparison`, `p_value`, `confidence_interval_lower`, `confidence_interval_upper`, `effect_size`, `observed_power`, `correction_method`. Output CSV conforms to `statistical_summary.schema.yaml`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed with no violations. | N/A |

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| API rate limits | Exponential backoff (3 retries); automatic fallback to N=50 or Ollama 7B if wall-clock time exceeds 5.5h at checkpoint |
| Dataset unavailable | Use supplemental CodeTrans sources; if none available, abort with clear error message |
| Infinite loops in generated JS | Node.js test timeout (10 seconds); log as timeout failure |
| Python execution failure | Exclude snippet from correctness analysis; verify exclusion is independent of condition via chi-square contingency test |
| Underpowered results | Conduct post-hoc power analysis; frame as exploratory if observed effect sizes are small (Cohen's f < 0.15) |
| I/O pair extraction failure | If synthetic input generation fails for a snippet, log and skip that snippet; require ≥5 successful I/O pairs for inclusion |
| Circular validation | Eliminated: ground truth is empirical (Python execution with fixed synthetic inputs), not algorithmic (transpiler-generated) |
| Snippet difficulty confounding | Fit logistic regression with difficulty score as predictor; stratify results if significant |
| Fallback model non-equivalence | Verify equivalence on N=10 subset; if non-equivalent, exclude from main analysis; if equivalent, stratify results by model source |
