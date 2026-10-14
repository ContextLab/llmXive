# Project Plan: Evaluating the Impact of Code Generation Models on Code Security

## Summary

This project evaluates the security implications of using Large Language Models (LLMs) for code generation. We generate and analyze code snippets from three open‑weight models (StarCoder‑Base, CodeGen, GPT‑NeoX) using a curated set of security‑focused prompts.

**Amended Requirements (spec §2.2 FR‑002)**:
- The prompt set is limited to **N = 30 prompts** in total, comprising **10 prompts** selected from the CodeXGLUE security subset and **20 handcrafted** prompts (5 each for Database Access, HTML Rendering, Authentication, Injection).
- This yields **N = 90 generated code snippets** (30 prompts × 3 models).

**Amended Constraints (spec §3.1 SC‑005)**:
- The entire pipeline (generation + analysis) must complete within **6 hours** on a **CPU‑only GitHub Actions runner** with a maximum of **7 GB RAM**.
- Models are loaded with **4‑bit quantization** and batch size = 1 to satisfy the memory limit.

## Objectives

1. Generate code snippets from security‑focused prompts using three LLMs.
2. Analyze generated code for vulnerabilities using static analysis tools (Bandit, Semgrep, CodeQL).
3. Compute vulnerability density (V/100LOC) and severity metrics.
4. Perform statistical comparison of security performance across models.
5. Produce visualizations and summary reports.

## Data Collection
- **CodeXGLUE**: Filtered for security keywords (SQL, XSS, auth, injection). Top 10 candidates selected by relevance score.
- **Handcrafted**: 20 prompts covering database access, HTML rendering, authentication, and injection scenarios.
- **Total**: 30 unique prompts.

## Generation
- Models loaded with 4‑bit quantization for CPU compatibility.
- Generation timeout: 120 s per prompt.
- Output: `data/generated/snippets.csv` (N=90 rows).

## Analysis
- **Static Analysis**: Bandit (Python) [UNRESOLVED-CLAIM: c_e41e5bff — status=not_enough_info], Semgrep (multi‑language) [UNRESOLVED-CLAIM: c_90dbea36 — status=not_enough_info], {{claim:c_7449ff5d}} (Wikidata Q93480303, https://www.wikidata.org/wiki/Q93480303).
- **Severity Mapping**: Raw scanner labels mapped to NIST‑based ordinal ranks.
- **Metrics**: Vulnerability count, V/100LOC, mean severity.

## Statistical Testing
- **Kruskal‑Wallis**: Non‑parametric test for differences in V/100LOC across models.
- **Dunn’s Post‑hoc**: Pairwise comparisons with Bonferroni correction (α = 0.0167).
- **ZINB Regression**: Applied if zero‑vulnerability percentage ≥ 20%.

## Deliverables

1. **Data Artifacts**:
 - `data/prompts/manifest.json`: Combined prompt dataset with checksums.
 - `data/generated/snippets.csv`: Generated code snippets.
 - `data/findings/raw_findings.csv`: Vulnerability findings from scanners.
 - `data/results/raw_metrics.csv`: Raw vulnerability metrics.
 - `data/results/statistical_summary.csv`: Results of statistical tests.
 - `data/results/sensitivity_analysis.csv`: Sensitivity analysis results.
2. **Visualizations**:
 - Box‑plot of V/100LOC per model.
 - Heat‑map of CWE frequency per prompt category.
3. **Reports**:
 - `data/results/run_summary.csv`: Execution summary (completion rate, failure counts, wall‑clock time).
 - `docs/research.md`: Methodology and limitations.

## Constraints & Assumptions

- **Hardware**: CPU‑only execution (GitHub Actions environment).
- **Memory**: 7 GB RAM limit.
- **Time**: 6‑hour execution window.
- **Model Quantization**: 4‑bit quantization required for all models.
- **Timeouts**: 120 s per generation, per‑scan timeout for scanners.
- **FPR Proxy**: False Positive Rate (FPR) data used for descriptive reporting only, not for algorithmic correction of vulnerability counts (FR‑004b).

## Risk Management

- **Resource Exhaustion**: Mitigated by N=30 prompt limit and 4‑bit quantization.
- **Timeouts**: Handled via explicit timeout logic; failures logged to `data/failures.log`.
- **Scanner Errors**: Graceful handling for empty snippets, unsupported languages.
- **Statistical Power**: Acknowledged limitation due to small sample size (N=90).

## Timeline

- **Phase 0**: Spec & Plan Alignment (T000a, T000b)
- **Phase 1**: Setup (T001a‑T002)
- **Phase 2**: Core Data Production (T003‑T010)
- **Phase 3**: Generation & Analysis (T011‑T019)
- **Phase 4**: Metrics & Stats (T020‑T029)
- **Phase 5**: Visualisations & Reporting (T030‑T035)
- **Phase N**: Polish & Cross‑Cutting (T036‑T041)

## FR/SC Coverage Map

| ID | Requirement | Plan Element |
|----|-------------|--------------|
| FR-001 | Download 3 models (4-bit) | Task 0.2 (All models 4-bit) |
| FR-002 | Generate 30 prompts (amended) | **AMENDED**: Plan uses 30 prompts (Task 0.3) due to resource constraints. |
| FR-003 | Run scanners | Task (with Timeout set to a moderate duration.) |
| FR-004 | Compute V/100LOC | Task 1.5 (with FPR correction) |
| FR-005 | Kruskal‑Wallis + Dunn | Task 2.1, 2.2 |
| SC-005 | Completion rate ≥90% | Task 3.2 (RunSummary calculation) |

## Dependencies

- Python 3.11
- transformers, torch, bitsandbytes (CPU versions)
- scikit-learn, scipy, statsmodels, pandas, matplotlib, seaborn
- bandit, semgrep, codeql (external tools)

## Success Criteria

1. All 30 prompts processed successfully (N=90 snippets generated).
2. Static analysis completed for all snippets (with documented failures).
3. Statistical tests executed and results documented.
4. Visualizations and summary reports generated.
5. All artifacts hashed and recorded in `state.yaml`.

## Revision History

- **2024-01-15**: Initial draft.
- **2024-01-16**: Amended scope to N=30 prompts (T000a, T000b). Updated Summary and Constraints sections to reflect resource limitations and CPU‑only execution.

<!-- Reviewer Sign‑off: approved -->