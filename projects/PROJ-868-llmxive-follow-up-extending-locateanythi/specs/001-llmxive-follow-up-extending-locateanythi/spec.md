# Feature Specification: llmXive follow-up: extending "LocateAnything: Fast and High-Quality Vision-Language Grounding with P"

**Feature Branch**: `001-llmxive-follow-up`  
**Created**: 2026-09-19  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'LocateAnything: Fast and High-Quality Vision-Language Grounding with P'"

## User Scenarios & Testing

### User Story 1 - Quantify Geometric Coherence Degradation under Attention Sparsity (Priority: P1) (US-1)

**User Journey**: A researcher configures a vision-language grounding model to run with restricted attention windows (simulating edge-device constraints) and executes an inference pass on a dataset of dense, cluttered scenes to measure the resulting drop in bounding box accuracy compared to global attention.

**Why this priority**: This is the core scientific objective. Without establishing the baseline relationship between attention sparsity and geometric coherence (mIoU), no further analysis of feature importance or tipping points is possible. It directly addresses the "What is NOT known" gap regarding the causal impact of attention sparsification.

**Independent Test**: The system can be tested by running a single inference job on a fixed subset of dense images with a specific sparsity mask (e.g., 32‑patch window) and comparing the output bounding boxes against ground truth to calculate mIoU. Success is defined by the ability to produce a valid mIoU score for the restricted configuration.

**Acceptance Scenarios**:
1. **Given** a pre‑loaded LocateAnything‑based model and a dense‑scene image subset (≥5 overlapping boxes per image), **When** the inference engine applies a local‑only attention mask (e.g., 32‑patch window), **Then** the system outputs the predicted bounding boxes, computes the mean Intersection‑over‑Union (mIoU) score, and records the numeric delta versus the global‑attention baseline.
2. **Given** the same dense‑scene subset, **When** the inference engine applies a global attention mask, **Then** the system outputs the predicted bounding boxes, computes the baseline mIoU, and records it for comparison.

### User Story 2 - Identify the "Tipping Point" for Ambiguity Resolution (Priority: P2) (US-2)

**User Journey**: A researcher iteratively adjusts the attention window size (from global down to local‑only) across a grid of sparsity levels to pinpoint the specific threshold where the model fails to maintain ≥ 80 % mIoU in dense scenes, thereby defining a hardware‑feasibility bound.

**Why this priority**: This refines the P1 finding into an actionable design constraint. It moves from "it gets worse" to "it gets worse at X," enabling the definition of minimum hardware requirements for specific accuracy targets.

**Independent Test**: The system is tested by executing inference runs across the defined grid of attention window sizes (Global, 64, 32, 16 patches, optional 1 patch) and producing per‑configuration mIoU scores. Success is defined by FR‑010: reporting the smallest window size whose dense‑scene mIoU first falls below 0.80, or reporting that no such tipping point exists.

**Acceptance Scenarios**:
1. **Given** a sequence of sparsity configurations (Global, 64, 32, 16, [optional 1] patches), **When** the system processes the dense‑scene subset, **Then** it generates a dataset of mIoU scores per configuration and reports the tipping point per FR‑010.
2. **Given** the calculated mIoU scores, **When** the system performs the optional ±8‑patch sensitivity sweep around the identified tipping point (if any), **Then** it reports the additional mIoU values per FR‑011.

### User Story 3 - Attribute Failure Modes to Structural Visual Features (Priority: P3) (US-3)

**User Journey**: A researcher uses gradient‑based attribution methods (e.g., Grad‑CAM or attention rollout) on the model's failure cases (from P2) to determine which visual features (texture, edges, global tokens) the model relied on, and how this reliance shifts as global context is removed.

**Why this priority**: This explains *why* the degradation occurs (P2), fulfilling the research question's second part about "specific structural features." It provides the theoretical basis for future architectural improvements.

**Independent Test**: The system is tested by selecting images where dense‑scene predictions fail under local attention but succeed under global attention, running an attribution algorithm, and computing the proportion of activation mass on tokens labelled “global‑context”. Success is defined by FR‑005 and SC‑004: generating attribution maps and reporting that the absolute difference in global‑context activation proportion between success and failure groups is **≥ 30 %** (as required by SC‑004).

