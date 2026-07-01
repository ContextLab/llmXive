# Specification: The Impact of Visual Attention on False Memory Formation

## Overview
This specification defines the requirements for a study examining the relationship between visual attention (saliency) and false memory formation.

## User Stories

### US1: Compute Attention-False-Memory Relationship
**As a researcher**, I want to compute the correlation between object saliency and false memory rates so that I can test the hypothesis that attention increases false memory.

**Acceptance Criteria**:
- Saliency scores are computed for all objects in the linked dataset.
- False memory candidates are filtered based on transcript presence and VG absence.
- Human consensus verification is performed on false memory candidates.
- Pearson correlation and mixed-effects regression are calculated.
- FDR correction is applied to multiple comparisons.
- Output is written to `data/processed/correlation_results.json`.

### US2: Validate Saliency Model
**As a researcher**, I want to validate the saliency model against human eye-fixation data so that I can ensure the computational model approximates human attention.

**Acceptance Criteria**:
- SALICON test set is loaded and processed.
- Fixation map predictions are generated.
- AUC is calculated and meets threshold (>= 0.70).
- Results are logged to `data/processed/saliency_validation.json`.

### US3: Assess Robustness of Findings
**As a researcher**, I want to assess how analysis choices affect the observed relationship so that I can confirm the stability of the findings.

**Acceptance Criteria**:
- Correlation is re-run with multiple thresholds.
- Alternative saliency model (ViT-B/CAM) is used.
- Sign stability and magnitude change (<= 0.05) are verified.
- Robustness report is generated in `data/processed/robustness_report.md`.

## Functional Requirements

- **FR-001**: System must download Visual Genome and SALICON datasets from verified URLs.
- **FR-002**: System must compute saliency maps using a CPU-compatible model.
- **FR-003**: Saliency model AUC must be >= 0.70 on SALICON benchmark.
- **FR-004**: System must link VG image IDs with recall transcripts.
- **FR-005**: System must filter for false memory candidates (transcript present, VG absent).
- **FR-006**: System must calculate Pearson correlation (r, p, CI).
- **FR-007**: System must perform mixed-effects logistic regression.
- **FR-008**: System must apply Benjamini-Hochberg FDR correction.
- **FR-009**: System must perform sensitivity analysis across thresholds.
- **FR-010**: Power analysis must calculate required sample size for r=0.30, alpha=0.01, power=0.80.
- **FR-011**: System must log exclusion reasons for ID mismatches.

## Non-Functional Requirements

- **NFR-001**: All computations must be CPU-only.
- **NFR-002**: Images must be downsampled to 224x224 for saliency computation.
- **NFR-003**: System must handle study invalidation if noise correlation exceeds threshold.
- **NFR-004**: Ethics gate must check for IRB approval before pipeline execution.

## Data Models

- **Image**: Image ID, URL, dimensions, metadata.
- **Object**: Object ID, image ID, bounding box, category.
- **ParticipantRecall**: Participant ID, image ID, recalled objects, false memories.

## Constitution Check
**Status: PASS**
- T008a: Visual Genome URL verified and documented in `data/verified_sources.md`.
- T008b: SALICON URL verified and documented in `data/verified_sources.md`.
- All foundational prerequisites (T001-T007) are complete.
- Data sources are accessible and valid for the study.
- Ethics gate is configured to check for IRB approval.