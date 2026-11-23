# Research: Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation

## Dataset Strategy

The study requires a corpus of Python-to-JavaScript translation pairs. Based on the verified datasets block, the following sources are used:

| Dataset | URL | Purpose | Notes |
|---------|-----|---------|-------|
| CodeTrans (test) | https://huggingface.co/datasets/CM/codexglue_codetrans | Primary source for translation pairs | Contains Python/JS pairs; filtered for ≥100 valid snippets |
| CodeTrans (interduplication) | [URL to the test split of the CodeTrans interduplication dataset] | Supplemental source | Used if primary source insufficient |

**Dataset Selection Rationale**:  
The CodeTrans datasets are the only verified sources containing explicit Python-to-JavaScript translation pairs. The `codexglue_codetrans` test set is selected as the primary source due to its curated nature. For the Few-shot condition, a subset of the primary CodeTrans dataset (verified pairs) will be used as examples. No CPU-tractable dataset source was verified, so all data processing will be done via streaming and chunking to fit within 7GB RAM.

**Variable Fit Check**:  
The study requires `python_source`, `source_dataset_id`, and `dataset_url`. The CodeTrans datasets contain these fields. No additional variables are needed, so there is no mismatch.

**Sample Size Justification**:  
The primary target is N≥100 snippets (instead of the originally specified 200) to fit within the 6-hour CI runtime constraint. With 100 snippets × 4 conditions = 400 API requests at [deferred] per request and 2-worker parallelization, wall-clock time is estimated at [deferred]. If time remains after Phase 4 (JavaScript validation), the sample can be expanded post-hoc. This trade-off ensures feasibility while preserving the core experimental design.

## Experimental Design

### Conditions
1. **Zero-shot Basic**: Simple instruction without style specs.
2. **Zero-shot+Style**: Instruction with explicit style requirements (e.g., "use ES6 syntax").
3. **Few-shot**: Instruction with several example Python/JS pairs (drawn from the primary dataset).
4. **Few-shot+Style**: Instruction with examples and style requirements.

### Execution Plan
- **Model**: CodeLlama-7B accessed via the HuggingFace Inference API.  
- **Timeout**: 30 seconds per request; exponential backoff for rate limits (3 retries).  
- **Output Storage**: Raw responses stored in `data/evaluation/raw_outputs/` with metadata (prompt, seed, timestamp).
- **Fallback Strategy**: If HF API is unavailable or rate limits prevent completion, automatic fallback to N=50 sample or local Ollama 7B (CPU-executable). Fallback trigger: wall-clock time > 5.5h at [deferred] checkpoint or API unavailable after 3 retries per request.

### Validation Strategy (Critical Update)

#### Functional Correctness via Empirical I/O Pair Extraction

The study eliminates circular validation by using **empirical I/O pairs** derived from executing the original Python code with fixed synthetic inputs, rather than transpiler-generated tests.

**Ground Truth Generation**:
1. For each Python snippet in the corpus, generate 10 fixed test cases covering:
   - Boundary conditions: empty inputs (empty list, empty string), single elements.
   - Typical cases: integers 1–100, strings of length 1–50, lists of 1–10 elements.
   - Mixed types: combinations of the above.
2. Execute each snippet with all 10 test inputs; record input and output for each execution that completes without error.
3. A snippet is included in validation only if ≥5 I/O pairs are successfully extracted.
4. Store these pairs in `data/evaluation/io_pairs.csv`.
5. **Ground Truth Definition**: The extracted I/O pairs are treated as GROUND TRUTH by definition (the original Python code is assumed correct). **Limitation**: If the original Python code contains a logic error, the extracted I/O pairs will encode that error, and JavaScript code that reproduces the error will be marked as "correct." This limitation applies equally to all conditions and does not affect the validity of comparing prompt conditions.
6. **Optional Human Verification** (if time permits): A subset of N=10 I/O pairs can be independently verified by a human reviewer to check for obvious logic errors in the original Python code. Results of this review are reported separately as a sensitivity analysis.

**Exclusion Independence Check**:
- Conduct a chi-square contingency test: exclusion (≥5 I/O pairs extracted vs. <5) vs. prompt condition (4 levels).
- If p ≥ 0.05, exclusion is independent; proceed with full sample.
- If p < 0.05, exclusion is condition-dependent (a design compromise); results are framed as exploratory, not causal.
- Report: 'Exclusion was [independent/dependent] of condition (χ² = [value], p = [value]). Results are [reported in aggregate / treated as exploratory] accordingly.'

**JavaScript Validation**:
1. For each generated JavaScript file, execute it with the same synthetic inputs via Node.js.
2. Compare the output to the expected output (from `io_pairs.csv`).
3. Record pass/fail status: pass if all I/O pairs match; fail otherwise.
4. Handle timeouts: Node.js test runner timeout = 10 seconds per test.

