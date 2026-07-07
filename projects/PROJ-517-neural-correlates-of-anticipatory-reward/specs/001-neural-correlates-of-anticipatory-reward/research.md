# Research: Neural Correlates of Anticipatory Reward Processing in Vocal Learning

## Scientific Context

### Research Question
Does anticipatory neural activity in songbird Area X scale with expected reward magnitude?
Specifically, we test the hypothesis that the firing rate of neurons in the -500ms to 0ms window prior to reward delivery is positively correlated with the magnitude of the impending reward.

### Background
Vocal learning in songbirds (e.g., zebra finches) relies on the basal ganglia-thalamocortical loop, specifically Area X. Previous literature suggests that dopaminergic reward prediction errors (RPEs) modulate synaptic plasticity in this region. However, the trial-by-trial encoding of *expected* reward magnitude in anticipatory firing rates remains a critical, under-explored link between reinforcement learning theory and neural data.

### Methodology Overview
1. **Data Ingestion**: Load spike timestamps and trial metadata.
2. **Feature Engineering**: Calculate spike counts in the [-500ms, 0ms] window.
3. **Statistical Modeling**: Fit a Negative Binomial GLM (suitable for over-dispersed count data) with `reward_magnitude` as the predictor.
4. **Validation**: Use permutation testing (1000 iterations) to establish significance, apply Bonferroni correction for multiple neurons, and perform 5-fold cross-validation to assess model stability.
5. **Robustness**: Check for non-linearity (categorical vs continuous), over-dispersion, lack of variance in predictors, and selection bias from trial exclusion.

## Dataset Strategy

### Verified Datasets
The project relies on the following verified datasets. **No other URLs are used.**

**Critical Data Gap**: The provided verified dataset list contains generic LLM benchmark data (OpenNeuro FSLR64k, GLM jsonl, MixSub) which are **NOT** songbird electrophysiology datasets. The spec assumes the existence of "pre-processed spike train data and trial metadata from public repositories (OpenNeuro/Zenodo)" containing specific bird neural data. Since the verified dataset block does **not** contain a songbird Area X dataset:
1. **Pipeline Validation**: The `code/ingestion.py` and `code/modeling.py` will include a `--synthetic` flag to generate a synthetic dataset that mimics the expected schema (spike timestamps, reward magnitudes) for testing the pipeline logic (US-1, US-2).
2. **Scientific Discovery**: The plan **cannot** produce a valid scientific conclusion regarding neural correlates using synthetic data, as the synthetic generator likely hardcodes the relationship or assumes independence. The current output is a **Validated Pipeline**, not a scientific result. **The 'Scientific Discovery' phase is blocked until a verified real dataset is ingested.**

