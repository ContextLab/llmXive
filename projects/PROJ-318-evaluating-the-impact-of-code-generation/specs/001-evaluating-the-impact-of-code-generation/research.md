# Research: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

## Executive Summary

This research evaluates whether LLM-generated docstrings provide better **parameter coverage** than existing human-written docstrings in top Python repositories. The study uses a structural ground truth (AST) to measure completeness, avoiding reliance on semantic similarity as a primary validator. The sample size is fixed at a representative number of methods per repository to ensure statistical power and reproducibility within a practical runtime limit.

## Dataset Strategy

The study relies on the **Top 20 Python PyPI Repositories**. Since the spec requires downloading the "top 20 Python repositories from the PyPI leaderboard," we must verify an open, programmatic source.

**Verified Datasets**:
- **PyPI Leaderboard Repositories**: No single "PyPI Leaderboard" dataset exists as a static, versioned file on Hugging Face or OpenML that lists the *current* top 20 by downloads. The spec requires fetching the *current* top 20.
 - *Strategy*: The `extract.py` script will use the **PyPI JSON API** (`https://pypi.org/pypi/{package}/json`) to fetch metadata. The *list* of top 20 packages will be sourced from the **PyPI Stats API** (`) or a verified static snapshot.
 - *Constraint Check*: To satisfy **Constitution Principle I (Reproducibility)**, the implementation will **fetch the list ONCE**, save it to `data/repo_list.json`, and treat this file as a committed artifact. All subsequent runs must use this exact file. Dynamic fetching at runtime is prohibited.
 - *Data Source*: The actual code will be fetched from **GitHub** (using the GitHub API or `git clone` of the repository URLs found in the PyPI metadata).
 - *Verification*: The implementation will verify that the GitHub repository is accessible before processing.

**Note on "Top 20"**: The "Top 20" list is dynamic. To ensure reproducibility:
1. Query the PyPI API for the "Most Downloaded" list at the start of the project.
2. **Save** the resulting 20 URLs into `data/repo_list.json`.
3. This file is committed to the repository. Future runs read from this file, ensuring the study is reproducible on a specific snapshot in time.

**Data Access Feasibility**:
- **GitHub Repos**: Public, open, directly downloadable via `git clone` or API.
- **PyPI Metadata**: Public API, no auth required.
- **Constraint**: The short duration limit and modest RAM limit are the primary constraints, not data access.

## Model & Methodology

### Model Selection
- **Primary Model**: `Salesforce/codegen-350M-mono`
 - *Rationale*: The spec explicitly mandates this model. It is a compact model, small enough to fit in consumer-grade CPU memory with 4-bit quantization.
 - *Quantization*: 4-bit (`bitsandbytes`).
 - *Device*: CPU (GitHub Actions free tier).
 - *Temperature*: 0.2 (Fixed per Constitution Principle VII).
 - *Fallback*: If `bitsandbytes` 4-bit quantization fails on CPU (OOM or unsupported), the system will automatically fall back to 8-bit quantization or full precision, logging the switch to ensure the pipeline does not crash.

### Metric Definitions
1. **Parameter Coverage Score (Primary)**:
 - **Formula**: `(Count of AST parameters found in docstring) / (Total AST parameters)`.
 - **Ground Truth**: Extracted via Python `ast` module.
 - **Validation**: Uses the `docstring_parser` library to extract parameter names from Google/NumPy style docstrings. **Excludes** 'self' and 'cls' from the AST count. Handles parameter aliases via name normalization.
 - **Handling Complex Types**: If the LLM fails to parse complex types, the parameter is counted as "unmatched" (score = 0 for that param).

2. **Semantic Similarity (Auxiliary)**:
 - **Model**: `sentence-transformers/all-MiniLM-L6-v2`.
 - **Purpose**: Detect style overlap and potential hallucinations.
 - **Constraint**: Explicitly **NOT** used to validate completeness (Constitution Principle VI).

### Statistical Analysis
- **Test**: Wilcoxon signed-rank test.
- **Hypothesis**:
 - $H_0$: There is no difference in Parameter Coverage Scores between Human and LLM docstrings.
 - $H_1$: There is a difference (two-tailed).
- **Significance Level**: $\alpha = 0.05$.
- **Minimum Effect Size (MES)**: A difference of **> 0.05** is required for practical significance. Statistical significance alone is insufficient if the effect size is negligible.
- **Data Structure**: Paired data (Human vs. LLM for the *same* method signature).
- **Interpretation**: The 'Human' score is treated as a **baseline efficiency** metric derived from the fixed structural ground truth (AST). The test checks if the LLM's efficiency significantly exceeds this baseline. The Human score is a lower bound of true completeness, not an independent outcome variable. The test is a paired difference test against a fixed ground truth.
- **Power Consideration**: With a fixed a priori sample size, power will be high. The fixed N ensures deterministic statistical power.

## Compute Feasibility & Resource Plan

### CPU-First Strategy
The entire pipeline is designed for the GitHub Actions free tier (CPU, 7GB RAM).
- **Model Loading**: `Salesforce/codegen-350M-mono` in 4-bit quantization (with fallback).
 - *Est. Memory*: ~600MB - 1GB for weights + overhead. Safe for 7GB.
 - *Speed*: CPU inference for medium-scale models is slow, with token generation rates limited to a few tokens per second.
 - *Mitigation*: The fixed sample size of methods/repo ([deferred] total) is critical.
 - *Time Estimate*: [deferred] methods * [deferred]/method (conservative CPU estimate) = 10,000 seconds ([deferred]). This is well within the established time limit, including a safety buffer.
 - **Feasibility**: The fixed N eliminates the risk of dynamic reduction bias and ensures the job completes within the time limit.

### GPU Escape Hatch
- **Status**: Not required for `codegen-350M` on CPU, but if the CPU run fails due to OOM, the system will attempt to load without 4-bit (not recommended) or fail gracefully.
- **Note**: The spec assumes CPU. The "GPU escape hatch" is for models that *cannot* run on CPU. `codegen-350M` can run on CPU.

## Risk Mitigation

1. **AST Parsing Failures**:
 - *Risk*: Non-standard Python syntax (e.g., type comments, experimental features).
 - *Mitigation*: Wrap `ast.parse` in `try/except`. Log error code `AST_PARSE_FAIL`. Skip file. Continue.
2. **Model Generation Timeout**:
 - *Risk*: Generation takes too long per token.
 - *Mitigation*: Set `max_new_tokens` to a low value (e.g., 64). Monitor elapsed time.
3. **Memory Overflow**:
 - *Risk*: 7GB RAM limit exceeded during batch processing.
 - *Mitigation*: Process one repository at a time. Clear model cache (`torch.cuda.empty_cache` if GPU, but for CPU, just `del model` and `gc.collect()`).
4. **Rate Limiting**:
 - *Risk*: GitHub API or PyPI API limits.
 - *Mitigation*: Implement exponential backoff (1s, 2s, 4s, 8s).

## Conclusion

The proposed methodology is feasible within a fixed computational time constraint with a fixed sample size of [deferred] methods. The primary metric (AST-based coverage) is robust and aligns with the constitution. The auxiliary metric (semantic similarity) provides context but does not drive the conclusion. The statistical analysis includes a minimum effect size threshold to ensure practical relevance.