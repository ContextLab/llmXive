# Specification: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

## Functional Requirements

### FR-005: Behavioral Alignment and Stationarity
The system must align neural metrics (MMN amplitude) with behavioral accuracy metrics over time.
**Update (Plan Methodological Correction):** The alignment strategy is defined as "Lagged Alignment".
- Neural data (MMN) is calculated over a preceding 50-trial window (t-50 to t-10).
- This neural metric is aligned to the subsequent behavioral accuracy block (t to t+n).
- The system must verify stationarity of the behavioral trend (<10% drift) within the alignment block.
- If behavioral logs are missing, the system must fallback to "Stimulus-Driven" mode (P=0.8 probability) as per FR-012.

### FR-006: Statistical Modeling
The system must fit a statistical model to relate neural correlates to behavioral performance.
**Update (Plan Methodological Correction):** The model specification is changed from a generic LME to a **Gaussian Linear Mixed-Effects Model (Gaussian LME)**.
- Formula: `MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)`
- The model must support multiple-comparison correction (FDR) for electrode clusters.
- The model must include a permutation test (n=1000) to validate significance.
- **Exclusion:** Subjects with zero accuracy (singularity risk) must be excluded from the primary model fitting.

## User Stories

### User Story 2: MMN Amplitude and Behavioral Alignment
As a researcher, I want to compute MMN amplitudes and align them with behavioral accuracy using Lagged Alignment, so that I can observe the temporal relationship between prediction error signals and learning.

**Acceptance Criteria:**
1. MMN amplitude is calculated as the mean difference wave (-250ms to 250ms) at electrodes CP3, CP4, C3, C4.
2. **Lagged Alignment:** The system calculates MMN over a 50-trial lookback window (t-50 to t-10) and aligns it to the target behavioral block.
3. **Underpowered Subject Exclusion:** Subjects/conditions flagged as underpowered (e.g., <20 subjects in a cluster or insufficient trials) are explicitly excluded from the primary GLMM input data, as per Plan Phase 0.5.
4. The output `data/aligned_data.csv` must contain `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`, and `analysis_mode`.
5. Missing behavioral logs trigger the "Stimulus-Driven" fallback mode.

---
*Note: This specification has been amended to reflect Plan Methodological Corrections regarding Gaussian LME and Lagged Alignment.*
