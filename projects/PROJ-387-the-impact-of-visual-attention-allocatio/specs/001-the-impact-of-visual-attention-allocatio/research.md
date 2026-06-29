# Research: 001-visual-attention-recall

## Dataset Strategy

**Status**: ⚠️ **CRITICAL BLOCKER** — No Verified Source Found

Per the Verified datasets block in the project context, **no eye-tracking dataset containing fixation duration, saccade amplitude, gaze distribution, recall accuracy, and valence labels exists in the verified list.**

| Required Variable | Status in Verified Datasets |
|-------------------|-----------------------------|
| Fixation Duration | **Missing** (No verified source) |
| Saccade Amplitude | **Missing** (No verified source) |
| Gaze Distribution | **Missing** (No verified source) |
| Recall Accuracy | **Missing** (No verified source) |
| Valence Label | **Missing** (No verified source) |
| FR-002 Data Source | **NO verified source found** |

**Available Datasets (Not Applicable)**:
- `us_100K_difficult/tx_log.csv`: Transaction logs (US-1). Does not contain eye-tracking or recall metrics.
- `qwen3.5-toolcalling-v2`: Tool-calling traces. Not eye-tracking.
- `erp-and-erotica`: Text roleplays. No eye-tracking.
- `UIT-ViIC`: Vietnamese annotations. No eye-tracking.

**Decision/Rationale**:
The pipeline is designed to ingest and validate data per US-1. However, since no verified source contains the required variables, **FR-002 validation will fail**, and the pipeline will halt before analysis. The implementation will proceed to build the ingestion and validation logic to demonstrate compliance with US-1 (flagging incompatibility), but statistical analysis (FR-003) cannot be executed without external data acquisition that bypasses the `Verified datasets` constraint.

**Fallback Procedure**:
1. If metadata is unavailable, NLP sentiment scoring (VADER/TextBlob) was assumed in spec assumptions. However, `Verified datasets` lists `NLP: NO verified source found` and `VADER: NO verified source found`.
2. Consequently, **no valence annotation strategy is viable** under current constraints.
3. The `research_complete` stage cannot be reached until a verified eye-tracking dataset is added to the `Verified datasets` block.

## Statistical Rigor

**Method**: Linear Mixed-Effects Models (LMM) via `statsmodels`.
**Rationale**: LMM handles hierarchical data (participants × passages) and is CPU-tractable.

### LMM Random Effects Structure (Explicit Specification)

**Fixed Effects**:
- Attention metric (fixation_duration_ms, saccade_amplitude_deg, gaze_distribution_density) × valence_category interaction
- Primary predictor: attention metric
- Moderator: valence_category (positive, negative, neutral)

**Random Effects**:
- **Random intercepts for participant_id**: Accounts for individual baseline differences in recall performance
- **Random intercepts for passage_id**: Accounts for passage-specific difficulty effects
- **Random slopes for attention metric by participant_id**: Accounts for individual differences in attention-recall relationships
- **Convergence Fallback**: If full random slopes model fails to converge, fall back to random intercepts only (document in output report)

**Full Model Formula**:
```
recall_accuracy ~ attention_metric * valence_category + (1 | participant_id) + (1 | passage_id) + (attention_metric | participant_id)
```

**Implementation**: `statsmodels.regression.mixed_linear_model.MixedLM` with REML estimation.

### Multiple-Comparison Correction

- **Method**: Bonferroni correction.
- **Scope**: 9 tests minimum (3 attention metrics × 3 valence categories).
- **Compliance**: FR-004, SC-003.
- **Implementation**: `multipletests` from `statsmodels.stats.multitest`.

### Causal Inference

- **Nature**: Observational (no random assignment of attention).
- **Framing**: All results explicitly labeled "associational" (FR-005).
- **Assumptions**: No causal claims. Confounding variables (e.g., reading skill) not controlled unless present in dataset (unlikely per data gap).

### Measurement Validity

- **Instruments**: Recall measures must document validation evidence (see Recall Measure Validity section below).
- **Eye-Tracking**: Calibration required (Constitution VI). Track loss ≤5% (US-1).

## Power Analysis

**Status**: `[deferred]` — Dependent on dataset availability.