**Relevant Verified Sources (for reference only, schema alignment required):**
* *OpenNeuro (parquet)*: ` (Note: This is human fMRI data, not bird spikes. Used only to verify the *loader* capability if the schema were compatible, but the schema is incompatible. **Decision**: Do not use for analysis. Use synthetic data for the specific bird schema.)

**Dataset Strategy Table:**

| Dataset Name | Source URL (Verified) | Status | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **Synthetic Bird Data** | N/A (Generated) | **Primary for CI** | Used to validate FR-001 through FR-010. Generates `trial_id`, `neuron_id`, `spike_timestamps`, `reward_magnitude`. |
| **Real Songbird Data** | N/A (Not Verified) | **Blocked** | No verified songbird Area X dataset exists in the provided list. Analysis of real data is pending future data ingestion. |

**Potential Future Sources (Not Verified Yet):**
If real data becomes available, potential sources to investigate (not verified yet) include:
- **CRCNS** (Collaborative Research in Computational Neuroscience): Search for "Area X" or "zebra finch".
- **OpenNeuro**: Search for "zebra finch" or "Area X".
- **Zenodo**: Repositories associated with specific songbird electrophysiology papers (e.g., from the Brainard, Fee, or Sober labs).
*Note: These sources must be manually verified for schema compatibility and data integrity before use.*

## Statistical Rigor & Assumptions

### Model Selection
* **Distribution**: Negative Binomial. Spike count data is typically over-dispersed (variance > mean). A Poisson GLM is only used if the dispersion parameter < 1.1 (FR-010).
* **Link Function**: Log link (standard for count data).
* **Predictor**: `reward_magnitude` (continuous).
* **Outcome**: `spike_count` (integer).
* **Robustness Check (Non-linearity)**: To address potential non-linearity, a secondary model will treat `reward_magnitude` as a categorical factor. A Likelihood Ratio Test (LRT) or AIC comparison will be performed. If the categorical model fits significantly better, the linear "scaling" claim will be qualified as non-linear.

### Significance Testing
* **Permutation Test**: 1000 iterations (FR-004). We will shuffle `reward_magnitude` labels relative to `spike_count` to generate a null distribution of coefficients.
* **Multiple Comparisons**: If multiple neurons are analyzed, Bonferroni correction will be applied to the p-values to control Family-Wise Error Rate (FWER) ≤ 0.05 (SC-005).

### Power & Sample Size
* **Power Analysis**: The Minimum Detectable Effect Size (MDES) will be calculated **a priori** based on the observed sample size and variance (SC-002). This replaces the simple "30 trials per level" halt condition. If the MDES is too large (indicating low power), the project will flag this limitation rather than halting or proceeding with underpowered results.
* **Limitation**: If the dataset has < 30 trials per reward level, the system halts (FR-007). This ensures sufficient power for the GLM to converge.

### Model Stability (Cross-Validation)
* **5-Fold CV**: Per FR-008, 5-fold cross-validation will be performed. **Note**: This is **not** used to validate the scientific claim of significance (which is done by permutation), nor is it a measure of "predictive performance" in the machine learning sense. It is used strictly as a **diagnostic for model stability and overfitting**. High variance in CV scores would indicate the model is capturing noise, invalidating the coefficient estimate regardless of p-value.

### Confounding Variables & Causal Inference
* **Observational vs. Experimental**: The analysis is based on trial-by-trial variation in a controlled experimental setting. While randomization of reward magnitude is assumed in the experimental design, the analysis is framed as **associational** regarding the neural encoding of expectation.
* **Reward Independence**: A critical confound in songbird studies is that reward magnitude may be determined by the bird's own vocalization (endogenous). The plan includes a check to verify if reward magnitude is exogenous (fixed by experimenter) or endogenous. If endogenous, the analysis will be framed as "neural correlates of the behavioral-reward loop" rather than pure anticipation.
* **Selection Bias (FR-009)**: Trials with short cue-reward intervals (< 500ms) are excluded to avoid confounding anticipation with cue-evoked responses. However, this may introduce selection bias. The plan includes a "Trial Exclusion Impact Analysis" that compares the distribution of reward magnitudes in included vs. excluded trials. If excluded trials have systematically different rewards, the slope estimate may be biased.

### Measurement Validity
* **Time Window**: The -500ms to 0ms window is validated by FR-009 against cue-reward delays. If a cue occurs < 500ms before reward, the trial is flagged.
* **Spike Sorting**: The plan assumes pre-processed data (as per spec "pre-processed spike train data"). We do not perform spike sorting but validate that the input data has `neuron_id` and `timestamp` fields. **Constitution Principle VI Compliance**: The plan requires documentation of the upstream spike sorting validation criteria (e.g., SNR > 3, Isolation Distance > 20) that the provided data must have met.

## Compute Feasibility

* **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
* **Method**:
 * `statsmodels` GLM is CPU-efficient.
 * Permutation test (1000 iters) on ~5000 trials is computationally light (~minutes).
 * No GPU required.
 * Data subset to fit in RAM.
* **Fallback**: If the dataset is too large, the pipeline will sample trials to fit within the 7 GB RAM limit while maintaining the distribution of reward magnitudes.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Real Dataset** | High | Use synthetic data generator that strictly follows the schema. Document that real data is required for final scientific conclusion. **Current output is Pipeline Validation only.** |
| **Zero Variance in Reward** | High | FR-007 and FR-009 checks will halt the pipeline if variance is insufficient. |
| **Silent Neurons** | Medium | Filter out neurons with 0 spikes across all trials before modeling (Edge Case handling). |
| **Over-dispersion** | Medium | FR-010 checks dispersion; fallback to Poisson if low, otherwise use Negative Binomial. |
| **Non-linearity** | Medium | Robustness check (categorical vs continuous) will detect and flag non-linear relationships. |
| **Selection Bias** | Medium | Trial Exclusion Impact Analysis will compare reward distributions of included vs. excluded trials. |
| **Endogenous Reward** | High | Reward Independence Check will flag if reward is behavior-dependent, re-framing the interpretation. |