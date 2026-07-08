# Research: The Impact of Linguistic Complexity on Trust in AI-Generated Text

## Background & Hypothesis

**Research Question**: Does linguistic complexity (syntactic and lexical) in AI-generated text predict readers' trust ratings when the source is explicitly identified as AI-generated?

**Hypothesis**: There is a non-linear (inverted-U) relationship between linguistic complexity and trust. Moderate complexity maximizes trust, while very low (too simple) or very high (too complex) complexity reduces trust.

**Theoretical Basis**: Prior work in psycholinguistics suggests that readability affects comprehension and perceived credibility. Overly simple text may be perceived as childish or lacking authority, while overly complex text may be perceived as obfuscating or hard to process, reducing trust. The "inverted-U" curve is a common pattern in cognitive load theory.

## Dataset Strategy

| Dataset | Source | Purpose | Variables | Verification |
|---------|--------|---------|-----------|--------------|
| **Wikipedia Corpus** | `datasets.load_dataset("wikitext", "wikitext-2-raw-v1")` | Source material for text generation | Raw text paragraphs | Verified via HuggingFace Datasets library (canonical source) |
| **MTLD Metadata** | https://huggingface.co/datasets/Abeyankar/mtl_ds_full_fin/resolve/main/metadata.json | Reference for MTLD calculation methodology | MTLD scores, text samples | Verified URL (listed in "# Verified datasets" block) |
| **Prolific Survey Data** | N/A (Primary Collection) | Trust ratings (dependent variable) | ParticipantID, TextSampleID, TrustRating (1-5), AttentionCheckStatus | Collected via Prolific API; no external dataset needed |

**Note**: The Wikipedia corpus is used to generate text samples, not as a direct analysis dataset. The MTLD metadata is cited for methodological reference only. The primary analysis dataset is generated locally (FR-001) and collected via survey (FR-003).

**Dataset Fit Confirmation**:
- **Wikipedia**: Contains diverse text with varying complexity. When processed by Gemma-2B with prompt variations (e.g., "rewrite in simple terms", "rewrite in academic style"), it will produce samples spanning the target FK range (5.0–12.0).
- **MTLD Reference**: Provides the algorithm for MTLD calculation (Paquot & Plonsky, 2017). The implementation will follow this standard.
- **Prolific**: Will provide the trust ratings (1–5 Likert) and attention check responses. The sample size target (N ≥ 100) is feasible via Prolific.

**No Missing Variables**: The spec requires text samples (generated), complexity metrics (computed), and trust ratings (collected). All are covered. No external dataset is needed for the dependent variable (trust), as it is collected de novo.

## Methodology & Statistical Plan

### Phase 1: Data Generation (FR-001, FR-002)
1. Load Wikipedia text (Wikitext-2).
2. Use Gemma to generate text samples with prompt variations targeting different complexity levels.
3. Compute metrics for each sample:
   - **Flesch-Kincaid (FK)**: Readability score (syntactic).
   - **MTLD**: Measure of lexical diversity.
   - **Sentence Length**: Average words per sentence (syntactic).
4. Validate variance: Ensure FK range spans 5.0–12.0 (SC-001). If not, adjust prompts and regenerate.

### Phase 2: Data Collection (FR-003, FR-004)
1. Deploy survey via Prolific (or simulate for CI testing).
2. **Experimental Design**: Within-subjects. Each participant rates a random subset of 10 text samples (total N_data = 1000 observations).
3. Present each text sample labeled as "AI-Generated".
4. Collect Likert trust ratings.
5. Include attention checks (e.g., "Select 'Strongly Disagree' for this item").
6. Filter out participants who fail attention checks or straight-line (all same rating).
7. Target N ≥ 100 valid participants (SC-002).

