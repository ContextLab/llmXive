# Project Plan: Quantization Robustness of Multi-Effect LoRA Adapters

**Project ID**: PROJ-892
**Version**: 2.1 (Updated for Constitution Amendment)
**Status**: Active

## 1. Executive Summary

This project investigates the robustness of multi-effect LoRA adapters under quantization (FP16 -> INT8/INT4). We aim to measure the degradation in concept adherence and the emergence of concept bleeding (cross-effect interference) using a Bayesian Hierarchical Model (BHM) to handle the small sample size of distinct effects.

## 2. Research Questions

1. How does quantization (INT8, INT4) affect the cosine similarity between generated images and their target text prompts compared to FP16?
2. Does quantization increase "concept bleeding" (similarity to non-target effect prompts), and is this correlated with the effective subspace rank of the LoRA adapter?
3. Is the observed degradation statistically significant given the small sample size (N=10 effects)?

## 3. Methodology

### 3.1 Experimental Design
- **Factors**: Quantization Level (FP16, INT8, INT4)
- **Units**: 10 distinct effect prompts (e.g., "oil painting", "watercolor", "cyberpunk").
- **Replicates**: 5 seeds per prompt/level combination.
- **Total Observations**: 10 effects * 3 levels * 5 seeds = 150 images.

### 3.2 Statistical Analysis (Updated)
**Constitution Amendment 001** is active. We will **NOT** use repeated-measures ANOVA.

- **Model**: Bayesian Hierarchical Model (BHM) implemented in `pymc`.
- **Structure**:
 - `Y_ij` (Similarity Score) ~ `Normal(mu_ij, sigma)`
 - `mu_ij` = `Intercept` + `Quantization_Effect[j]` + `Effect_Random[i]`
 - Priors: Weakly informative `Normal(0, 1)` for fixed effects, `HalfNormal(0.5)` for random effects.
- **Inference**: NUTS sampler (No-U-Turn Sampler).
- **Outcome**: Posterior distribution of the `Quantization_Effect` for INT8 and INT4.
- **Decision Rule**: If the 95% HDI of the quantization effect excludes zero, the effect is significant.

### 3.3 Correlation Analysis
- Correlate the magnitude of concept bleeding (posterior mean of bleeding effect) with the effective subspace rank (from SVD of LoRA weights).
- Use Bayesian correlation to generate a posterior distribution for the correlation coefficient (rho).

## 4. Implementation Phases

- **Phase 1: Setup**: Directory structure, dependencies, environment.
- **Phase 2: Foundational**: Data loading, model download, SVD rank calculation.
- **Phase 3: US1 (Baseline)**: FP16 generation, CLIP/LPIPS metrics.
- **Phase 4: US2 (Quantization)**: INT8/INT4 generation, CESR calculation.
- **Phase 5: US3 (Analysis)**: BHM execution, correlation analysis, reporting.
- **Phase 6: Polish**: Testing, documentation, validation.

## 5. Risk Management

- **Risk**: Small sample size (N=10) leads to underpowered analysis.
 - **Mitigation**: BHM partial pooling improves power over ANOVA. If posterior widths remain > 0.2, the result is flagged as "Underpowered" (FR-014) rather than forcing a false positive.
- **Risk**: OOM on quantization steps.
 - **Mitigation**: `handle_oom` logic in `main.py` skips affected levels gracefully.

## 6. Deliverables

1. `data/results.csv`: Raw metrics for all generated images.
2. `data/subspace_ranks.json`: Effective ranks of LoRA adapters.
3. `data/analysis_results.json`: BHM posterior summaries and correlation stats.
4. `docs/report.md`: Final scientific report with posterior plots.

## 7. Approval Status

- **Constitution Compliance**: Principle VII updated via Amendment 001 to reflect BHM methodology.
- **Plan Status**: PENDING AMENDMENT RATIFICATION.
- **Next Step**: Execute Phase 3 (US1) to generate baseline data.
