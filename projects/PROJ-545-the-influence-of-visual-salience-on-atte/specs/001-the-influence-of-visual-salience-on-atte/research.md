# Research: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

## Dataset Strategy

| Dataset Name | Purpose | Source / URL | Verification Status |
|:--- |:--- |:--- |:--- |
| Moral Machine | Primary data source (choices, attributes) | Primary: | **NO VERIFIED SOURCE** (See Note 1) |
| Moral Machine | Primary data source (choices, attributes) | Mirror 1: https://dataverse.harvard.edu/dataset.xhtml?persistentId= | **NO VERIFIED SOURCE** (See Note 1) |
| Moral Machine | Primary data source (choices, attributes) | Mirror 2: /tree/master/data | **NO VERIFIED SOURCE** (See Note 1) |
| OpenCV | Salience computation (ITTI/GBVS) | `opencv-python` library | Verified (PyPI) |
| NumPy/SciPy | aDDM Simulation | `numpy`, `scipy` libraries | Verified (PyPI) |

**Note 1 (Dataset Gap):** The Verified Datasets block for this project explicitly states `FR-001: NO verified source found` and `US-001: NO verified source found` for the Moral Machine dataset. The implementation will attempt to fetch from the canonical repository described in literature (Awad et al.), with Harvard Dataverse and GitHub mirrors as fallbacks. The Reference-Validator Agent will flag this as unverified per Constitution Principle II. The plan proceeds with the understanding that this is a known verification gap in the current system state.

**Reproducibility Impact:** Per Constitution Principle I, every result MUST be reproducible by re-running the project's `code/` against the project's `data/` on a fresh GitHub Actions runner. The dataset verification gap means the Reference-Validator Agent will flag this as unverified, potentially blocking the `research_accepted` transition. This is documented as a known constraint.

## Methodology

### 0. Culpability Label Detection (FR-008)

**Step**: Before any analysis, the system MUST scan the dataset for explicit 'actual culpability' labels. The Moral Machine dataset is a survey experiment measuring moral preferences, not real-world accident data (Awad et al., Nature).

**Expected Result**: No explicit 'actual culpability' labels will be found.

**Action**: If absent, log detection and proceed to use scenario attributes (number of lives saved/lost, species, social status, age, gender) as proxy control variables for confounding.

### 1. Salience Computation (FR-002)

- **Visual**: ITTI/GBVS algorithm via OpenCV. Converts images to saliency maps, aggregates mean intensity as `salience_score` (0.0–1.0).
- **Text**: Word-frequency and position heuristics (distinct from visual). Normalized TF-IDF score for key moral terms in text-only stimuli.
- **Edge Case**: If image URL broken, fallback to text-salience only (US-001 Edge Case).

### 2. Choice-Only aDDM Implementation (FR-003)

**Critical Limitation**: The Moral Machine dataset contains choice outcomes but **no response time (RT) data**. The standard aDDM requires RT for parameter identifiability. This study implements a **choice-only aDDM variant** that estimates salience weight from binary choices only. This constrains parameter identifiability and is explicitly acknowledged as a methodological limitation.

- **Model**: Attentional Drift Diffusion Model (choice-only variant). Drift rate modulated by salience weight ($w_s$).
- **Mathematical Formulation**: The drift rate $v$ is computed as:

 $$v = w_s \times \text{salience} + \sum_{i=1}^{k} \beta_i \times \text{attribute}_i + \epsilon$$

 Where:
 - $w_s$ is the salience weight parameter (grid searched over 0.0 to 1.0 in steps of 0.1)
 - $\text{salience}$ is the computed salience score (0.0–1.0)
 - $\beta_i$ are coefficients for scenario attribute covariates (lives saved/lost, species, social status, age, gender)
 - $\epsilon$ is noise (Gaussian)

- **Precision**: `float64` (default). No CUDA/mixed-precision.
- **Optimization**: Grid search over $w_s \in \{0.0, 0.1, \dots, 1.0\}$ (11 steps).
- **Constraint**: To meet US-002 (≤30 mins on 2 CPU), grid search runs on a stratified sample. Best $w_s$ applied to the full dataset.
- **Representative Agent Assumption**: The analysis assumes a 'representative agent' model, aggregating across participants. This is justified by the dataset structure (single-trial per participant, no individual RT data). Individual parameter variance is not estimable; this is a methodological limitation explicitly documented in the paper.

### 3. Model Comparison & Statistics (FR-005, FR-007, FR-008)

- **Baseline**: aDDM with $w_s = 0$ (no salience).
- **Metric**: AIC, BIC, Log-Likelihood.
- **Cross-Validation**: 5-fold CV on held-out choice data. **Success Criterion (SC-002)**: ≥ 95% of splits must converge within 30 minutes.
- **Simulation-Based Calibration**: Generate synthetic choice data with known salience weights to validate the fitting procedure. This provides ground truth for model comparison.
- **Correction**: Bonferroni correction applied if >3 hypothesis tests (FR-007).
- **Collinearity**: Variance Inflation Factor (VIF) computed for salience vs. attribute proxies (FR-008). Flag if VIF > 5.0.
- **VIF Remediation**: If VIF > 5.0:
 1. Report descriptive bounds (no independent effect claim)
 2. Attempt L1 regularization (Lasso) as alternative
 3. If collinearity persists, report only the joint effect of salience+attributes without claiming independence
- **Causal Framing**: All results reported as **associational correlations**. No claims of "moral virtue" caused by salience (FR-006). This addresses reviewer concerns (Socrates/Kahneman) regarding "spectacle" vs. "good".

## Statistical Rigor

- **Multiple Comparisons**: Bonferroni correction applied across threshold sweeps (0.01, 0.05, 0.10).
- **Power**: Sample size will be sufficient for stable likelihoods; however, grid search is limited to a predefined threshold for runtime. This is documented as a computational constraint, not a statistical limitation.
- **Causal Inference**: Explicitly observational. No randomization of stimuli. Claims limited to "association between salience and choice".
- **Measurement Validity**: ITTI/GBVS is standard for visual attention (cited in literature). Text heuristics validated against word-frequency norms.
- **Parameter Identifiability**: Acknowledged limitation: choice-only aDDM variant has reduced identifiability compared to full aDDM with RT data. This is a known constraint of the dataset.

## Risks & Mitigations

| Risk | Mitigation |
|:--- |:--- |
| **Dataset URL Unverified** | Document gap in `research.md`. Proceed with canonical name and fallback mirrors. |
| **Runtime Exceeds Threshold** | Subsample 10k for grid search. Use `numba` for vectorized loops. |
| **Non-convergence** | Cap retries at 3. Log failures. Exclude from aggregate (US-002 Edge Case). |
| **Collinearity** | Compute VIF. If >5.0, apply remediation steps (descriptive bounds, Lasso, joint effect). |
| **RT Data Missing** | Acknowledge as limitation. Use choice-only aDDM variant. Document in paper. |
| **Representative Agent** | Explicitly state assumption. Do not claim individual-level effects. |
| **Verification Gap** | Document in `research.md`. May block `research_accepted` per Constitution Principle II. |

