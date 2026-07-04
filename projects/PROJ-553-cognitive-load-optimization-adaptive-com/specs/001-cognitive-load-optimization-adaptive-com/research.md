# Research: Cognitive Load Optimization: Adaptive Complexity Scaling for Personalized Learning

## 1. Problem Statement & Hypothesis

**Research Question**: How does dynamically adjusting explanation complexity based on multimodal cognitive load signals affect learning efficiency compared to static complexity levels in AI tutoring systems?

**Hypothesis**: Adaptive complexity selection (matching explanation difficulty to inferred cognitive load) yields higher estimated learning efficiency (engagement time × potential gain / total time) than static complexity baselines.

**Key Constraint**: The system must operate without self-reported cognitive load data *unless* the dataset contains concurrent interaction features AND self-reports. **Crucially, the system MUST NOT rely on heuristic proxies** (e.g., "high error = high load") for validation, as this creates a circular logic that invalidates the research.

## 2. Dataset Strategy

The plan relies on the following verified datasets. No other sources are used.

| Dataset | Source URL | Role in Plan | Validation Check |
|:--- |:--- |:--- |:--- |
| **ASSISTments** | ` (and related) | Primary source for interaction features (response latency, error logs, hint requests, timestamps). | Verify presence of `response_time`, `is_correct`, `hint_count`, `timestamp` columns. **Must also check for `nasa_tlx` or similar self-report columns.** |
| **OULAD** | ` | Secondary source for interaction patterns. | Verify JSON structure contains session logs with interaction events. **Must also check for concurrent self-reports.** |

**Golden Set Strategy**:
Public datasets (ASSISTments, OULAD) **do not** typically contain expert-labeled cognitive load scores or concurrent self-reports (NASA-TLX) for the specific interaction events required.
- **Method**: The implementation **MUST** load a "Golden Set" of ≥50 interactions manually labeled by domain experts (or a dataset subset with verified concurrent NASA-TLX ratings).
- **Blocking Condition**: If the `data/processed/golden_set.csv` file is missing or lacks the `expert_load_score` column, **AND** if the public datasets lack concurrent self-reports, the system MUST halt execution with the error: `Validation Data Missing: Golden Set or required interaction features with concurrent self-reports not found. Cannot proceed with model training.`
- **No Synthetic Proxies**: The plan explicitly **rejects** the generation of synthetic labels via heuristics (e.g., "high error + long latency = High Load"). Such a proxy would make the validation target definitionally dependent on the predictors, rendering the correlation metric ($r \ge 0.6$) a tautology rather than an empirical result.

## 3. Methodological Approach

### Phase 0: Data Availability Check (NEW)
- **Action**: Scan `data/processed/` for `golden_set.csv` with `expert_load_score`.
- **Action**: Scan public datasets for `nasa_tlx` or equivalent self-report columns concurrent with interaction events.
- **Outcome**: If neither is found, **HALT**. Do not proceed to Phase 1.

### Phase 1: Cognitive Load Estimation (US-1)
- **Model**: Gradient Boosting Regressor (`LightGBM` or `XGBoost` with `tree_method='hist'` for CPU efficiency).
- **Features**: Response latency (log-transformed), error frequency (count per session), hint usage (count), pause duration.
- **Validation**: Pearson correlation ($r$) between predicted load and **External** Golden Set labels (or concurrent NASA-TLX). Target: $r$ indicates a strong positive correlation.
- **Collinearity Check**: Compute Variance Inflation Factor (VIF). If VIF > 5 for any predictor, report descriptive relationship only; do not claim independent effects.
- **Success Criterion**: Validation passes only if $r \ge 0.6$ against **external** ground truth.

### Phase 2: Complexity Tier Generation (US-2)
- **Input**: Sample instructional units (e.g., from ASSISTments "skill" descriptions or synthetic pedagogical text).
- **Process**:
 1. **Simple**: Reduce sentence length, remove jargon, simplify syntax.
 2. **Moderate**: Standard academic text.
 3. **Complex**: High jargon density, nested clauses.
- **Metrics**: Flesch-Kincaid Grade Level.
- **Constraint**: Adjacent tiers must differ by a substantial margin.
- **Fidelity**: Jaccard similarity of key terms $\ge$ high threshold; semantic similarity $\ge 0.90$.

### Phase 3: Adaptive vs Static Simulation (US-3)
- **Design**: Within-subject simulation. Replay a sufficient number of historical sessions.
- **Conditions**:
 1. **Static**: Always serve "Moderate" complexity.
 2. **Adaptive**: Select tier based on Load Estimate + Hysteresis Controller.
- **Hysteresis**: Thresholds swept at $\{0.01, 0.05, 0.1\}$. Report inconsistency rates.
- **Outcome Metric**: Learning Efficiency = $(\text{Predicted Engagement} \times \text{Gain}) / \text{Total Time}$.
- **Statistical Test**: Linear Mixed-Effects Model (LMM).
 - Fixed Effects: Condition, Estimated Load, Condition × Load.
 - Random Effects: Session ID (intercept).
 - Output: Cohen's $d$, confidence interval, $p$-value.
- **Corrections**: Family-wise error correction (e.g., Bonferroni) if multiple hypotheses tested.
- **Validity**: The "Potential Gain" metric is now grounded in the externally validated load model, not a heuristic artifact.

## 4. Statistical Rigor & Limitations

- **Multiple Comparisons**: If testing multiple thresholds or load bins, apply Bonferroni correction.
- **Power Analysis**: If $N < 40$ sessions are available in the dataset, the system will halt or flag a "Power Limitation" warning and defer effect-size claims.
- **Causal Claims**: **NONE**. All findings are framed as associational (FR-006). The simulation replays historical data; no random assignment occurred.
- **Measurement Validity**: Flesch-Kincaid is a proxy for complexity. The plan acknowledges this limitation.
- **Collinearity**: If "error frequency" and "hint usage" are highly correlated (definitionally related), the model will report VIF and avoid claiming independent predictive power for both.
- **External Validity**: The study's validity is entirely dependent on the quality of the external Golden Set. If the Golden Set is missing, the study cannot proceed.

## 5. Compute Feasibility

- **Hardware**: 2 CPU cores, 7 GB RAM.
- **Strategy**:
 - Data subset to a manageable size.
 - Model: `LightGBM` (CPU-only, efficient).
 - Text processing: `textstat` (CPU lightweight).
 - Simulation: Vectorized pandas operations.
 - No GPU, no deep learning.
- **Time Limit**: All steps designed to complete in < 2 hours (well within 6h limit) **IF** data is present.