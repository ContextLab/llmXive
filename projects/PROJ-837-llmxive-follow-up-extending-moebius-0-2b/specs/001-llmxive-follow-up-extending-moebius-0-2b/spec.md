# Specification: Moebius-Dynamic Extension

## 1. Introduction
This document defines the requirements for extending the Moebius 0.2B model with a dynamic rank adjustment mechanism. The goal is to reduce inference latency on CPU by adapting the model's computational rank based on the complexity of the masked region.

## 2. User Stories

### US1: Data Preparation and Human Complexity Annotation
**As a** researcher, **I want** to ingest the Places2 dataset and generate ground-truth complexity labels (either via crowdsourcing or a decoupled synthetic proxy) **so that** I can train a gating mechanism without circularity.
- **Acceptance Criteria**:
 - Places365 subset is fetched via HuggingFace `datasets`.
 - Masks are generated with recorded gradient variance and texture entropy.
 - **CI Mode**: Scores are generated via uniform random distribution (1-5), strictly independent of mask metrics.
 - **Research Mode**: Scores are loaded from external human-annotated CSV.
 - Inter-rater reliability (Krippendorff's alpha) is calculated for Research Mode.

### US4: Synthetic Proxy Validation
**As a** developer, **I want** to validate that synthetic mask metrics correlate with ground truth **so that** I can trust the proxy before training.
- **Acceptance Criteria**:
 - Pearson correlation $r$ is computed between synthetic metrics and ground truth.
 - **Research Mode**: If $r < 0.7$, the process blocks (`gate_status: BLOCKED`).
 - **CI Mode**: Low correlation is expected and logged (`gate_status: EXPECTED_LOW_CORRELATION`).

### US2: Dynamic Rank Adjustment Mechanism
**As a** system, **I want** to adjust the rank of $L\lambda MI$ matrices dynamically based on a gating head prediction **so that** I save compute on simple regions.
- **Acceptance Criteria**:
 - Gating head is $\le 5M$ parameters.
 - Output is a scalar complexity score mapped to rank indices (1-5).
 - Fallback to static high-rank if mask coverage > 50%.

### US3: Efficiency and Fidelity Evaluation
**As a** stakeholder, **I want** to benchmark the dynamic model against a static baseline **so that** I can verify efficiency gains without quality loss.
- **Acceptance Criteria**:
 - Latency reduction $\ge 30\%$ for low-complexity regions.
 - FID difference $\le 0.5$ vs static baseline.
 - Power analysis confirms statistical significance ($p > 0.05$).

## 3. Technical Constraints
- **CPU-Only**: All training and inference must run on CPU.
- **Memory**: Processing must fit within 7GB RAM.
- **Data Integrity**: No synthetic input data. Real datasets only.
- **Auditability**: CI vs Research mode must be clearly logged.

## 4. Success Metrics
- **Efficiency**: 30% latency reduction on low-complexity masks.
- **Quality**: FID delta $\le 0.5$.
- **Robustness**: Gating head parameter count $\le 5M$.