**Acceptance Scenarios**:
1. **Given** sets of “failure” images (dense, local‑attention mIoU < 0.80) and “success” images (dense, global‑attention mIoU ≥ 0.80), **When** the system applies Grad‑CAM or attention rollout on the full (unmasked) model, **Then** it produces heatmaps for both groups and reports that the absolute difference in global‑context activation proportion between the success and failure groups is **≥ 30 %** (as quantified in SC‑004).

### Edge Cases

- **Low‑density images** (≤ 5 overlapping bounding‑box pairs per image): The system must still compute mIoU for these images (FR‑003) but must **not** compute the ambiguity‑resolution failure metric; SC‑007 requires reporting “N/A” for this metric on low‑density samples.
- **Ambiguous or poorly annotated ground‑truth boxes**: Any ground‑truth box with zero area or with IoU > 0.95 to another box is considered ambiguous. FR‑007 mandates that such samples be flagged and excluded from all mIoU calculations. SC‑006 requires reporting the proportion of excluded samples (must be ≤ 5 % of the dataset).
- **Window size = 1 patch**: This is an optional supplementary run. FR‑009 requires the system to execute it if requested, record the resulting mIoU as the lower bound of the degradation curve, and include it in SC‑001 if executed.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST implement a parameterized “sparsity knob” that dynamically restricts the attention window size (ranging from global to local‑only) and masks global context tokens during inference. The supported grid is **Global**, **64**, **32**, **16** patches, with an **optional 1‑patch** run for lower‑bound analysis. (See US‑1)
- **FR-002**: The system MUST calculate the mean Intersection‑over‑Union (mIoU) for predicted bounding boxes against ground‑truth annotations for every inference run across all sparsity levels. (See US‑1, US‑2)
- **FR-003**: The system MUST filter the input dataset to create a **dense‑scene subset** defined as images containing **> 5 overlapping bounding‑box pairs** (pairwise IoU > 0.10). It MUST also define a **non‑dense subset** as all remaining images (≤ 5 overlapping pairs). (See US‑2)
- **FR-004**: The system MUST execute a **two‑way mixed ANOVA** (within‑subject factor: sparsity level; between‑subject factor: scene density) to assess the interaction effect on mIoU. If normality assumptions are violated, it MUST fall back to a **Friedman aligned‑rank test**. The analysis MUST report the p‑value. (See US‑2, SC‑002)
- **FR-005**: The system MUST implement gradient‑based attribution (e.g., Grad‑CAM or attention rollout) **on the full, unmasked model** to generate visual heatmaps of feature importance for selected failure cases. (See US‑3)
- **FR-006**: The system MUST enforce a CPU‑only execution mode with `torch.set_num_threads(2)` and memory‑mapped loading to ensure compatibility with the 2‑core/Limited RAM constraint. (See US‑1)
- **FR-007**: The system MUST flag and exclude images whose ground‑truth boxes are **ambiguous** (zero‑area or IoU > 0.95 with another box) from all mIoU calculations. (See US‑1)
- **FR-008**: For **low‑density images** (≤ 5 overlapping pairs), the system MUST still compute mIoU but MUST NOT compute or report the ambiguity‑resolution failure metric; SC‑007 requires reporting this as “N/A”. (See US‑1)
- **FR-009**: When the sparsity knob is set to **1 patch**, the system MUST optionally execute this run, record the resulting mIoU, and treat it as the lower bound of the degradation curve. (See US‑1)
- **FR-010**: The system MUST identify the **tipping point** as the smallest sparsity window size for which the dense‑scene subset mIoU first drops **below 0.80**. If no such window exists within the grid, the system MUST report “no tipping point reached”. (See SC‑001)
- **FR-011**: If a numeric tipping point is identified by FR‑010 and the tipping point window size is greater than 1 patch, the system MUST perform a **±8‑patch sensitivity sweep** (clamped to the valid range 1‑64) around that window size and report the additional mIoU values. If no tipping point exists or the tipping point is the global configuration, the sweep is omitted and a note is recorded. (See SC‑001)
- **FR-012**: The system MUST randomize the order of sparsity‑configuration inference runs (using a fixed random seed logged for reproducibility) to eliminate systematic warm‑up or caching effects. (See US‑1)
- **FR-013**: The sparsity‑knob API shall be defined as `SparsityConfig(num_patches, window_size=None)` where the constructor accepts `num_patches` and an optional `window_size`. It shall provide a method `get_mask()` (no arguments) that returns the appropriate attention mask. (See US‑1)
- **FR-014**: After generating per‑window inference files (`inference_<window>.parquet`), the system MUST consolidate them into a master table `data/results/master_inference.parquet` for all downstream analysis, satisfying the Single Source of Truth principle. (See US‑1)