### Phase 3: Statistical Analysis (FR-005, FR-006, FR-007, FR-008)
1. **Factor Construction (PCA)**:
   - Perform Principal Component Analysis (PCA) on FK and Sentence Length to derive a single orthogonal **Syntactic Factor**. This resolves the definitionally collinear nature of FK and ASL (Constitution VII).
   - Retain MTLD as the **Lexical Factor**.
   - Verify orthogonality (negligible correlation) between Syntactic and Lexical factors.

2. **Primary Analysis (Multilevel Modeling)**:
   - Fit two separate Linear Mixed-Effects Models (LME) with random intercepts for participants to account for within-subject non-independence.
   - **Model 1 (Syntactic)**: `Trust ~ Syntactic_Factor + Syntactic_Factor² + (1 | ParticipantID)`
   - **Model 2 (Lexical)**: `Trust ~ Lexical_Factor + Lexical_Factor² + (1 | ParticipantID)`
   - Test: Significance of the quadratic term (p < 0.05) for the inverted-U hypothesis.
   - **Assumption Check**: Treat Likert as interval for LME (standard practice), but validate via co-primary ordinal model.

3. **Multiple Comparison Correction**:
   - Apply **Benjamini-Hochberg (FDR)** correction for the 2 tests (Syntactic vs. Lexical). FDR is robust to dependency and more appropriate than Bonferroni for correlated factors.
   - Log correction method and adjusted q-values.

4. **Power Analysis**:
   - Conduct **a priori** power analysis to determine the Minimum Detectable Effect Size (MDES) for the quadratic term given N=100 participants and 10 observations each.
   - If power < 0.80, report MDES as a limitation rather than claiming sensitivity.

5. **Sensitivity Check**:
   - **Ordinal Model**: Run an Ordinal Logistic Mixed-Effects Model (co-primary analysis) for both factors. If the sign/significance of the quadratic term differs from the linear model, the hypothesis is considered inconclusive.
   - **Metric Sensitivity**: Verify that the PCA-derived Syntactic Factor yields consistent results with a robustness check using only FK (if MTLD is excluded).

6. **Visualization**: Generate plots of Trust vs. Complexity (Factor Scores) with fitted curve and confidence interval.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Benjamini-Hochberg (FDR) applied for 2 orthogonal tests.
- **Power**: A priori power analysis reported. If N < 100 or power < 0.80, MDES is reported as a limitation.
- **Causal Framing**: Study is observational (trust ratings vs. complexity). Claims framed as associational, not causal. No randomization of complexity (it is a property of the text).
- **Measurement Validity**: 
  - FK and Sentence Length are standard syntactic metrics, combined via PCA to form an orthogonal factor.
  - MTLD follows Paquot & Plonsky (2017) methodology.
  - Likert scale treated as interval for LME (standard), validated via Ordinal Logistic Regression (co-primary).
- **Collinearity**: FK and Sentence Length are definitionally related. PCA is used to create a single orthogonal predictor, eliminating multicollinearity in the regression model.

## Compute Feasibility

- **Gemma-2B**: Runs on CPU (default precision) with ~2 GB RAM for inference. 200 samples will take < 1 hour.
- **Analysis**: `statsmodels` mixedlm and `scikit-learn` PCA are CPU-tractable. N=1000 observations is trivial for LME.
- **Total Runtime**: < 6 hours on GitHub Actions free-tier.
- **Memory**: < 6 GB peak (LLM + data processing).
- **Disk**: < 14 GB (text samples + survey data + plots).

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Generated text lacks FK variance (5.0–12.0) | Adjust prompts (e.g., "simplify to 5th grade", "complexify to academic") and regenerate. Log variance. |
| Prolific API error / N < 100 | Simulate survey data for CI testing; report limitation if N < 100 in paper. |
| Straight-lining / low-quality responses | Attention checks + exclusion criteria (FR-004). |
| Model non-convergence | Check for NaN/Inf; if occurs, report failure (SC-004). |
| No significant quadratic term | Report null result; hypothesis rejected. |
| Low Power | Report MDES; acknowledge inability to detect small effects. |