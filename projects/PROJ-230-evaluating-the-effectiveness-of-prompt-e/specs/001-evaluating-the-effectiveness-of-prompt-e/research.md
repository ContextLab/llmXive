# Research: Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation

## Dataset Strategy

The study requires a corpus of Python-to-JavaScript translation pairs. Based on the verified datasets block, the following sources are used:

| Dataset | URL | Purpose | Notes |
|---------|-----|---------|-------|
| CodeTrans (test) | https://huggingface.co/datasets/CM/codexglue_codetrans/resolve/main/data/test-00000-of-00001-99438bdbf212fe2c.parquet | Primary source for translation pairs | Contains Python/JS pairs; filtered for ≥200 valid snippets |
| CodeTrans (interduplication) | https://huggingface.co/datasets/PELAB-LiU/codetrans_interduplication/resolve/main/data/test-00000-of-00001-33d06fa7ba2a2959.parquet | Supplemental source | Used if primary source insufficient |
| JavaScript (test) | https://huggingface.co/datasets/hchautran/javascript/resolve/main/data/test-00000-of-00038.parquet | REMOVED: Not used | Does not contain parallel pairs; cannot serve as ground truth |
| BigCode (arxiv) | https://huggingface.co/datasets/bigcode/starcoder2data-extras/resolve/main/arxiv/train-00000-of-00044.parquet | REMOVED: Not used for few-shot | Contains raw training corpora, not explicit translation pairs |

**Dataset Selection Rationale**:  
The CodeTrans datasets are the only verified sources containing explicit Python-to-JavaScript translation pairs. The `codexglue_codetrans` test set is selected as the primary source due to its curated nature. The `javascript` and `bigcode` datasets are **not** used for few-shot examples or ground truth because they lack the required parallel structure. For the Few-shot condition, a subset of the primary CodeTrans dataset (verified pairs) will be used as examples. No CPU-tractable dataset source was verified, so all data processing will be done via streaming and chunking to fit within 7GB RAM.

**Variable Fit Check**:  
The study requires `python_source`, `expected_js_reference`, and `source_dataset_id`. The CodeTrans datasets contain these fields. No additional variables (e.g., post-task anxiety) are needed, so there is no mismatch.

## Experimental Design

### Conditions
1. **Zero-shot Basic**: Simple instruction without style specs.
2. **Zero-shot+Style**: Instruction with explicit style requirements (e.g., "use ES6 syntax").
3. **Few-shot**: Instruction with several example Python/JS pairs (drawn from the primary dataset).
4. **Few-shot+Style**: Instruction with examples and style requirements.

### Execution Plan
- **Model**: CodeLlama-7B via HuggingFace Inference API.
- **Timeout**: 120 seconds per request; exponential backoff for rate limits (3 retries).
- **Output Storage**: Raw responses stored in `data/evaluation/raw_outputs/` with metadata (prompt, seed, timestamp).

### Validation Strategy (Critical Update)
- **Functional Correctness**: 
  - **Ground Truth Generation**: Python unit tests are translated to JavaScript using a **deterministic, rule-based transpiler** (e.g., `py2js` or a custom AST walker) to ensure semantic equivalence. 
  - **Verification**: 
 - **[deferred] Manual Review**: A human expert manually reviews a random subset of translated tests to verify semantic equivalence against the original Python logic.
    - **Deterministic Check**: The remaining majority are cross-verified by running the *translated* test against a *known-good* JavaScript implementation. of the logic (derived from the original Python ground truth, not the generated code). This ensures the test logic itself is valid.
  - **Exclusion**: If the deterministic transpiler fails to generate a valid JS test for a snippet, that snippet is **excluded** from the correctness analysis. It is not marked as pass/fail to prevent circular validation.
- **Quality Metrics**: Cyclomatic complexity and lines of code computed using `eslint` complexity rules.
- **Statistical Analysis**: 
  - **Correctness**: Generalized Linear Mixed Models (GLMM) with a binomial link function to account for binary outcomes and within-subjects correlation (snippet-level random effects).
  - **Quality**: Repeated Measures ANOVA to account for the same snippets being tested under multiple conditions.
  - **Multiple Comparisons**: Bonferroni correction applied for post-hoc tests.

## Statistical Rigor

- **Design Type**: Within-subjects randomized experiment. The same set of snippets is assigned to all four conditions.. This design allows for causal inference regarding the effect of prompt engineering, controlling for snippet difficulty.
- **Multiple Comparisons**: Bonferroni correction applied for GLMM and RM-ANOVA post-hoc tests (multiple conditions → corresponding comparisons).
- **Power Justification**: Assuming a moderate correlation (ρ=0.5) between conditions (snippets are similar across translations), N=200 provides >80% power to detect a medium effect size (Cohen's f=0.25) in RM-ANOVA. If the observed correlation is lower (e.g., <0.2), the study is treated as exploratory, and this limitation is explicitly acknowledged.
- **Causal Inference**: The design is a randomized controlled trial (RCT) at the snippet level (conditions applied uniformly). Causal claims about prompt effectiveness are justified, provided the deterministic test translation holds.
- **Measurement Validity**: Deterministic test translation ensures the ground truth is independent of the LLM generation. Unit tests are the gold standard for correctness; `eslint` complexity is a standard metric for code quality.
- **Collinearity**: Not applicable; conditions are mutually exclusive.

## Compute Feasibility

- **Runtime**: A set of API requests (multiple snippets × 4 conditions) at [deferred] timeout each. With 2 cores and parallelization, estimated runtime is ~-5 hours (within 6h limit).
- **Memory**: Data processed in chunks; streaming from HF datasets to avoid loading entire corpus into RAM.
- **No GPU**: Inference via API; local processing uses CPU-only libraries (`pandas`, `scikit-learn`).

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| API rate limits | Exponential backoff; retry logic; fallback to cached responses if available |
| Dataset unavailable | Use supplemental datasets; log error and abort if no valid source |
| Infinite loops in generated code | Node.js test timeout (configurable)

The research question is: How can test reliability be improved in asynchronous environments? The method is: Implementing adaptive timeout strategies based on historical execution data. References: Smith et al. ().; skip and log as failure |
| Test translation failure | **Exclusion**: Snippets where deterministic transpiler fails are excluded from correctness analysis. |
| Underpowered results | Acknowledge limitation; report effect sizes with confidence intervals; treat as exploratory if correlation is low |
| Circular validation | **Mitigation**: Deterministic transpiler + independent verification of test logic; exclusion of untranslatable snippets. |

## Decision Log

- **Dataset**: CodeTrans primary; others supplemental.
- **Model**: CodeLlama-7B via API (no local inference).
- **Validation**: Deterministic test translation; GLMM for correctness; RM-ANOVA for quality.
- **Stats**: GLMM (correctness), RM-ANOVA (quality); Bonferroni correction.
- **Compute**: Chunked processing; parallel API calls; timeout handling.