#### Code Quality Metrics
- Cyclomatic complexity computed using ESLint complexity rules.
- Lines of code counted directly from the generated JavaScript.

#### Statistical Analysis
- **Snippet Difficulty Analysis**: Compute difficulty score as the proportion of conditions under which a snippet fails. Fit logistic regression with difficulty score as predictor. If significant (p < 0.05), stratify results by difficulty; otherwise report aggregate results.
- **Correctness**: Generalized Linear Mixed Models (GLMM) with a binomial link function to account for binary outcomes and within-subject correlation (snippet-level random effects).
- **Quality**: Repeated Measures ANOVA to account for the same snippets being tested under multiple conditions.
- **Multiple Comparisons**: Bonferroni correction applied for post-hoc tests.
- **Model Source Stratification** (if fallback used): If Ollama 7B fallback was used and equivalence was verified, stratify results by model source (HF_API vs. Ollama_local).
- **Power Analysis**: Post-hoc power analysis conducted for each comparison. If observed power < 0.80, study is framed as exploratory for that comparison. If observed effect sizes are small (Cohen's f < 0.15), the entire study is framed as exploratory and limitations are explicitly acknowledged.

## Statistical Rigor

- **Design Type**: Within-subjects randomized experiment. The same set of snippets is assigned to all four conditions, allowing causal inference regarding prompt effectiveness while controlling for snippet difficulty (via confounder analysis).
- **Snippet Difficulty Confounder**: Snippet difficulty is tested as a potential confounder via logistic regression; results are stratified if difficulty is significant.
- **Exclusion Independence**: Contingency analysis verifies that exclusion (Python execution failure) is independent of condition. If dependent, causal claims are suspended and results are framed as exploratory.
- **Multiple Comparisons**: Bonferroni correction applied for GLMM and RM-ANOVA post-hoc tests (multiple conditions → corresponding comparisons).
- **Power Justification**: Power analysis is deferred to the implementation phase. A post-hoc power analysis will be conducted after data collection. If observed effect sizes are small (Cohen's f < 0.15), the study is treated as exploratory and limitations are explicitly acknowledged.
- **Causal Inference**: The design is a randomized controlled trial (RCT) at the snippet level (conditions applied uniformly). Causal claims about prompt effectiveness are justified, provided the I/O pair extraction is sound, exclusion is independent of condition, and snippet difficulty is not a significant confounder.
- **Measurement Validity**: I/O pair extraction with fixed synthetic inputs ensures the ground truth is independent of the LLM generation. Input-output behavior is the gold standard for functional correctness; ESLint complexity is a standard metric for code quality.
- **Collinearity**: Not applicable; conditions are mutually exclusive.

## Compute Feasibility

- **Runtime**: 100 snippets × 4 conditions = 400 API requests at [deferred] each. With 2-worker parallelization, estimated wall-clock time is [deferred] (within 6 h limit). Automatic fallback to N=50 triggered if wall-clock time > 5.5h at [deferred] checkpoint. Local processing (I/O extraction, quality metrics, statistical analysis) adds [deferred].
- **Memory**: Data processed in chunks; streaming from HF datasets to avoid loading entire corpus into RAM. I/O pair extraction runs Python in-process (no separate subprocess overhead).
- **No GPU**: Inference via API; local processing uses CPU-only libraries (`pandas`, `scikit-learn`, `statsmodels`).
- **Fallback Model Equivalence**: If Ollama 7B fallback is used, equivalence is verified on N=10 subset. If metrics differ by >10%, Ollama outputs are excluded; otherwise, results are stratified by model source.

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| API rate limits | Exponential backoff (3 retries); automatic fallback to N=50 or Ollama 7B if wall-clock time exceeds 5.5h at checkpoint |
| Dataset unavailable | Use supplemental CodeTrans sources; log error and abort if no valid source |
| Infinite loops in generated JS | Node.js test timeout (10 seconds); log as timeout failure |
| Python execution failure | Exclude snippet from correctness analysis; verify exclusion is independent of condition via chi-square contingency test |
| Underpowered results | Conduct post-hoc power analysis; frame as exploratory if observed effect sizes are small (Cohen's f < 0.15) |
| I/O pair extraction failure | If synthetic input generation fails for a snippet, log and skip that snippet; require ≥5 successful I/O pairs for inclusion |
| Circular validation | Eliminated: ground truth is empirical (Python execution with fixed synthetic inputs), not algorithmic (transpiler-generated) |
| Snippet difficulty confounding | Fit logistic regression with difficulty score as predictor; stratify results if significant (p < 0.05) |
| Fallback model non-equivalence | Verify equivalence on N=10 subset (metrics differ by >10%); if non-equivalent, exclude from main analysis; if equivalent, stratify results by model source |