**Minimum Sample Requirements** (for LMM with 9 hypothesis tests):
- **Participants**: ≥30 (minimum for stable random intercepts)
- **Trials per Participant**: ≥5 passages per valence category
- **Total Observations**: ≥450 (30 participants × 15 passages)
- **Effect Size Detection**: Medium effect (Cohen's f² = 0.15) with α = 0.05, power = 0.80

**Power Limitation Acknowledgement**:
If available dataset has fewer participants or trials, power for interaction effects (valence × attention) will be reduced. This will be explicitly documented in the output report.

## Confounding Variables

**Identified Confounds** (cannot be controlled unless present in dataset):
1. **Reading Skill**: Individual differences in reading proficiency may affect both attention patterns and recall accuracy.
2. **Text Difficulty**: Passage complexity may confound attention-recall relationships.
3. **Prior Knowledge**: Topic familiarity may influence both attention allocation and recall performance.
4. **Fatigue Effects**: Order effects across multiple passages may bias results.

**Mitigation Strategy**:
- Document confounds in output report as limitations.
- If dataset includes covariates (e.g., reading comprehension scores), add as fixed effects.
- Otherwise, acknowledge as uncontrolled confounds in associational framing (FR-005).

## Valence Annotation Strategy

**Preferred Method**: Human-rated metadata using standardized affective norms (e.g., 9-point Likert scale per Constitution VII).

**⚠️ NLP Fallback (NOT VIABLE FOR PRIMARY ANALYSIS)**:
- If NLP sentiment scoring (VADER/TextBlob) is used to derive valence labels, the emotional categorization is **not independent of the stimulus text itself**.
- **Circularity Risk**: Attention patterns are measured on the same text content that NLP analyzes for valence. This creates confounding between attention patterns and valence labels derived from the same content.
- **Consequence**: NLP-derived valence cannot support primary hypothesis testing; any observed attention-valence relationships may reflect text properties rather than true emotional effects.
- **Mitigation**: NLP-derived valence must be treated as a **separate validation study only** (not primary analysis). Document validation agreement (Cohen's κ) between NLP and human ratings. If human ratings unavailable, **block research_complete**.

**Current Status**: No verified source for either human-rated metadata or NLP tools. **Blocker for research_complete.**

## Recall Measure Validity

**Primary Outcome**: `free_recall_accuracy` (0.0 to 1.0)
- **Rationale**: Free recall is the standard measure for narrative memory in eye-tracking studies.
- **Validity Requirements**: Dataset must document instrument validation evidence (e.g., inter-rater reliability ≥0.80, test-retest stability ≥0.70).

**Secondary Outcome**: `recognition_score` (0.0 to 1.0)
- **Rationale**: Recognition provides convergent validity for memory assessment.
- **Validity Requirements**: Same as primary outcome; if unavailable, document as "unverified secondary measure".

**Validity Verification Protocol**:
1. Check dataset metadata for validation evidence (inter-rater reliability, test-retest stability, internal consistency).
2. If validation evidence present: Document citation and reliability coefficients in output report.
3. If validation evidence absent: Flag in output report as "unverified recall measure" and exclude from primary analysis conclusions.
4. Constitution VII requires standardized rating scale for valence; recall measures should similarly follow validated protocols.

**Assumption Note**: Spec assumes "All recall measures used in the source datasets are validated instruments" — this must be verified against actual dataset documentation before research_complete.

## Compute Feasibility

**Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 6h).
**Strategy**:
- **Data**: Sample to fit RAM if >7 GB. Use `dtype` optimization (float32).
- **Libraries**: `pandas` (data), `statsmodels` (LMM), `scipy` (stats), `seaborn` (plots). All CPU wheels available.
- **No GPU**: No CUDA, no `load_in_8bit`, no `device_map="cuda"`.
- **Runtime**: LMM on sampled data (<10k rows) typically <30 mins. Sensitivity sweep adds <10 mins. Total <1h.
- **Memory**: 7 GB limit respected by avoiding full dataset load if >1 GB.

## Sensitivity Analysis

**Parameter**: Significance threshold (α).
**Sweep**: {0.01, 0.05, 0.1}.
**Output**: Rate of significant findings at each threshold (FR-006).
**Implementation**: Loop over thresholds, re-run correction, log counts.

**Additional Sensitivity**: If NLP valence used (against recommendation), sweep sentiment cutoff scores and report agreement with human-rated valence (if available). **Note**: This is a validation study only, not primary analysis.