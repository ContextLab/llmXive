# Research: The Impact of Perspective-Taking on Moral Outrage in Online Discourse

## 1. Research Question & Hypothesis

**Research Question**: Does prompting individuals to adopt the perspective of a disagreeing online poster reduce their self-reported moral outrage toward the post?

**Hypothesis**: Participants in the **Perspective-Taking** condition will report significantly lower mean moral outrage scores compared to participants in the **Control Summarization** condition.

**Operationalization**:
- **Independent Variable**: Instruction Type (Perspective-Taking vs. Control Summarization).
- **Dependent Variable**: Mean score on the 7-item Moral Outrage Scale (1-7 Likert).
- **Effect Size Target**: Cohen's d ≥ 0.2 (Small to Medium).

## 2. Dataset Strategy

### Verified Datasets
The following dataset is the primary source for stimulus curation. **CRITICAL**: The pipeline is currently BLOCKED until a verified URL is provided.

| Dataset Name | Source Type | URL / Loader | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Against the Others!** | ArXiv / GitHub | **BLOCKED: Must be provided in config.py** | **BLOCKED** | Contains annotated Twitter posts with outrage labels and topics. |

> **Critical Note on Dataset Fit**: The spec requires "high-outrage" posts on specific topics (climate, immigration). The `ingest.py` script MUST verify that the dataset actually contains these specific topic labels and the `outrage_label` field. If the dataset lacks these fields or values, the plan **cannot** proceed. The system will halt and flag this mismatch.

*Self-Correction for Implementation*: Since the user message did not provide a specific "Verified datasets" block in the prompt text, the implementation must rely on a URL provided in `config.py`. If no URL is provided, the pipeline halts. If a URL is provided, the `ingest.py` script must verify the schema.

### Data Preprocessing Plan
1. **Ingestion**: Download raw JSON/CSV.
2. **Schema Verification**: Check for required fields (`outrage_label`, `topic`) and values (`high`, `climate`, `immigration`). If missing, raise `DataInsufficientError`.
3. **Filtering**: Keep only `outrage_level == "high"`.
4. **Topic Selection**: Filter for `topic == "climate"` or `topic == "immigration"`.
5. **Sampling**: Randomly select 20 posts per topic (Total n=40).
6. **Sanitization**: Remove any PII (user handles, IDs) before storing in `data/processed/stimuli.json`.

## 3. Methodology & Statistical Design

### Experimental Design
- **Type**: Between-subjects experiment (simulated).
- **Conditions**:
  1. **Perspective-Taking**: "Read the post, then write a short paragraph describing the situation from the poster's point of view. Why might they feel this way?"
  2. **Control**: "Read the post, then write a short paragraph summarizing the main argument."
- **Participants**: 200 synthetic participants (for pipeline validation).
- **Randomization**: Simple random assignment to conditions (1:1 ratio).

### Statistical Analysis Plan
1. **Primary Analysis**:
   - **Test**: Linear Mixed-Effects Model (LMM).
   - **Fixed Effects**: `Condition`, `Topic`, `Condition:Topic` interaction.
   - **Random Effects**: `(1 | Stimulus)`, `(1 | Participant)`.
   - **Rationale**: Accounts for the nested design (multiple responses per stimulus) to prevent pseudoreplication. The model estimates the effect of condition while controlling for stimulus variability.
   - **Assumption**: The 7-point Likert scale is treated as interval data, a standard approximation in psychometrics for scales with ≥5 points.
   - **Output**: Fixed effect coefficients, p-values, 95% Confidence Interval.

2. **Sensitivity Analysis (Ordinal Robustness)**:
   - **Test**: Mann-Whitney U test (per condition, per topic).
   - **Purpose**: Verify results if the interval assumption is violated. This is a primary sensitivity analysis, not just a robustness check.

3. **Power Analysis**:
   - **Tool**: `statsmodels.stats.power.tt_ind_solve_power`.
   - **Parameters**: α = 0.05, Power = 0.80, Effect Size (d) = 0.4 (medium).
   - **Output**: Required sample size for the human experiment (FR-010).

### Multiple Comparison & Family-Wise Error
- **Correction**: The primary analysis includes the `Condition:Topic` interaction term. If this interaction is significant, post-hoc tests will be conducted with Bonferroni correction. If the interaction is non-significant, the main effect of Condition is interpreted.
- **Decision**: The plan explicitly models the interaction to avoid masking heterogeneous effects.

### Causal Inference & Validity
- **Causal Claim**: The study design (randomized instruction) supports causal claims about the *effect of the instruction* on outrage scores.
- **Limitation**: The *stimuli* (posts) are observational. We cannot claim the intervention changes outrage toward the *topic* in the real world, only toward the *specific stimulus* in the experiment.
- **Measurement Validity**: The Moral Outrage Scale is a validated instrument (Smith et al.). The plan assumes the scale's psychometric properties hold in this synthetic context.

## 4. Compute Feasibility & Constraints

- **Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Libraries**: `pandas`, `numpy`, `scipy`, `statsmodels`. All are CPU-optimized and lightweight.
- **Runtime**: Estimated < 10 minutes for 200 participants and 40 stimuli.
- **Memory**: Dataset is text-only; < 10MB total footprint.
- **No GPU**: No deep learning models are used. Statistical tests are analytical.

## 5. Decision Log & Rationale

| Decision | Rationale |
| :--- | :--- |
| **Use LMM instead of t-test** | The design has 40 stimuli (n=40 for the IV), not 200. A t-test on participant means ignores the nested structure and inflates Type I error (pseudoreplication). LMM correctly models stimulus as a random factor. |
| **Generative Simulation (H0/H1)** | Generating data with a fixed mean shift creates circular validation. The new approach tests the pipeline's ability to detect a null effect (Type I error) and a known effect (Power) using empirically grounded noise. |
| **Include Interaction Term** | The effect of perspective-taking may differ by topic (e.g., climate vs. immigration). Aggregating without testing for interaction risks masking or spurious results. |
| **Mann-Whitney U as Sensitivity** | Likert data is ordinal. While LMM assumes interval scaling (standard for 7-point scales), the Mann-Whitney U provides a primary check for ordinal consistency. |
| **Strict Topic Filtering** | The hypothesis is specific to "high-outrage" posts. Including low-outrage posts would dilute the effect and violate the experimental design. |
| **Power Analysis Before Recruitment** | To avoid underpowered studies (Type II errors), the required sample size is calculated formally (FR-010) before human recruitment begins. |

## 6. Ethical Considerations

- **Synthetic Data**: No ethical concerns for simulation.
- **Human Data (Future)**:
  - **Informed Consent**: Participants must be informed that they are viewing controversial content and that their emotional responses are being measured.
  - **Debriefing**: Participants must be debriefed after the study, explaining the purpose and providing resources if the content caused distress.
  - **Privacy**: No PII will be stored. Data will be anonymized.