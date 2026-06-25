# Feature Specification: The Impact of Visual Attention on False Memory Formation

**Feature Branch**: `feature-visual-attention-false-memory`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: “Does heightened visual attention to salient but irrelevant scene elements during encoding increase the likelihood of forming false memories for those elements during later recall? The study will use computational saliency estimates from a deep visual‑attention model applied to Visual Genome images and human recall transcripts from the Memory‑for‑Scenes / OpenNeuro dataset to test a correlational hypothesis (Pearson r > 0.3, p < 0.01).”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Compute Attention‑False‑Memory Relationship (Priority: P1)

_As a cognitive‑psychology researcher, I want to compute object‑level saliency scores and corresponding false‑memory rates so I can test whether greater visual attention predicts higher false‑memory incidence._

**Why this priority**: This story delivers the core scientific claim of the project; without it the investigation cannot proceed.

**Independent Test**: Run the end‑to‑end pipeline on a single image with its associated recall data and verify that a Pearson correlation coefficient and a mixed‑effects regression output are produced.

**Acceptance Scenarios**:

1. **Given** a downloaded Visual Genome image and its object annotations, **when** the saliency model generates a fixation map, **then** the system stores a numeric saliency score for each object.
2. **Given** participant recall transcripts for that image, **when** the false‑memory flag is coded, **then** the system computes a false‑memory rate for each object and produces a correlation (r, p) between saliency and false‑memory rate.

---

### User Story 2 – Validate Saliency Model (Priority: P2)

_As a researcher, I want to confirm that the computational saliency model approximates human eye‑fixation patterns on natural scenes, so the predictor is methodologically defensible._

**Why this priority**: Validating the saliency estimator ensures the independent variable truly reflects visual attention, addressing the “measurement validity” requirement.

**Independent Test**: Execute the model on the SALICON benchmark and check that the reported AUC meets the predefined threshold.

**Acceptance Scenarios**:

1. **Given** the SALICON test set, **when** the model predicts fixation maps, **then** the system computes an AUC ≥ 0.70 and records it in the results folder.

---

### User Story 3 – Assess Robustness of Findings (Priority: P3)

_As a researcher, I want to examine how analysis choices (e.g., percentile threshold for “salient” objects, alternative saliency models) affect the observed relationship, ensuring conclusions are not artefacts of arbitrary decisions._

**Why this priority**: Robustness checks protect against over‑fitting to a single analytical pipeline and satisfy the “threshold justification & sensitivity” methodological demand.

**Independent Test**: Run the pipeline with three different percentile thresholds (5 %, 10 %, 15 %) and with an alternative Vision‑Transformer CAM saliency map, then compare correlation signs and magnitudes.

**Acceptance Scenarios**:

1. **Given** the default pipeline, **when** the threshold is changed to 5 % or [deferred], **then** the system reports the new correlation values and confirms that the direction remains positive and its absolute change ≤ 0.05.
2. **Given** the alternative ViT‑B/16 CAM saliency maps, **when** the analysis is repeated, **then** the system reports a comparable correlation (within ±0.05 of the primary result).

---

### Edge Cases

- What happens when an image lacks object masks or the mask file is corrupted?
- How does the system handle a participant who provides no recall statements for a given image?
- What if the saliency model fails to produce a fixation map for an image (e.g., due to size incompatibility)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and cache Visual Genome images and their region/object annotations. (See US-1)
- **FR-002**: System MUST compute saliency maps for each image using the Deep Visual Attention Prediction model on CPU only. (See US-1)
- **FR-003**: System MUST validate the saliency model on the SALICON benchmark, achieving an AUC ≥ 0.70. (See US-2)
- **FR-004**: System MUST identify “salient but irrelevant” objects by selecting objects whose average saliency falls in the top **[deferred]** of all objects **and** are not mentioned in the ground‑truth scene description. (See US-1)
- **FR-005**: System MUST compute a binary false‑memory flag for each object from participant recall transcripts and aggregate a false‑memory rate per object. (See US-1)
- **FR-006**: System MUST calculate Pearson’s r, two‑tailed p‑value, and 95 % confidence interval for the relationship between object saliency and false‑memory rate. (See US-1)
- **FR-007**: System MUST fit a mixed‑effects logistic regression with random intercepts for participants and items, reporting coefficient estimates, standard errors, and p‑values. (See US-1)
- **FR-008**: System MUST apply Benjamini‑Hochberg FDR correction to any item‑wise significance tests. (See US-1)
- **FR-009**: System MUST perform a sensitivity analysis over percentile thresholds {low percentile (e.g., the lowest few percentiles), [deferred], [deferred]} and report how the correlation magnitude varies. (See US-1)
- **FR-010**: System MUST conduct an a‑priori power analysis targeting detection of **r = 0.30** with 80 % power (α = 0.01), reporting the required participant‑image sample size. (See US-1)

### Key Entities

- **Image**: Represents a single Visual Genome photograph; attributes include `image_id`, `url`, and associated object masks.
- **Object**: An annotated region within an Image; attributes include `object_id`, `category`, `mask`, `saliency_score`, `is_irrelevant`.
- **ParticipantRecall**: Transcript of a participant’s free recall for a given image; attributes include `participant_id`, `image_id`, `reported_objects`.
- **SaliencyModel**: The computational predictor; attributes include `model_name`, `weights_path`, `benchmark_auc`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pearson correlation **r** must be reported with a 95 % confidence interval and two‑tailed p‑value; a result of **r > 0.30** and **p < 0.01** will be interpreted as supporting the hypothesis. (See US-1)
- **SC-002**: Mixed‑effects logistic regression must converge; variance components for the random intercepts of participants and items must be statistically significant (**p < 0.05**). (See US-1)
- **SC-003**: Sensitivity analysis must show that the sign of the correlation remains positive across thresholds {5 %, 10 %, 15 %} and that the absolute change in **r** does not exceed **0.05**. (See US-3)
- **SC-004**: Saliency model benchmark performance on SALICON must be **AUC ≥ 0.70**. (See US-2)
- **SC-005**: Power analysis must indicate that the collected dataset meets or exceeds the required sample size for [deferred] power; if not, the shortfall must be documented. (See US-1)

## Assumptions

- The “Memory for Scenes” subset (or the OpenNeuro ds003166 “Free Recall” annotations) contains per‑image participant recall transcripts aligned with Visual Genome image IDs. **[NEEDS CLARIFICATION: does the chosen recall dataset provide object‑level false‑memory annotations for the Visual Genome images?]**
- Visual Genome provides accurate object masks for all images used; missing masks will be excluded without affecting overall power. **[NEEDS CLARIFICATION: are there images without masks that could reduce usable sample size?]**
- All computations will run on GitHub Actions free‑tier runners (≤2 CPU cores, ≤7 GB RAM, ≤6 h runtime); therefore, only CPU‑compatible libraries (e.g., PyTorch CPU, scikit‑learn) are employed.
- The saliency model’s pretrained weights are compatible with CPU inference and do not require GPU acceleration.
- The analysis is observational; results will be framed **associationally**, not as causal claims.  

---
