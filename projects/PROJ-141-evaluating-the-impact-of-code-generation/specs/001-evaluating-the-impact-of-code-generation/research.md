# Research: Evaluating the Impact of Code Generation Models on Developer Productivity

**Branch**: `001-code-gen-productivity` | **Date**: 2024-01-15

## Dataset Strategy

| Dataset | Purpose | Verified URL | Loader Method | Notes |
|---------|---------|--------------|---------------|-------|
| HumanEval | Coding problems for experiment | https://github.com/openai/human-eval | git clone | Official GitHub repo; record commit hash in data/metadata.yaml |
| Codeforces (medium difficulty) | Coding problems for experiment | https://codeforces.com/problemset | API | Public API; filter by medium difficulty; record API snapshot date |
| Participant experiment data | Timestamps, code submissions, consent logs | N/A (collected during experiment) | SQLite + files | Anonymized, encrypted at rest, secure deletion after analysis |

**Construct Validity Note**: HumanEval/Codeforces are algorithmic benchmarks, not real development tasks. FR-014 validation (avg time ≥5 min, medium difficulty) is necessary but insufficient. Mitigation: (1) select only problems with real-world analogs; (2) document construct validity limitation in paper; (3) frame findings as "algorithmic task productivity" not general "developer productivity"; (4) recommend supplementary real-task validation in future work.

**Dataset Variable Fit Check**:
- Required variables: problem statement, test suite, difficulty level, average solution time
- HumanEval: Contains function signature, docstring, test cases (verified via GitHub repo)
- Codeforces: Problem statement, constraints, test cases (via API)
- **Gap**: FR-014 requires validation that problems have average solution time ≥5 minutes and medium difficulty. This validation step MUST be implemented before problem selection.

## Model Strategy

| Model | Language | Purpose | Verified URL | CPU Feasibility |
|-------|----------|---------|--------------|-----------------|
| StarCoder | Python | Code generation (LLM-assisted condition) | https://huggingface.co/bigcode/starcoder | ✅ Verified: CPU-wheel available, ≤1GB |
| JaCoText | Java | Code generation (LLM-assisted condition) | **NO verified source found** (FR-013) | ⚠️ Blocking gap: No public CPU-tractable source |

**CRITICAL GAP**: FR-013 specifies JaCoText for Java, but NO verified public source exists. This is a spec-root cause requiring kickback. **Options**: (1) Change spec to use verified Java model (e.g., CodeGen, StarCoder for both languages); (2) Accept Java condition cannot run on GitHub Actions free-tier; (3) Limit experiment to Python-only condition.

**Decision**: Research CPU-wheel versions for JaCoText; if unavailable, flag as blocking gap and propose alternatives to spec owner. Verify:
1. Model size ≤1 GB (to fit 7 GB RAM + 14 GB disk)
2. CPU-only inference available (no CUDA dependencies)
3. Default precision (not 8-bit/4-bit quantization requiring bitsandbytes/CUDA)

## Statistical Methodology

**Design**: Randomized within-subject experiment (each participant completes both LLM-assisted and baseline conditions, randomly assigned via system randomization—not self-selection).

**Causal Inference**: Randomization within-subject design controls for participant-level confounders. Counterbalancing (Latin square or random order swap) mitigates carryover effects. Causal claims are valid for within-subject randomization. Claims MUST be framed as "LLM-assisted vs. baseline effect on algorithmic task productivity" (not general developer productivity).

**Primary Hypotheses**:
1. H1: LLM-assisted condition reduces task-completion time vs. baseline (paired t-test or Wilcoxon signed-rank)
2. H2: LLM-assisted condition affects code quality metrics (pass rate, complexity, coverage, warnings) vs. baseline

**Multiple-Comparison Correction**: Bonferroni or Holm method applied across all 5 metrics (time, pass rate, complexity, coverage, warnings) for each participant to control family-wise error rate at α ≤ 0.05 (FR-009, SC-003, SC-004).