### Key Entities

- **Sparsity Configuration**: An object defining the attention window size (e.g., 32 patches) and the specific mask pattern applied to the transformer layers.
- **Dense Scene Sample**: An image containing **> 5 overlapping bounding boxes** (pairwise IoU > 0.10); used to test geometric ambiguity resolution.
- **Non‑dense Sample**: Any image not meeting the dense‑scene definition (i.e., ≤ 5 overlapping pairs), including low‑density cases.
- **Attribution Map**: A visual representation of the model’s internal attention weights or gradients, highlighting which image regions influenced the prediction.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The degradation curve of dense‑scene mIoU across the sparsity grid (including optional 1‑patch) must be measured; the **tipping point** is defined as the first window size where mIoU < 0.80 (per FR‑010). The reported tipping point (or “no tipping point”) satisfies the requirement. (See US‑1, US‑2)
- **SC-002**: The p‑value from the two‑way mixed ANOVA (or its non‑parametric fallback) for the interaction between sparsity and scene density must be reported. (See FR‑004)
- **SC-003**: The relationship between ordered sparsity levels and mIoU shall be assessed using an ordered‑factor trend test (Jonckheere‑Terpstra) or a mixed‑effects regression that respects the categorical nature of the predictor. The test statistic and associated p‑value must be reported. (See US‑2)
- **SC-004**: For the attribution analysis, the system must compute the **global‑context activation proportion** for both failure and success groups and report that the **absolute difference** between the two groups is **≥ 30 %**. (See FR‑005)
- **SC-005**: The total inference latency per image must be measured and the overall batch run must complete within **6 hours** on the specified Multi‑core CPU. (See US‑1)
- **SC-006**: The number of images excluded due to ambiguous ground‑truth (FR‑007) must be reported and must not exceed **5 %** of the total dataset. (See Edge Cases)
- **SC-007**: For low‑density images, the ambiguity‑resolution failure metric must be reported as **“N/A”**, and this reporting must be verified. (See Edge Cases)
- **SC-008**: The randomization seed used for ordering sparsity runs must be logged, and a checksum confirming that the master inference table includes data from all sparsity levels must be provided. (See FR‑012, FR‑014)

## Assumptions

- **Dataset Variable Fit**: It is assumed that the VRSBench validation split and the curated COCO/RefCOCO+ subset contain sufficient ground‑truth bounding‑box annotations to accurately calculate mIoU for overlapping objects. RefCOCO+ does not provide explicit “overlapping object” annotations; overlap status is programmatically derived from the spatial intersection of existing ground‑truth boxes (IoU > 0.10). The dense‑scene subset is therefore constructed by computing pairwise ground‑truth box IoU per image and retaining images with **> 5** boxes whose pairwise IoU exceeds 0.10, consistent with FR‑003 and Constitution Principle VI.
- **Inference Framing**: The study is observational; findings regarding the “impact” of attention sparsity are framed as associational relationships between configuration and performance, not causal claims about architectural superiority, due to the lack of random assignment in the dataset generation.
- **Threshold Justification**: The grid of sparsity levels (Global, 64, 32, 16, optional 1) is selected based on common efficient‑attention window sizes in the literature (e.g., Swin‑Transformer, ViT‑S). The 0.80 mIoU tipping‑point threshold follows Constitution Principle VI and reflects a pragmatic trade‑off between accuracy and resource constraints.
- **Compute Feasibility**: The analysis assumes that the selected model architecture (LocateAnything variant) can be run in default precision (FP32) on a 2‑core CPU without requiring 8‑bit quantization or GPU acceleration. If memory pressure exceeds 7 GB, the dataset will be sampled to fit.
- **Measurement Validity**: The mIoU metric is assumed to be a valid proxy for “geometric coherence” in this context, as it directly measures the spatial alignment of predicted boxes against ground truth.
- **Predictor Collinearity**: Since “attention window size” and “global context tokens” are definitionally linked (reducing the window reduces global tokens), the analysis treats them as a single joint predictor rather than claiming independent effects for each.
