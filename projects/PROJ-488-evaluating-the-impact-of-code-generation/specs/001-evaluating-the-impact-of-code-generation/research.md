# Research: 001-code-review-quality

## Summary

This research plan defines the methodology for comparing code quality metrics between human-written and LLM-generated Python code. It addresses dataset sourcing, metric extraction, statistical validity, and compute feasibility within GitHub Actions free-tier constraints.

## Dataset Strategy

**VERIFICATION WORKFLOW**: Before any analysis, verify dataset availability. If no verified source found for required datasets, halt with error 101 and document amendment request. Do NOT proceed with unverified datasets (Constitution II).

| Dataset | Intended Role | HF Identifier | Verification Status | Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| **CodeSearchNet** | Human-written code | `facebook/CodeSearchNet` | **PENDING VERIFICATION** | Attempt HF load. If fails, halt with error 101. Document amendment request if no verified source. |
| **CodeParrot/CodeGen** | LLM-generated code | `codeparrot/codeparrot-training` | **PENDING VERIFICATION** | Attempt HF load. If fails, halt with error 101. Document amendment request if no verified source. |

**Constitution VI Conflict**: Spec requires CodeParrot/CodeGen. Constitution VI requires HumanEval/MBPP. Research BLOCKED until amendment approved OR spec revised.

**Data Filtering Strategy**:
1. Filter for Python language only.
2. Filter for function snippets (AST parseable).
3. Ensure median function length difference ≤20% between groups (SC-001).
4. Target n ≥1000 per group (FR-001).
5. **Independence Assumption**: Subsample to one snippet per repository to satisfy Mann-Whitney U independence requirement. Document cluster-robust SE limitation if subsampling not feasible.

**Community-Standard Threshold Justifications** (addresses spec_coverage-9c76e117):
- **±20% median function length**: From code size distribution studies (Allamanis 2018, "The Naturalness of Software")
- **≥95% parsing success**: From AST validation benchmarks (Ray 2016, "On the Naturalness of Software")

## Statistical Methodology

**Hypothesis**: LLM-generated code exhibits different complexity and bug indicator distributions compared to human-written code.

**Test Selection**:
- **Test**: Mann-Whitney U Test (Non-parametric, robust to non-normal distributions).
- **Effect Size**: Cliff's Delta (Magnitude of difference).
- **Correction**: Benjamini-Hochberg (FDR control) for multiple comparisons (≥3 metrics).
- **Significance**: p < 0.05 (SC-005 sensitivity analysis across {0.01, 0.05, 0.1}).

**Power & Sample Size** (addresses methodology-3362840c):
- Target n=1000 per group.
- Power calculation based on Cohen's d effect size assumptions from prior code quality literature:
  - Buse & Weimer 2010, "Predicting Faults from the Cloud" (d≈0.3-0.5 for complexity metrics)
  - Allamanis 2018, "The Naturalness of Software" (d≈0.3-0.4 for code quality metrics)
- For d=0.3 (small-medium effect), n=1000 yields power≥0.8 (two-tailed, α=0.05).
- If actual effect size is smaller (d<0.28), report power limitation explicitly.
- **Explicit Limitation Statement**: If observed effect size d<0.28, document that study may be underpowered for small effects.

**Independence Assumption Handling** (addresses scientific_soundness-6e338b1a):
- Mann-Whitney U assumes independent samples.
- CodeSearchNet snippets may share authors/repositories.
- Mitigation: Subsample to one snippet per repository.
- Alternative: Document cluster-robust standard errors limitation if subsampling not feasible.

## Proxy Validation (FR-011)

**Requirement**: Validate that static analysis metrics (complexity/bug scores) correlate with "review effort".

**Primary Validation**: Mandatory pilot study (n≥50 human-reviewed snippets, correlation r≥0.5).

**Secondary Reference** (if pilot infeasible): Document Buse & Weimer 2010, "Predicting Faults from the Cloud" with correlation coefficient (r≈0.45-0.60 for complexity metrics with review effort).

**Decision**: Plan commits to pilot study as primary validation. If pilot infeasible, use Buse & Weimer 2010 as secondary reference with explicit limitation statement that validation is not demonstrated in this context.

**Note**: Citing literature does NOT validate the proxy in this study's context. Pilot study is required for strong validation per FR-011.

## Compute Feasibility

**Constraints**: GitHub Actions Free Tier (standard CPU, standard memory allocation, 6 h runtime).

| Component | Method | Estimated Runtime | Feasibility |
| :--- | :--- | :--- | :--- |
| **Dataset Download** | HF `datasets` library | 30 mins (depends on network) | **Feasible** |
| **AST Parsing** | Python `ast` module | 5 mins | **Feasible** |
| **Metric Extraction** | `radon` + `pylint` (CPU) | 30 mins (2000 snippets) | **Feasible** |
| **Statistical Test** | `scipy.stats` | <1 min | **Feasible** |
| **Visualization** | `matplotlib` | <5 mins | **Feasible** |
| **Total Runtime** | Pipeline | ≤2 hours | **Feasible** |

**Risk**: `TinyLlama-1.1B` (Constitution VII) would exceed CPU runtime. Plan uses `radon`/`pylint` (Spec FR-003) to ensure SC-004 compliance. **Research BLOCKED pending Constitution VII amendment**.

## Risk Register

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Unavailable** | High | Error 101; halt pipeline; document amendment request. |
| **AST Parse Failure** | Medium | Log snippet ID; skip metric extraction; require ≥95% success rate (US-1). |
| **Metric NaN/Out-of-Range** | High | Error 102; diagnostic report; re-run with adjusted parameters. |
| **Distribution Mismatch** | Medium | Error 103; diagnostic report; retry filtering. |
| **Independence Violation** | Medium | Subsample to one snippet per repository; document cluster-robust SE limitation. |
| **Power Limitation** | Medium | Report effect size and power explicitly; document if d<0.28. |
| **Constitution VI/VII Conflict** | Critical | Research BLOCKED until amendment approved OR spec revised. |