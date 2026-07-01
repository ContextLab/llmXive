# Research: The Impact of Predictive Coding Errors on Subjective Time Perception

## Summary of Research Strategy

This research evaluates the association between stimulus surprisal (a proxy for prediction error) and subjective time duration estimates. The strategy relies on secondary analysis of existing public datasets. The core challenge is ensuring dataset variable fit: verifying that datasets contain sequential stimulus data and duration estimates. If explicit predictability metrics are absent, a first-order Markov model will compute surprisal. Statistical analysis will employ Linear Mixed-Effects Models (LMM) to account for repeated measures, with rigorous sensitivity analysis for Minimum Detectable Effect (MDE).

**CRITICAL FINDING**: The current "Verified datasets" block provided in the user message **does not contain any dataset explicitly identified as a time perception or duration estimation study**. The listed datasets (NLP, Twitter, Robotics) lack the dependent variable ("duration estimates") and the specific experimental paradigm required. Consequently, **Gate 0** (defined in `plan.md`) will block this project from proceeding until a valid dataset is added to the verified list.

## Dataset Strategy

The analysis will utilize datasets from OpenML and HuggingFace. **Crucially, only the datasets listed in the "Verified datasets" block of the user message are eligible for citation and use.**

| Dataset Name | Source URL | Variable Availability | Fit Assessment |
|--------------|------------|-----------------------|----------------|
| **MDE (Parquet)** | https://huggingface.co/datasets/Sleoruiz/dataset-tokenized-mdeberta/resolve/main/data/test-00000-of-00002-2a6bdc48f6e79516.parquet | Token sequences, probabilities. | **Mismatch**: Contains sequential data (tokens) but **NO duration estimates**. Excluded. |
| **MDE (Parquet 2)** | https://huggingface.co/datasets/mderuiter/cryptoTwitterData/resolve/main/tweets.parquet | Tweet sequences. | **Mismatch**: Contains crypto-twitter data. **NO duration estimates** or time perception tasks. Excluded. |
| **EVERY (CSV)** | https://huggingface.co/datasets/lang-uk/every_prompt/resolve/main/every_prompt_stats.csv | Prompt statistics. | **Mismatch**: Lacks sequential stimulus timing and duration estimates. Excluded. |
| **EVERY (Parquet)** | https://huggingface.co/datasets/USC-PSI-Lab/humanoid-everyday/resolve/main/data/chunk-000/episode_000000.parquet | Humanoid everyday episodes. | **Mismatch**: Likely robotics data. **NO human duration estimates**. Excluded. |
| **EVERY (Parquet 2)** | https://huggingface.co/datasets/tarteel-ai/everyayah/resolve/main/data/test-00000-of-00013-18d88ded65aa7b53.parquet | Audio/Recitation data. | **Mismatch**: Religious recitation data. **NO time perception metrics**. Excluded. |

**Gap Analysis**: The provided "Verified datasets" block **does not contain any dataset explicitly identified as a time perception or duration estimation study**. The spec requires "sequential stimuli with known predictability manipulations" and "duration estimates."
- **Action**: The `download.py` script will attempt to fetch these datasets.
- **Fallback**: If none of the verified datasets contain the required variables (duration estimate, stimulus timing), the pipeline will log a critical exclusion in `data/README.md` stating: *"No verified dataset in the allowed list contains both sequential stimulus data and human duration estimates. The project cannot proceed with the current dataset list. The spec requires a dataset with these specific variables."*
- **Note**: The plan **cannot** invent a new dataset URL. If the verified list is insufficient, the project is blocked at the data acquisition phase (Gate 0). The implementation will strictly adhere to the verified list.

*Self-Correction for Implementation*: The spec assumes such datasets exist. The research phase must verify this. If the verified list is empty of suitable data, the `plan.md` must acknowledge this fatal mismatch. For the purpose of this plan, we assume the implementation will check for the presence of `duration_estimate` or similar columns. If absent, the dataset is dropped.

## Statistical Methodology

### Model Specification
- **Outcome**: Duration Estimate (continuous).
- **Fixed Effects**: Surprisal (continuous), Sequence Length, Stimulus Modality.
- **Random Effects**: Participant ID (Random Intercept).
- **Formula**: `Duration ~ Surprisal + Sequence_Length + Modality + (1 | Participant_ID)`

### Rigor & Assumptions

#### Construct Validity & Limitations
1.  **Surprisal vs. Prediction Error**: Surprisal measures *stimulus uncertainty* (a statistical property), not necessarily the *latent participant prediction error* (a cognitive mechanism). The analysis tests the association between stimulus surprisal and duration estimates.
    *   **Constraint**: This proxy is only valid if the dataset has a known experimental design (e.g., oddball paradigm) where transition probabilities are definable. For unstructured sequences (e.g., tweets), the computed surprisal is a proxy for linguistic complexity, not temporal prediction error. Such datasets will be excluded.
2.  **Causal Inference**: The analysis is **observational** (no random assignment to predictability conditions within participants in the secondary data context). Findings are framed as **associational**. No causal claims (moderation/mediation) are made without an identification strategy.
3.  **Confounding Control**: The model controls for sequence length and modality. However, in unstructured data, surprisal may be confounded with semantic complexity. The plan explicitly flags this limitation.

#### Multiple Comparisons & Power
1.  **Multiple Comparisons**: If >1 hypothesis test is run (e.g., multiple datasets or multiple covariates tested separately), Bonferroni or Benjamini-Hochberg correction will be applied. Family-wise error rate controlled at α ≤ 0.05.
2.  **Power & MDE**: Sensitivity analysis will calculate the Minimum Detectable Effect (MDE) for power=0.80 given the observed sample size and variance using `pingouin`. If the observed effect is smaller than the MDE, this is reported as a limitation.
3.  **Measurement Validity**: Instruments used in the source datasets are assumed validated. If non-validated measures are found, they are flagged in `data/README.md`.
4.  **Collinearity**: If surprisal is definitionally related to sequence length (e.g., bounded), collinearity diagnostics (VIF) will be run. If VIF ≥ 5, independent effects are not claimed; relationships are described descriptively.

### Computational Constraints
- **Environment**: CPU-only (2 cores, 7 GB RAM).
- **Methods**: `statsmodels` for LMM (CPU-tractable), `pingouin` for MDE and effect sizes, `scipy` for Shapiro-Wilk, `joblib` for parallel bootstrap.
- **Data Handling**: Streaming aggregation for datasets >500 MB. Sampling to ≤5000 trials if necessary to meet runtime constraints.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use First-Order Markov Model for Surprisal** | Explicit predictability metrics are often missing. A first-order Markov model is the standard, computationally cheap approximation for surprisal in sequential tasks. **Only applied to structured experimental data.** |
| **Exclude Datasets Missing Duration Estimates** | The research question is about *subjective time*. Without duration estimates, the hypothesis cannot be tested. |
| **Observational Framing** | Secondary data rarely allows for causal inference. Framing as associational prevents overclaiming. |
| **CPU-Only Execution** | Mandatory for GitHub Actions free-tier compliance. GPU methods are excluded. |
| **Blocker Protocol** | If no valid dataset is found in the verified list, the project halts at Gate 0. No analysis is performed on invalid data. |
| **Pingouin for MDE** | `statsmodels` does not natively support easy MDE calculation for LMMs. `pingouin` is used for robust power analysis. |