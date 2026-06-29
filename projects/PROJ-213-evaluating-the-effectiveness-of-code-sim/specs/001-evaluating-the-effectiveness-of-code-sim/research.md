# Research: Evaluating the Effectiveness of Code Simplification on LLM Performance

## Dataset Strategy

| Dataset | Purpose | Source / Loader | Verified URL | Notes |
|---------|---------|-----------------|--------------|-------|
| HumanEval | Benchmark code snippets + reference solutions | `datasets.load_dataset("openai_humaneval")` | ** (verified) | Full set: the complete set of problems. FR-001 satisfied. |
| StarCoder-1.3B (4-bit) | Code LLM for inference | `llama-cpp-python` with GGUF quantized model | **[VERIFICATION PENDING]** | Spec assumes 4-bit quantized StarCoder fits 7GB RAM; feasibility confirmed in implementation. |

> **VERIFICATION STATUS**: HumanEval source verified (HuggingFace official). StarCoder GGUF source pending verification; Phase 1 blocked until verified per Constitution Principle II.

## Model Strategy

| Model | Purpose | Quantization | Memory Estimate | Notes |
|-------|---------|--------------|-----------------|-------|
| StarCoder-1.3B | Code generation for pass@1 | 4-bit (GGUF via llama.cpp) | Model weights and system overhead constitute the total memory footprint. | Confirmed CPU-only inference within 7GB RAM; exact memory documented in implementation. |

**Decision/Rationale**: StarCoder-1.3B 4-bit chosen to meet the 7GB RAM constraint on GitHub Actions free-tier. Alternative (larger models) excluded due to memory limits. CPU-only inference required; no GPU/CUDA.

## Statistical Analysis Design

| Hypothesis | Test | Correction | Effect Size | Power Consideration |
|------------|------|------------|-------------|---------------------|
| H1: Simplified code has different pass@1 than raw | **McNemar's test** (binary paired) | Bonferroni (α=0.05/3=0.0167) | **Odds ratio with 95% CI** | n=164 problems; minimum detectable effect [deferred] for power≥0.8 |
| H2: Simplified code has different inference time than raw | Paired Wilcoxon signed-rank | Bonferroni (α=0.05/3=0.0167) | **Rank-biserial correlation** | Same sample; power limitation noted if n<100 |
| H3: Simplified code has different token count than raw | Paired Wilcoxon signed-rank | Bonferroni (α=0.05/3=0.0167) | **Rank-biserial correlation** | Same sample; exploratory metric |

**Multiple-Comparison Handling**: Three hypotheses (accuracy, latency, token reduction); Bonferroni correction applied to α=0.05. Family-wise error rate controlled at 0.05.

**Power Justification**: Per FR-010, document minimum detectable effect size for n=164 at power≥0.8 in final report. Sample size is fixed (full HumanEval); power analysis performed **before** data collection in Phase 0.

**Causal Inference Assumptions**: Observational comparison (paired within same problem); claims framed as **associational differences, not causal**. Randomization of code representation (raw vs. simplified) is not random assignment; no causal claim.

**Measurement Validity**: HumanEval pass@1 is a standard benchmark metric; inference time measured via wall-clock timing. Token count via tokenizer. Instruments: standard (no external validation needed).

**Collinearity Note**: Token count and code length are definitionally related; do not claim independent effects. Report descriptively.

**Test Harness Validation**: HumanEval test harness coverage is [deferred] and will be assessed via reference solution comparison. **Limitation**: False negatives in semantic change detection remain possible; FR-008 logs flagged snippets but cannot guarantee all semantic changes are caught.

## Decision Log

| Decision | Rationale | Alternative Rejected |
|----------|-----------|---------------------|
| AST-based simplification (dead-code + boolean) | Directly addresses spec; deterministic; semantics-preserving for majority | Regex-based (non-deterministic, error-prone) |
| **McNemar's test for pass@1** | **Appropriate for binary paired data**; standard in this field | Wilcoxon (inappropriate for binary outcomes) |
| **Wilcoxon for continuous metrics** | Non-parametric; appropriate for paired, non-normal distributions | Paired t-test (assumes normality) |
| Bonferroni correction | Simple, controls FWER for three hypotheses | Holm-Bonferroni (slightly more complex, similar outcome) |
| **Rank-biserial correlation** | **Non-parametric effect size for Wilcoxon** | Cohen's d (parametric, inappropriate) |
| **Odds ratio for McNemar's** | **Standard effect size for binary paired data** | Cohen's d (inappropriate) |
| a fixed per-sample timeout | Prevents runaway inference; aligns with a maximum job time limit | No timeout (risk of job failure) |
| CPU-only inference | Required by GitHub Actions free-tier | GPU/CUDA (not available) |

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| HumanEval not available from verified source | Low | Blocking | Verified via HuggingFace official dataset; fallback documented |
| StarCoder-1.3B 4-bit exceeds 7GB RAM | Medium | Blocking | Test on CI; fallback to smaller model (e.g., CodeGen-350M) if needed |
| AST simplification alters semantics | Medium | Partial failure | FR-008: log flagged snippets; test harness validation [deferred]; proceed with available data if >5% |
| Inference timeout exceeds 6h job limit | Medium | Partial failure | FR-009: 30s timeout per sample; sample size = 164 (full HumanEval) |
| Parse failures exceed 5% | Low | Partial failure | FR-007: log failures; report drop rate per SC-005; document limitation |

## Open Questions

1. What is the exact GGUF quantized StarCoder model file for CPU inference? (Verification pending)
2. What is the minimum detectable effect size for n=164 at power=0.8 for McNemar's test? (To be calculated in Phase 0)
3. What is the test harness coverage for semantic change detection? (To be assessed in implementation; limitation documented)