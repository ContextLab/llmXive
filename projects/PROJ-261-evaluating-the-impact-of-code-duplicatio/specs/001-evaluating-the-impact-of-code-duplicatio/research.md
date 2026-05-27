# Research: Evaluating the Impact of Code Duplication on LLM Code Understanding

**Branch**: `001-evaluate-code-duplication-llm-understanding` | **Date**: 2026-05-12

## Research Question

How does syntactic code duplication density correlate with LLM code understanding metrics (perplexity and bug detection accuracy)?

## Background

Code duplication is a well-documented software engineering concern with implications for maintainability and technical debt. Recent work has explored code complexity benchmarks for LLM evaluation (DynaCode 2025). However, the specific relationship between syntactic clone density and model understanding remains underexplored.

**Verified Citations** (Reference-Validator will verify these):
- DynaCode: A Dynamic Complexity-Aware Code Benchmark for Evaluating Large Language Models in Code Generation (2025). Wenhao Hu, Jinhao Duan, C. Wei, Li Zhang, Yue-feng Zhang, et al.. Annual Meeting of the Association for Computational Linguistics. https://doi.org/10.48550/arXiv.2503.10452
- The Stack: 3 TB of permissively licensed source code (2022). Denis Kocetkov, Raymond Li, Loubna Ben Allal, Jia Li, Chenghao Mou, et al.. Trans. Mach. Learn. Res.. https://doi.org/10.48550/arXiv.2211.15533

## Dataset Strategy

| Dataset | Source | Access Method | Size | Validation |
|---------|--------|---------------|------|------------|
| codeparrot/github-code | HuggingFace Datasets | `datasets.load_dataset("codeparrot/github-code", streaming=True)` | 500MB sample | Checksum recorded in `artifact_hashes` |
| Salesforce/codegen-350M-mono | HuggingFace Model Hub | `transformers.AutoModelForCausalLM.from_pretrained(..., load_in_8bit=True)` | 350M parameters | Model config verified against hub |
| human-eval | HuggingFace Datasets | `datasets.load_dataset("openai_humaneval")` | 164 problems (50-sample subset) | Standard benchmark, no modification |

**Dataset Fetching Notes**:
- codeparrot/github-code uses HuggingFace Datasets streaming mode to avoid full download; subset filtered for Python files
- Model loaded with bitsandbytes 8-bit quantization for memory efficiency (SC-002: under 7GB)
- human-eval subset randomly sampled with pinned seed for reproducibility

## Clone Detection Methodology

**AST-Based Subtree Matching** (FR-002, FR-003):
- Python's built-in `ast` module parses code segments into Abstract Syntax Trees
- Function bodies extracted as discrete code segments
- Clone detection via subtree hash comparison with configurable threshold
- No external dependencies beyond Python standard library

**Clone Density Formula**:
```
clone_density = (number_of_duplicate_subtrees / total_subtrees) * 100
```

**Threshold Configuration**:
- Default: 0.8 (80% subtree similarity)
- Sensitivity analysis: 0.7, 0.8, 0.9 (User Story 3)

## Model Metrics Methodology

**Perplexity Computation** (FR-004, FR-005):
- Model: Salesforce/codegen-350M-mono
- Quantization: 8-bit via bitsandbytes
- Metric: Token-level perplexity from log-probability outputs
- Formula: `perplexity = exp(-1/N * sum(log_prob(token_i)))`

**Bug Detection Evaluation** (FR-006):
- Benchmark: human-eval (50-problem subset)
- Metric: pass@1 accuracy
- Evaluation: Model generates solution; tests determine pass/fail

## Statistical Analysis Plan

**Primary Correlation** (FR-007, Principle VI):
- Method: Spearman's rank correlation
- Relationships tested:
  1. clone_density ↔ perplexity
  2. clone_density ↔ bug_detection_accuracy
- Significance threshold: p < 0.05
- Output: correlation coefficient, p-value, sample size (n)

**Sensitivity Analysis** (User Story 3):
- Vary clone detection thresholds: 0.7, 0.8, 0.9
- Compare correlation coefficients across thresholds
- Verify robustness of findings

## Expected Results

Based on preliminary literature review:
- Higher clone density may correlate with lower perplexity (redundant patterns easier to predict)
- Higher clone density may correlate with lower bug detection accuracy (redundant code may mask bugs)
- Null findings (no significant correlation) are equally valid and will be documented

**Statistical Power**: With n ≥ 1000 segments (SC-003), correlation analysis has adequate power to detect medium-effect relationships at p < 0.05.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| HuggingFace rate limiting | Implement retry logic with exponential backoff; log failures |
| AST parsing failures | Skip unparseable files; log to parse_failures.csv (Assumption) |
| Model OOM | 8-bit quantization; monitor memory; fallback to CPU if needed |
| NaN/infinite perplexity | Validate log-probability outputs; exclude invalid segments |
| Zero clone density segments | Include in analysis; document as baseline case |

## Reproducibility Checklist

- [ ] Random seeds pinned in `code/config.py`
- [ ] Dataset subset hash recorded in `state/...yaml`
- [ ] Model version pinned (codegen-350M-mono)
- [ ] Clone detection threshold documented
- [ ] All hyperparameters in configuration file
- [ ] Pipeline runnable end-to-end without manual intervention
- [ ] All artifacts checksummed in `artifact_hashes`
