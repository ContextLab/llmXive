# Feature Specification: Qwen‑VLA Cross‑Embodiment Transfer Study  

**Feature Branch**: `[feature‑branch]`  
**Created**: 2026‑06‑24  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Cross‑Embodiment Pre‑training & Zero‑Shot Evaluation (Priority: P1)

A robotics researcher wants to pre‑train a Vision‑Language‑Action (VLA) model on a mixed‑embodiment dataset and evaluate its zero‑shot success rate on robot platforms that were **not** seen during training.

**Why this priority**: Demonstrates the core hypothesis that embodiment diversity improves generalisation; without this step the research question cannot be answered.

**Independent Test**: Run the full pre‑training pipeline on the filtered Open X‑Embodiment subset, then evaluate on the LIBERO‑Spatial and LIBERO‑Object benchmarks for the held‑out platforms. The test passes if the evaluation script completes and produces success‑rate numbers for each seed.

**Acceptance Scenarios**:

1. **Given** a filtered dataset of ~50 k demonstrations spanning ≥3 robot platforms, **when** the model is trained with a frozen Qwen2‑VL‑2B vision encoder and a diffusion‑transformer action head on a CPU‑only runner, **then** training finishes within 6 h (if exceeded, a warning is logged but the job continues) and produces a checkpoint file ≤2 GB.
2. **Given** the trained checkpoint, **when** the model is run on the LIBERO‑Spatial benchmark for the held‑out platform, **then** a per‑seed success‑rate (percentage of successful task completions) is logged for all 5 random seeds.

### User Story 2 – Baseline Comparison & Statistical Significance (Priority: P2)

The researcher needs to compare the cross‑embodiment model against a single‑embodiment baseline and determine whether any performance gap is statistically reliable.

**Why this priority**: Provides the quantitative evidence required to answer the research question; significance testing guards against spurious claims.

**Independent Test**: Execute the baseline training (BridgeData‑only) and the cross‑embodiment training, then run the Wilcoxon signed-rank test on the collected success‑rate vectors. The test passes if the script outputs a p‑value and a decision (significant / not significant).

**Acceptance Scenarios**:

1. **Given** success‑rate vectors from the cross‑embodiment and baseline runs, **when** the Wilcoxon signed-rank test is applied, **then** the output reports a p‑value and indicates whether the improvement is statistically significant.
2. **Given** the statistical result, **when** the researcher inspects the generated report, **then** the absolute improvement in mean success‑rate is shown (e.g., +[deferred]).

### User Story 3 – Data‑Composition Ablation (Priority: P3)

The researcher wants to vary the proportion of cross‑embodiment data in the pre‑training corpus to quantify marginal transfer benefits.

**Why this priority**: Enables a finer‑grained understanding of how much embodiment diversity is needed, informing data‑collection strategies.

**Independent Test**: Run three additional training runs with 0.0, 0.5 and 1.0 cross‑embodiment data, evaluate each on the held‑out benchmarks, and plot success‑rate vs. proportion. The test passes if the ablation script completes and produces a CSV/plot with the three points and 95 % confidence intervals.

**Acceptance Scenarios**:

1. **Given** three pre‑training corpora (0.0, 0.5, 1.0 cross‑embodiment), **when** each model is trained and evaluated, **then** a table of mean success‑rates with 95 % confidence intervals is generated.
2. **Given** the table, **when** the researcher inspects the trend of performance, **then** the report clearly indicates the relationship between data proportion and performance.

---

### Edge Cases

- What happens if the Open X‑Embodiment dataset does not contain the required action token format for the diffusion‑transformer head?  
- How does the system behave when the training job exceeds the 7 GB RAM limit on the CI runner?  
- How is failure handled if the Wilcoxon signed-rank test cannot be performed because one of the seed runs crashes? 

## Requirements *(mandatory)*

### Functional Requirements

