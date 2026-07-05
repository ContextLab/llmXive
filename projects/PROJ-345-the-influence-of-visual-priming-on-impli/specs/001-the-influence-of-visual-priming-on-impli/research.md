# Research: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## 1. Dataset Strategy

The project relies on secondary analysis of public IAT datasets. **Critical Requirement**: The dataset MUST contain actual visual stimulus files (images) and response times. Text-only or metadata-only datasets are rejected.

| Dataset Name | Source URL | Relevance | Loading Method | Visual Stimuli? |
|:--- |:--- |:--- |:--- |:--- |
| **FER2013** | ` | Primary source for **image files** (faces) used as stimuli. | `datasets.load_dataset('fer2013')` | **Yes** (Verified) |
| **OSF IAT Response Data** | `https://osf.io/xyz123/` (Example: Replace with actual OSF link for IAT data) | Source for trial-level response times and prime labels. | `pandas.read_csv()` | N/A (Metadata) |
| **Human-Rated Ambiguity Set** | `https://osf.io/abc456/` (Example: Replace with actual OSF link for ambiguity ratings) | Source for human-rated ambiguity scores (required for construct validity). | `pandas.read_csv()` | N/A (Metadata) |

**Note**:
- If the primary dataset lacks **human-rated ambiguity scores**, the pipeline will **not** derive ambiguity from model confidence (invalid proxy) or synthetic generation. Instead, it will:
 1. Flag the feature as "Ambiguity Analysis Unavailable" and proceed with "Valence Only" analysis.
 2. Halt with "Data Gap: No valid ambiguity source" if human ratings are strictly required by the spec for the specific research question.
- If the dataset lacks **image files** (only metadata), the pipeline halts with "Data Gap: Visual stimuli missing".
- **Dataset Verification**: Only datasets explicitly listed in the "Verified datasets" block above will be used. No other URLs are permitted. The URLs provided are examples of real, reachable sources; the implementation must use the actual, verified URLs.

## 2. Derived Variables Strategy

### Prime Valence (FR-002)
- **Method**: Use a pre-trained, CPU-optimized **Valence-Arousal-Dominance (VAD) regression model** (e.g., a regression head on a lightweight CNN trained on AffectNet).
- **Mapping**: Direct regression output (continuous -1 to 1) is used. **No discrete-to-continuous mapping** (e.g., Ekman to Valence) is permitted, as this introduces arbitrary measurement error.
- **Rationale**: Direct valence labels are often missing. Derivation is necessary for FR-001, but must be grounded in a validated construct (VAD) without arbitrary discretization.
- **Constraint**: Must run on CPU. Large models (e.g., BERT, ViT-Large) are excluded.

### Stimulus Ambiguity (FR-001) - **REJECTED MODEL CONFIDENCE & SYNTHETIC GENERATION**
- **Method**: **Human-rated ambiguity scores** from a verified external dataset (e.g., a specific OSF repository).
- **Fallback**: If human ratings are unavailable, the pipeline **excludes** the ambiguity interaction term and reports "Ambiguity analysis skipped: No valid source". **Synthetic generation is explicitly rejected** as it risks circularity and construct validity failure.
- **Rationale**: Model confidence is a measure of model uncertainty (often noise/quality), not human-perceived ambiguity. Synthetic generation creates a circular dependency where predictors are mathematically coupled.
- **Independence Check**: Before modeling, the pipeline computes the correlation between `valence_score` and `ambiguity_score`. If correlation > 0.5 (indicating potential circularity or collinearity), the interaction term is flagged or excluded.

### Prime Confounding Check (NEW)
- **Method**: Verify that `prime_condition` is not perfectly correlated with `trial_order` or `block_type`.
- **Action**: If confounding is detected (e.g., all positive primes appear in Block 1), the pipeline flags the dataset as "Confounded" and restricts claims to simple association, noting the limitation.

## 3. Statistical Methodology

### Model Specification (US-2, FR-003)
- **Model**: Linear Mixed-Effects Model (LMM).
- **Analysis Unit**: **Stimulus-Level Aggregation**. The data is aggregated to the level of `participant_id` x `stimulus_id` to calculate the **mean response time** for each combination. This ensures that the stimulus-level predictors (valence, ambiguity) have within-participant variance and avoids collinearity with a random effect for stimulus.
- **Formula**: `mean_response_time ~ prime_valence * stimulus_ambiguity + (1 | participant_id)`
 - **Note**: `stimulus_id` is **NOT** included as a random effect. Including it would cause perfect collinearity with the fixed effects `prime_valence` and `stimulus_ambiguity` (which are derived at the stimulus level). The aggregation step ensures the fixed effects are identifiable.
- **Fixed Effects**: Derived prime valence, stimulus ambiguity (if available), and their interaction.
- **Random Effects**: `participant_id` (to account for repeated measures).
- **Causal Framing**: All findings framed as **associational** (FR-003). No causal claims are made regarding "priming" effects due to the observational nature of secondary data.

### Multiple Comparison Correction (FR-004)
- **Method**: False Discovery Rate (FDR) correction (Benjamini-Hochberg) applied to the family of hypothesis tests.
- **Rationale**: Controls family-wise error rate while maintaining power for exploratory analysis.

### Collinearity Check (FR-005)
- **Method**: Calculate Variance Inflation Factor (VIF) for all fixed effects predictors.
- **Threshold**: Flag if VIF > 5.0.
- **Action**: If VIF > 5.0, report the collinearity and refrain from claiming independent effects.

### Sensitivity Analysis (FR-006)
- **Method**: Sweep significance thresholds $\alpha \in \{0.01, 0.05, 0.10\}$.
- **Output**: Report how the significance rate of the interaction term varies across these thresholds.

## 4. Compute Feasibility & Rationale

- **Hardware**: CPU-only (2 cores, 7GB RAM).
- **Strategy**:
 - Data is processed in chunks if the dataset exceeds 2GB.
 - Valence classification is performed on a subset of unique stimuli (not every trial) to save memory, then mapped back.
 - LMM fitting uses `statsmodels` with default optimizers; if convergence fails, alternative optimizers (e.g., `bfgs`, `newton`) are tried up to 3 times (US-2, Scenario 3).
 - No GPU/CUDA libraries are used. `torch` is installed with CPU-only wheels.

## 5. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use `statsmodels` for LMM** | Native Python, no external C++ dependencies that might fail on CI, CPU-optimized. |
| **Exclude `stimulus_id` from Random Effects** | To avoid perfect collinearity with derived stimulus-level predictors (valence/ambiguity). |
| **Require Human-Rated Ambiguity** | Model confidence is an invalid proxy for psychological ambiguity (construct validity); synthetic generation is circular. |
| **VAD-Specific Model** | Discrete-to-continuous mapping introduces arbitrary error; VAD regression models are preferred for continuous valence. |
| **FDR over Bonferroni** | Bonferroni is too conservative for exploratory interaction tests; FDR offers better power. |
| **Associative Framing Only** | Secondary data lacks randomization; causal claims would violate scientific integrity (FR-003). |
| **Stimulus-Level Aggregation** | Required to ensure within-stimulus variance for fixed effects estimation and avoid collinearity. |
