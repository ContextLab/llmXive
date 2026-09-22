# Research: The Influence of Chatbot Politeness on User-Perceived Quality

## Summary

This research plan outlines the methodology to test the hypothesis that higher linguistic politeness in chatbot responses correlates with higher user-perceived quality. The study leverages existing open-source dialogue datasets to avoid data acquisition barriers, ensuring feasibility on GitHub Actions free-tier runners.

## Dataset Strategy

The project relies on two primary datasets, both verified as open and programmatically accessible. Persona-Chat is **not** in the verified list and is excluded from the implementation plan.

| Dataset | Purpose | Source URL (Verified) | Access Method |
|---------|---------|-----------------------|---------------|
| **EmpatheticDialogues** | Primary source for dialogue context and `quality_rating` (1-5 Likert). | ` | `datasets.load_dataset(..., split="test")` |
| **HCI_P2** | Secondary source for dialogue diversity, `quality_rating`, and demographic metadata. | ` | `datasets.load_dataset(..., data_files=...)` |

**Dataset Fit Verification**:
- **EmpatheticDialogues**: Contains `utterances` (text), `emotion` (context), and `quality_rating` (proxy for trust). **Verified**.
- **HCI_P2**: Contains `age`, `gender`, `quality_rating` (1-5 Likert), and `utterances`. **Verified**. Columns explicitly confirmed in dataset documentation.
- **Persona-Chat**: Not in verified list. **Action**: Excluded from implementation. FR-001 satisfied by EmpatheticDialogues and HCI_P2.

**Data Volume & Streaming**:
- EmpatheticDialogues: a large-scale dataset of dialogues.
- HCI_P: ~5k dialogues.
- Total estimated text volume: substantial.
- **Strategy**: Use `datasets.load_dataset(..., streaming=True)` to iterate over utterances without loading the full dataset into RAM. Aggregate statistics (mean politeness) on the fly.

**Data Download & Filtering Logic (T017)**:
1. Download raw data to `data/raw/`.
2. Filter dialogues:
 - Exclude if `quality_rating` is missing (log count).
 - Exclude if no chatbot utterances exist (log count).
 - Exclude if `utterances` list is empty (log count).
3. Store filtered data in `data/processed/`.

**Validation Logic (T016)**:
1. Check for required columns: `utterances`, `quality_rating`, `annotator_id`.
2. Verify `quality_rating` is integer 1-5.
3. Verify `utterances` is a list of objects with `text` and `speaker`.
4. Log validation errors and excluded rows.

## Statistical Methodology

### Primary Analysis: Cumulative Link Mixed-Effects Model (CLMM)
- **Model Formula**: `quality_rating ~ politeness_score + conversation_length + dataset_source + (1 | annotator_id)`
- **Outcome**: `quality_rating` (Ordinal: 1-5).
- **Predictors**:
 - `politeness_score`: Z-scored mean politeness per dialogue (within-dataset).
 - `conversation_length`: Word count of bot utterances.
 - `dataset_source`: Fixed effect covariate to control for baseline distribution differences.
 - `annotator_id`: Random intercept to account for rater-specific bias (FR-003).
- **Software**: R `ordinal` package (`clmm()` function).
- **Assumptions**:
 - **Associational**: No random assignment; claims limited to association.
 - **Collinearity**: VIF check for `politeness_score` and `conversation_length`. If VIF > 5, the hypothesis that politeness has an independent effect is untestable. We will report the joint effect of politeness and length and note the limitation.
 - **Proportional Odds**: Assumed for CLMM; tested via Brant test or likelihood ratio.
- **Causal Interpretation Guardrails**:
 - Claims strictly framed as associational.
 - **E-Value Sensitivity Analysis**: E-values will be calculated for the main effect. If E-value < 1.5, causal claims are explicitly rejected in the final report. This threshold bounds unobserved confounding.

### Unit of Analysis Clarification
- **Quality Rating**: In EmpatheticDialogues, `quality_rating` is often per-utterance. If so, we will aggregate to the dialogue level (mean of turn ratings) to match the predictor (mean politeness per dialogue).
- **Random Effect**: `annotator_id` is used instead of `user_id` because in crowdsourced datasets, the "user" is the annotator. This controls for rater-specific bias in quality rating, which is the relevant source of variance.

### Robustness Checks (Reframed as Construct Validity Check)
1. **Alternative Classifier**: Re-run analysis using **textstat** (open-source) as a fallback for LIWC-2015.
 - **Limitation**: LIWC-2015 is proprietary and unavailable. The fallback to `textstat` is a **Construct Validity Check**, not a direct validation of the same construct. We explicitly acknowledge that comparing BERT-based politeness to lexicon-based word counts does not validate the same semantic construct (FR-005 Not Met).
2. **Subgroup Analysis**:
 - Split by `age` and `gender` (if metadata available in HCI_P2).
 - **Condition**: Only proceed if $n \ge 30$ per subgroup (FR-006).
 - **Correction**: Benjamini-Hochberg (BH) for multiple subgroup tests.

### Multiple Comparison Correction
- **Method**: Benjamini-Hochberg (BH) for all hypothesis tests (main effect + covariates + subgroups).
- **Rationale**: Controls False Discovery Rate (FDR) while maintaining power, preferred over Bonferroni for exploratory subgroup analyses.
- **Measurement**: Significance measured against p < 0.05 threshold (SC-005).

### Compute Feasibility

#### CPU-Only Strategy
- **Data Loading**: Streaming via `polars` or `datasets` (Python).
- **Politeness Scoring**: `jfiedler/politeness-bert` (small BERT model).
 - **Feasibility Calculation**: ~100k utterances. BERT inference on a multi-core CPU takes [deferred] per utterance. Total time: [deferred] * 0.0015s = 150s (2.5 mins) for inference, plus overhead. Even with conservative estimates, total time is [deferred]. Total pipeline estimated at approximately a few hours. **Fits within 6h limit**.
 - **Memory**: Model size < 100MB; batch processing keeps RAM usage low.
- **CLMM Fitting**: R `clmm()` on CPU.
 - **Feasibility**: Standard for ~20k rows; converges within minutes.

#### No GPU Escape Hatch
- **Decision**: GPU escape hatch removed to ensure reproducibility and CI determinism. CPU-Only strategy is verified to be feasible.

### Measurement Mechanisms
- **Runtime (SC-001)**: Measured using `time` command in shell scripts and `time` package in R. Results written to `results/metrics.json`.
- **Memory (SC-002)**: Measured using `psutil` in Python and `pryr` in R. Peak usage written to `results/metrics.json`.
- **Convergence (SC-003)**: CLMM convergence status logged. Rate calculated as (converged models / total attempts).
- **Effect Size (SC-004)**: **Spearman correlation** of predicted quality scores between primary and fallback models. **Threshold r ≥ 0.80**.
- **Significance (SC-005)**: Measured against p < 0.05 after BH correction.

## Ethical Considerations
- **PII**: User IDs are anonymized. Demographic data used only for statistical grouping, not individual identification.
- **Bias**: Politeness models may have cultural bias; acknowledged as a limitation.
- **Causality**: Claims strictly framed as associational.
