# Research: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments (Methodological Validation)

## Dataset Strategy

| Dataset Name | Verified Source URL | Role in Study | Data Availability Note |
|--------------|---------------------|---------------|------------------------|
| MFQ (Moral Foundations Questionnaire) | ` | Source of foundation scores (covariates). | Direct download via HuggingFace. Contains `foundation_scores` columns. |
| Moral Stories | ` | Source of moral vignettes (text). | Direct download. Contains text stories to be mapped to VR scenes. |
| OSF Loglikelihood (Supplemental) | ` | Potential source of additional covariates if needed. | Used only if MFQ lacks specific demographic controls. |

**Critical Data Gap & Resolution**:
The spec requires "actual VR interaction logs" (response times, gaze tracking). The verified datasets **do not** contain these fields.
- **Resolution**: The plan implements a **Simulation Layer** (`code/processing/simulate_logs.py`). This layer generates plausible `response_time` and `gaze_metrics` for each participant/story pair, conditioned on the `salience_level` (low/high) and the story content.
- **Justification**: This is necessary to satisfy FR-006 (capture VR data) without fabricating "real" participant data. The simulation will use a statistical model (e.g., log-normal for RT) with parameters derived from literature on VR reaction times, ensuring the generated data is statistically valid for the Bayesian model. The source of the simulation parameters will be cited in `research.md`.
- **Constraint**: The simulation is explicitly labeled as "simulated" in the data schema and logs. The primary analysis focuses on the *effect of salience* on the *simulated* logs, treating the simulation as a controlled experimental design rather than observational data.
- **Re-scoped Goal**: The study is **not** testing the hypothesis that "salience modulates human moral judgment". It is testing the hypothesis that "the Bayesian pipeline correctly recovers the ground-truth salience effect injected into the simulation".

**Future Data**: For Phase 5 (Real Data Integration), potential real VR datasets (e.g., from OpenNeuro or similar repositories) will be sought. No such dataset is currently verified in the open list.

## Methodological Rigor

### Ground Truth Injection
To validate the pipeline, the simulation layer will inject a known `ground_truth_effect` (e.g., 0.5) for the `salience_level` predictor. The Bayesian model's posterior distribution for this coefficient will be compared against the injected value. Success is defined by:
1. **Bias**: The difference between the posterior mean and the ground truth is < 0.1.
2. **Coverage**: The 95% credible interval includes the ground truth value in > 90% of simulation runs.

### Statistical Plan
1. **Bayesian Decision Model (FR-002, FR-003)**:
 - **Model**: Hierarchical Bayesian regression (PyMC5).
 - **Likelihood**: Gaussian (for continuous judgment ratings).
 - **Priors**: Normal(0, 1) for coefficients (weakly informative).
 - **Predictors**: `salience_level` (fixed effect), `foundation_scores` (covariates), `salience × foundation` (interaction).
 - **Inference**: NUTS sampler (PyMC).
 - **Convergence**: R-hat < 1.05, effective sample size > 200.
 - **Model Comparison**: Calculate WAIC and AIC for Salience Model vs. Baseline (no salience). Report ΔAIC.
 - **Multiple Comparisons**: Bonferroni correction applied to the interaction terms in the frequentist validation step (FR-004).

2. **Mixed-Effects Regression (FR-004)**:
 - **Method**: `statsmodels` MixedLM.
 - **Random Effects**: `(1 | participant_id)`.
 - **Fixed Effects**: `salience_level`, `foundation_scores`, `interaction`.
 - **Correction**: Bonferroni correction for the number of foundation tests (e.g., N foundations → α/N).

3. **Sensitivity Analysis (FR-005)**:
 - Sweep ΔAIC thresholds: {,, 20}.
 - Report model selection stability (proportion of runs selecting the salience model).

4. **Parameter Recovery (Validation)**:
 - Compare recovered posterior means of the `salience_effect` against the `ground_truth_effect` injected by the simulation.
 - Calculate the bias and coverage of the 95% credible interval.

### Methodological Distinction
This project explicitly distinguishes between:
- **Model Recovery**: Testing if the statistical code correctly recovers known parameters from simulated data. (Primary Goal)
- **Hypothesis Testing**: Testing if a theoretical effect exists in the real world. (Not possible with current data)

### Statistical Rigor Checklist
- **Multiple Comparisons**: Bonferroni applied to interaction tests (5 foundations).
- **Power/Sample Size**: MDES report (T045) will calculate required N for ΔAIC > 10. If available real data < required N, the simulation layer will generate the necessary sample size (with clear labeling) to meet power requirements, noting the limitation.
- **Causal Inference**: This is a *simulation* design. Claims are framed as "causal effect of salience manipulation" *within the simulation*, not general causal claims about real-world VR.
- **Measurement Validity**: MFQ scores are used as is. Validation of VR simulation against literature parameters is included in `research.md`.
- **Collinearity**: Foundation scores are correlated. The model will report VIF (Variance Inflation Factor) and acknowledge collinearity in the discussion.

## Limitations
- **Data Modality**: The study relies on simulated VR logs. No real human behavioral data (RT, gaze) in a VR context is available in the verified datasets. This limits the ability to draw empirical conclusions about human cognitive mechanisms.
- **External Validity**: Results are valid for the *simulated* data generation process, not necessarily for real-world VR interactions.
- **Future Work**: Phase 5 is required to ingest real VR data to test the original hypothesis.

## Compute Feasibility

- **CPU-First**: PyMC 5 is optimized for CPU. The model will run on the GitHub Actions free tier using a sample of participants.
- **GPU Escape Hatch**: If the model fails to converge on CPU within 4 hours, the execution stage will auto-offload to a Kaggle GPU (CUDA). The plan uses `device="cpu"` by default but includes a fallback flag for `device="cuda"`.
- **Data Streaming**: `datasets.load_dataset(..., streaming=True)` will be used to avoid loading the full dataset into memory. Only the required sample will be materialized for the model.

## Decision Rationale

- **Why PyMC5?**: Required by spec (FR-002) and is the modern successor to deprecated PyMC3.
- **Why Simulated VR Logs?**: Real data is unavailable. Simulation allows the statistical model to be tested against the experimental design (salience manipulation) without fabricating "real" participant data.
- **Why CPU?**: PyMC 5 is efficient on CPU for moderate N (200). GPU is only needed for large N or complex hierarchical structures not present here.
- **Why Parameter Recovery?**: Since the data is synthetic, the only way to validate the model is to check if it recovers the known parameters. This validates the *pipeline*, not the *human hypothesis*.