- **FR‑001**: System MUST ingest the Open X‑Embodiment dataset via the HuggingFace Datasets API and filter it to ~50 k demonstrations spanning ≥3 distinct robot platforms. *(See US‑1)*
- **FR‑002**: System MUST load the public Qwen2‑VL‑2B backbone weights (≈2 GB) in CPU‑only mode and keep the vision encoder frozen during training. *(See US‑1)*
- **FR‑003**: System MUST implement a diffusion‑transformer (DiT) action head that can be trained on the filtered dataset without exceeding 7 GB RAM (peak RSS measured via psutil) on the CI runner. *(See US‑1)*
- **FR‑004**: System MUST evaluate a trained checkpoint on the LIBERO‑Spatial and LIBERO‑Object benchmarks for the designated held‑out robot platforms, outputting per‑seed success‑rate, trajectory length, and variance. *(See US‑1)*
- **FR‑005**: System MUST compute Wilcoxon signed-rank tests with Holm‑Bonferroni correction between cross‑embodiment and single‑embodiment success‑rate vectors and output p‑values and significance decisions. *(See US‑2)*
- **FR‑006**: System MUST support configurable data‑composition ratios (e.g., 0.0, 0.5, 1.0) for ablation studies via a CLI argument `--ratio` accepting a float between 0.0 and 1.0, and automatically generate a CSV summarising mean success‑rate and 95 % confidence intervals for each ratio. *(See US‑3)*
- **FR‑007**: System MUST log all random‑seed values, hyper‑parameter settings, and software‑stack versions in a reproducibility manifest that can be rendered as a Markdown appendix by executing `render_manifest.py` which MUST exit with code 0 and produce `manifest.md`. *(See US‑1, US‑2, US‑3)*
- **FR‑008**: System MUST enforce a maximum wall‑time of 6 hours per CI job; if exceeded, the job MUST log a warning containing the string "TIMEOUT_WARNING" but MUST NOT abort. *(See US‑1)*

### Key Entities

- **DatasetSubset**: Represents the filtered Open X‑Embodiment demonstrations; attributes include `num_examples`, `platform_ids`, `normalized_action_tokens`.
- **ModelCheckpoint**: Serialized model weights after training; attributes include `size_mb`, `training_config`.
- **EvaluationResult**: Stores per‑seed metrics (`success_rate`, `trajectory_length`, `variance`).
- **StatisticalReport**: Contains Wilcoxon test results, corrected p-values, and confidence intervals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC‑001**: Cross‑embodiment model achieves an **absolute improvement value and 95% confidence interval** in mean zero‑shot success‑rate on held‑out platforms compared to the single‑embodiment baseline. *(See US‑2)*
- **SC‑002**: The Wilcoxon signed-rank test (Holm‑Bonferroni corrected) **reports the p-value and significance decision** for the improvement. *(See US‑2)*
- **SC‑003**: Ablation results **report the trend (slope) and statistical significance (p-value) of the relationship** between data proportion and performance, and each reported mean includes a **95 % confidence interval** computed from the 5 seeds. *(See US‑3)*
- **SC‑004**: All CI runs (training, evaluation, statistical analysis) complete and **report their wall-time and peak RAM usage (measured via psutil)**. *(See US‑1, US‑2)*
- **SC‑005**: The reproducibility manifest contains **exact versions** of Python, PyTorch, HuggingFace Datasets, and all other dependencies, and the manifest can be rendered **by executing `render_manifest.py` which MUST exit with code 0** and produce `manifest.md`. *(See US‑1, US‑2, US‑3)*

## Assumptions

- The CI environment provides **2 CPU cores**, **~7 GB RAM**, **~14 GB disk**, and **no GPU**.
- The Open X‑Embodiment subset selected (~50 k demos) **fits within the RAM limit** when loaded with lazy loading / streaming.
- The Qwen2‑VL‑2B weights are **compatible with CPU‑only inference** and do not require CUDA kernels.
- Action tokens in the dataset are **compatible with a diffusion‑transformer head**; if not, a simple token‑mapping will be applied (see clarification below).
- Random seeds are limited to **5 distinct values** (e.g., 0‑4) to balance variance estimation with compute budget.
- Statistical testing assumes **independent, non-normally distributed seed‑level success rates**; the Wilcoxon signed-rank test is used as the standard non-parametric approach for this data structure.

## Clarifications Needed

- **The Open X‑Embodiment dataset does not natively provide action tokens in the diffusion‑transformer format; the system MUST implement a preprocessing pipeline to normalize raw action vectors (e.g., joint positions/velocities) into the required token space. This is a standard requirement for cross‑embodiment transfer (see: Brohan et al., 2022, 'RT-1: Robotics Transformer for Real-World Control at Scale', arXiv:2212.06817).**
- **The upper bound on training examples is set to a large-scale collection of demonstrations. This limit is derived from the CI runner constraint of limited RAM, assuming a minimal batch size, a frozen vision encoder (significant memory overhead in CPU mode), and the diffusion transformer head. This aligns with the dataset subset size defined in FR‑001 and US‑1.**
- **The designated held‑out platforms for LIBERO evaluations are the Franka Emika Panda and the Universal Robots UR series. The evaluation on Franka serves as a 'within-embodiment generalization' test (same robot, different tasks), while the evaluation on UR serves as the true 'cross-embodiment' test (different robot). This distinction ensures a rigorous zero-shot generalization test while maintaining a valid baseline for task performance.**