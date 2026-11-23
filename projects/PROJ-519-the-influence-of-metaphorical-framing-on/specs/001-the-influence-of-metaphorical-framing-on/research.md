# Research: The Influence of Metaphorical Framing on Attitudes Towards Mental Health Treatment

## Summary

This research plan investigates how metaphorical framing ("Battle", "Journey", "Medical") influences public attitudes toward mental health treatment. The study employs a mixed-method approach: a controlled vignette experiment to establish causal links to stigma (CAMI) and help-seeking intent, and an observational analysis of public discourse to correlate metaphor usage with general sentiment (VADER). The methodology prioritizes CPU-tractable methods, open data access, and rigorous statistical controls (multiple-comparison correction, robust standard errors).

**Critical Scope Note on US-2**: The observational analysis (US-2) is implemented as a **Methodological Feasibility Demonstration** using a synthetic fallback corpus. No verified open discourse corpus is available in the provided source list. The synthetic data is designed to test the *pipeline logic* (regex, VADER, regression) and the system's ability to detect **null correlations** (random data) and **known correlations** (stress test). It does **not** claim to answer the ecological research question about naturalistic discourse.

## Dataset Strategy

### Experimental Data (Simulated)
Since the project runs in a CI environment without human participants, the experimental data (US-1) will be **simulated** based on the statistical power requirements (N=159) and expected effect sizes (Cohen's f = 0.25) outlined in the spec.
- **Source**: `numpy.random.Generator` with pinned seeds.
- **Configuration**: Simulation parameters (means, SDs, sample size) are stored in `config/simulation_config.yaml` to ensure bit-for-bit reproducibility.
- **Variables**: Condition (Battle/Journey/Medical), CAMI Score (continuous), Help-Seeking Intent (Likert).
- **Validation**: The simulation logic will be verified against the acceptance criteria (US-1) to ensure the vignette texts match the assigned conditions and scores are recorded correctly.
- **Null Effect Default**: By default, the simulation is set to produce **null effects** (no difference between conditions) to validate that the pipeline correctly identifies a non-significant result (p > 0.05) and does not artificially guarantee significance.

### Discourse Data (Synthetic Fallback)
For the discourse analysis (US-2), the plan relies on a **synthetic fallback corpus** generated for the purpose of this pipeline.
- **Constraint**: The provided "Verified datasets" block lists specific HuggingFace URLs related to "CAMI" and "MJ-historyera". **None of these are public mental health discourse corpora (e.g., Reddit posts) suitable for metaphor frequency analysis.**
- **Resolution**: The plan explicitly acknowledges that **no verified open discourse corpus** (e.g., Reddit r/mentalhealth) is listed in the "Verified datasets" block. Therefore, the plan will:
 1. **Abandon** the ecological study of naturalistic discourse for this iteration.
 2. Use a **static, synthetic, but realistic fallback corpus** generated for the purpose of this pipeline (labeled as "synthetic-fallback" in metadata) to demonstrate the *methodology* (VADER, regression, VIF checks) without fabricating a real dataset URL.
 3. The synthetic data generator will assign metaphor keywords and sentiment scores **independently** (randomly) for the primary run to ensure no tautological correlation (testing for null effect).
 4. The generator will include a **Stress Test Mode** where a known correlation (e.g., r=0.5) is injected into a subset of the data to verify the regression engine correctly detects a signal.
 5. The text generation logic will use placeholder tokens for keywords that do not affect the VADER calculation, ensuring the correlation is not a tautology of the generation script.

### Verified Datasets (Cited Only)
The following URLs are cited from the "Verified datasets" block. Note that they are **not** the primary source for discourse text, but may be used for CAMI instrument validation if applicable (though the spec assumes the instrument is validated).
- **CAMI Scale Reference**: ` (Note: This appears to be a specific dataset; if it contains CAMI responses, it will be used for the experimental *outcome* distribution validation, not the discourse text).

| Dataset Name | Source/URL | Usage | Status |
|:--- |:--- |:--- |:--- |
| CAMI Scale Data | ` | Potential validation of score distribution | ⚠️ Text content unknown; likely scores only |
| Synthetic Discourse | N/A (Generated) | Methodology validation for US-2 | ✅ Fallback per spec |

## Methodological Approach

### Phase 1: Experimental Vignette Design & Simulation (US-1)
- **Stimuli**: Three vignettes (Battle, Journey, Medical) will be constructed. They will be identical in clinical details (depression symptoms) and length, differing *only* in metaphorical framing.
 - *Battle*: "Fighting a war," "combat," "enemy."
 - *Journey*: "Long journey," "path," "milestones."
 - *Medical*: "Illness," "treatment," "symptoms" (neutral).
- **Simulation**: Participants (N=159) will be randomly assigned to conditions.
- **Outcome**: CAMI scores (simulated from a normal distribution with condition-specific means) and Help-Seeking Intent (Likert 1-5).
- **Statistical Test**: One-way ANOVA (FR-005) to detect differences in means.
- **Correction**: Bonferroni correction for post-hoc pairwise comparisons (FR-008).
- **Null Effect Validation**: The simulation will default to null effects (equal means across conditions) to validate that the pipeline correctly identifies a non-significant result.

### Phase 2: Discourse Analysis Pipeline (US-2) - Methodological Feasibility Demonstration
- **Data Processing**: Text cleaning, removal of PII, and metaphor keyword extraction (regex for "battle," "journey," "burden").
- **Sentiment**: VADER compound score calculation (FR-004). **Crucial Note**: VADER measures polarity, not stigma. This is explicitly stated in the output.
- **Circularity Mitigation**: To address the mechanical correlation between metaphor keywords and VADER scores (since VADER lexicon may assign negative weights to words like 'war'), the pipeline will:
 1. Generate synthetic text where metaphor keywords and sentiment scores are **independent** (randomly assigned) for the primary validation run.
 2. This ensures that any correlation found is due to the pipeline's ability to detect noise (null result), not a tautology of the generation script.
 3. **Stress Test**: A subset of the synthetic data will be generated with a **known correlation** (e.g., r=0.5) between metaphor count and sentiment to verify the regression engine can detect a signal.
- **Model**: Robust Linear Regression (Huber-White SE) with `vader_compound` as outcome, `metaphor_count` as predictor, and `post_length`/`engagement` as controls (FR-006).
- **Collinearity**: VIF check (FR-009). If VIF ≥ 5, robust SEs are reported, and the limitation is noted.

### Phase 3: Visualization & Reporting (US-3)
- **ANOVA**: Bar chart with error bars (95% CI) for mean CAMI scores by condition.
- **Regression**: Scatter plot of metaphor density vs. sentiment with fitted regression line (for both null and stress-test subsets).
- **Output**: Statistical results (F, p, coefficients) and images saved to `data/derived/`.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Bonferroni correction applied to the 3 pairwise comparisons (alpha_adj = 0.05/3 ≈ 0.0167).
- **Power**: The experimental sample size (N=159) is calculated for a medium effect size (f=0.25). If the actual simulated sample is smaller, a post-hoc power analysis will be documented.
- **Causal Framing**: Causal claims are restricted to the experimental arm. The discourse analysis is explicitly labeled as **associational** (and methodological for US-2).
- **Collinearity**: Predictors in the discourse model (metaphor count, length, engagement) will be checked for VIF. If high, the model will not claim independent effects for correlated predictors.
- **Data Limitation**: The lack of a verified open discourse corpus is a known limitation. The results from the discourse arm are methodological demonstrations, not ecological generalizations.
- **Lexicon Bias**: The plan explicitly addresses VADER's lexical bias by ensuring the synthetic data generation is independent of the VADER lexicon, avoiding mechanical correlations.

## Decision/Rationale

- **CPU-First**: All methods (ANOVA, VADER, Robust Regression) are computationally lightweight and run efficiently on CPU. No GPU is required.
- **Data Fallback**: Due to the absence of a verified open discourse corpus in the provided list, a synthetic fallback is used to ensure the pipeline is testable and reproducible. This adheres to the spec's "Assumption about data source" (static fallback).
- **VADER Usage**: VADER is used strictly for general polarity as per FR-004. The plan explicitly avoids claiming it measures stigma. The use of independent synthetic data mitigates lexical bias.
- **Simulation Integrity**: The experimental simulation defaults to null effects to validate the pipeline's ability to detect non-significance, avoiding the guarantee of a positive result.
- **Versioning Discipline**: Synthetic data generation parameters (seeds, correlation coefficients for stress test) are stored in `config/simulation_config.yaml` to ensure bit-for-bit reproducibility of the synthetic data on any run.