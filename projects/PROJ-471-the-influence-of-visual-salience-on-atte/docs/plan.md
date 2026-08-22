# Implementation Plan: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Project Overview

This project investigates how visual salience influences attentional bias in moral judgement tasks.
The study utilizes eye-tracking data and computational visual salience models to analyze
where participants look when presented with moral dilemmas involving faces and backgrounds.

## Scope and Constraints

### Functional Requirements (FR)
- **FR-001**: Download and cache the OpenNeuro dataset (ds004380).
- **FR-002**: Generate DeepGaze II salience maps for all stimulus images.
- **FR-003**: Parse raw eye-tracking data into fixation events.
- **FR-004**: Extract fixation metrics (Dwell Time, First Fixation Probability) for "Face" ROIs.
- **FR-005**: Align salience metrics with eye-tracking data on TrialID.
- **FR-006**: Apply FDR correction to all statistical p-values.
- **FR-007**: Append "Correlational Only" disclaimer to all derived data artifacts.
- **FR-008**: [REJECTED] Exclusion of "Weapons" ROI.
 - *Reason*: The COCO dataset (used by YOLOv8) does not have a distinct "weapon" class.
 - *Impact*: The study scope is reduced to "Face" vs "Background" comparisons only.
 - *Status*: Rejected via SCR-001.
- **FR-009**: [REJECTED] Exclusion of Low-Level Feature Covariates.
 - *Reason*: Multicollinearity with DeepGaze II features.
 - *Status*: Rejected via SCR-002.

### Non-Functional Requirements (NFR)
- **SC-001**: Process at least 80% of the source images.
- **SC-002**: Salience generation must complete within 6 hours on CPU.
- **SC-003**: Statistical power must be >= 0.8 for valid inference.

## Study Design Summary

**Primary Hypothesis**: Visual salience of the "Face" region predicts dwell time, which in turn correlates with moral judgement severity.

**Independent Variables**:
- Visual Salience (DeepGaze II score for Face ROI)

**Dependent Variables**:
- Dwell Time on Face
- First Fixation Probability on Face
- Moral Judgement Score

**Control Variables**:
- Luminance (implicitly handled by DeepGaze II)
- Image Resolution

**Exclusions**:
- "Weapons" ROI (FR-008) is explicitly excluded due to lack of COCO class support (SCR-001).
- Low-level feature covariates (FR-009) are excluded to prevent multicollinearity (SCR-002).
- The study proceeds with **"Face" ROIs only**.

## Complexity Tracking

### Data Volume
- Source: OpenNeuro ds004380
- Estimated Images: ~1,200
- Estimated Trials: ~1,200
- Salience Maps: ~1,200 (1024x1024 float32)

### Computational Load
- **Salience Generation**: High (CPU intensive, DeepGaze II)
- **Segmentation**: Medium (YOLOv8 inference)
- **Statistical Modeling**: Low (Linear Mixed Models)

### Risk Assessment
- **High**: Memory usage during salience generation (Target < 7GB).
- **Medium**: Data alignment mismatches.
- **Low**: Statistical power (mitigated by power analysis).

## Implementation Phases

### Phase 1: Setup
- Project structure, requirements, linting configuration.

### Phase 2: Foundational
- Configuration management, logging, versioning, data models.
- **Governance**: SCR-001 (Weapons Exclusion), SCR-002 (Low-Level Covariates Exclusion).

### Phase 3: User Story 1 - Data Ingestion
- Download dataset, generate salience maps, validate completeness.

### Phase 4: User Story 2 - Attention Metrics
- Parse eye-tracking, segment faces, align metrics.

### Phase 5: User Story 3 - Statistical Analysis
- Power analysis, LMM fitting, robustness checks.

### Phase 6: Polish
- Documentation, integration tests, final validation.

## Governance & Audit Trail

All major decisions regarding scope changes or requirement exclusions are documented in the `docs/` directory:
- `scr_001_weapons_exclusion.md`: Details the rejection of FR-008.
- `scr_002_lowlevel_covariates_exclusion.md`: Details the rejection of FR-009.

This plan explicitly confirms that the study proceeds with **"Face" ROIs only**, adhering to the constraints defined in SCR-001.