**Effect Size**: Cohen's d with 95% confidence intervals (±0.01 precision) (FR-010, SC-001, SC-002).

**Normality Check**: Shapiro-Wilk test on paired differences; use Wilcoxon if non-normal (FR-008).

**Power Consideration**: An appropriate number of participants chosen based on typical within-subject coding studies (d≈0.5 detectable at 80% power, α=0.05). Acknowledged limitation: 2 problems/condition (per compute constraint) reduces power. Document power limitation in paper; recommend ≥50 participants for future studies. If true effect size is smaller (e.g., d < 0.4), the study may be underpowered.

**Learning/Fatigue Controls**:
- (1) Counterbalancing via Latin square/random swap (US-1, AS-5)
- (2) Problem difficulty matching between conditions
- (3) Randomize problem order within each condition to mitigate practice effects
- (4) No washout period feasible in 6h job; document fatigue as limitation in paper

**Threshold Justification**: FR-011 sensitivity analysis for 15-30% time reduction threshold based on industry reports of LLM code-generation time savings (GitHub Copilot studies report a notable time reduction.

The research question is: How does the use of AI-assisted coding tools affect developer productivity and code quality?
The method is: A mixed-methods approach involving controlled experiments and qualitative interviews with software developers.
()). Documented as exploratory; sensitivity analysis validates robustness across plausible range.

**Measurement Validity**:
- HumanEval: Widely used benchmark for code generation; test suites are automated and reproducible
- Cyclomatic complexity (radon cc): Standard metric, validated in software engineering literature
- Test coverage (coverage.py): Industry-standard tool
- Static analysis (pylint/checkstyle): Standard tools, warnings are objective counts

**Predictor Collinearity**: Not applicable for primary analysis (within-subject comparison). For any secondary analysis with multiple predictors, acknowledge that time and quality metrics may be correlated by definition (e.g., faster completion may trade off with quality).

## Edge Case Handling

| Edge Case | Mitigation Strategy |
|-----------|---------------------|
| Test suite timeout/crash | Set execution timeout (e.g., 60s per test); log timeout as failed test; exclude from pass rate calculation |
| Participant dropout | Exclude incomplete within-subject data from paired analysis; document dropout rate; power analysis accounts for ≤20% dropout |
| LLM model exceeds 6-hour job limit | Set per-request timeout (e.g., 30s); cache model; use smaller context window; fail gracefully with error logged |
| Code fails to compile/syntax error | Catch exceptions during quality assessment; record as 0 pass rate, N/A complexity/coverage; log error |
| Completion time <30 seconds | Flag as outlier; verify problem difficulty; exclude if problem too trivial (per FR-014 validation) |

## Compute Feasibility Decision

**Constraint**: GitHub Actions free-tier: 2 CPU, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h

**Feasibility Assessment**:
- **LLM Inference**: StarCoder verified CPU-tractable (HuggingFace). JaCoText has NO verified source—blocking gap. If JaCoText unavailable, use StarCoder for both languages or limit to Python-only condition.
- **Quality Assessment**: radon, coverage.py, pylint are all CPU-only and lightweight. Feasible.
- **Statistical Analysis**: scipy/statsmodels are CPU-only. With 30 participants, negligible compute. Feasible.
- **Experiment Interface**: Flask is lightweight. Feasible if participants access remotely (not on GitHub Actions).
- **Total Runtime**: 30 participants × 2 conditions × [deferred]/problem × N problems. For N=2 problems, [deferred] per participant. Full experiment: 30 × 30 min = 900 min = 15 h (exceeds 6 h). **Decision**: Limit to N=2 problems per condition; experiment runs on separate server, analysis pipeline on GitHub Actions.

**Decision/Rationale**: Proceed with CPU-only models (verify sizes); limit problems to 2 per condition; use sampled data for quality assessment if needed; document all constraints in paper. JaCoText gap requires spec kickback.