# Software Change Request (SCR): Exclusion of FR-008 ("Weapons")

**SCR ID**: SCR-001
**Date**: 2023-10-27
**Status**: Accepted (Rejected Implementation)
**Related Feature Request**: FR-008
**Related User Story**: US1 (Data Ingestion and Salience Map Generation)

## 1. Executive Summary

This document formally documents the decision to **exclude** Feature Request FR-008, which proposed the inclusion of "Weapons" as a distinct Region of Interest (ROI) for visual salience analysis. The exclusion is necessitated by a technical limitation in the selected object detection backbone (YOLOv8/COCO dataset) and the lack of a verified, real-world data source for weapon-specific semantic segmentation that aligns with the study's ethical and data integrity constraints.

Consequently, the study scope is reduced to the analysis of "Face" vs. "Background" ROIs only.

## 2. Root Cause Analysis

### 2.1. Lack of COCO Class Support
The project relies on the YOLOv8 model trained on the Microsoft COCO (Common Objects in Context) dataset for semantic segmentation of ROIs. The COCO dataset defines 80 standard object classes.

- **Available Classes**: Includes `person`, `face` (via face detection models or person-class refinement), `car`, `dog`, etc.
- **Missing Class**: The class `weapon` (or specific subclasses like `gun`, `knife`, `sword`) is **not** a standard class in the COCO taxonomy.

Attempting to train a custom detector for weapons would require:
1. A large, annotated dataset of weapons in moral dilemma contexts (which does not exist as a public, verified source).
2. Significant computational resources for fine-tuning.
3. Ethical review for generating training data involving weapons.

Given the project's constraint to use **real, programmatically accessible data** without fabricating synthetic datasets or placeholder rows, and the absence of a pre-trained, verified weapon detector, this path is not feasible within the current scope.

### 2.2. Data Integrity Constraints
The project mandates that all data loaders must "fail loudly" if real data cannot be fetched. There is no existing public API or Hugging Face dataset that provides pre-segmented "weapon" masks for the specific stimulus images used in this study. Creating a synthetic "weapon" mask would violate the "Real Data Only" policy.

## 3. Impact Assessment

### 3.1. Scope Reduction
- **Original Scope**: Analysis of salience bias across Face, Weapon, and Background regions.
- **Revised Scope**: Analysis of salience bias across Face and Background regions only.

### 3.2. Scientific Validity
The primary hypothesis concerns the influence of visual salience on attentional bias in *moral judgements*. While weapons are often salient in moral contexts, the presence of the "Face" ROI remains the primary driver of social attention in the selected stimuli. The exclusion of weapons reduces the complexity of the visual scene analysis but does not invalidate the core investigation into Face vs. Background attentional dynamics.

### 3.3. Downstream Effects
- **US1 (Data Ingestion)**: Salience generation will proceed without weapon-specific masking.
- **US2 (Metric Extraction)**: Eye-tracking metrics will be calculated only for "Face" and "Background" ROIs.
- **US3 (Analysis)**: Statistical models will not include "Weapon Salience" as a predictor variable.

## 4. Alternatives Considered

| Alternative | Feasibility | Reason for Rejection |
|:--- |:--- |:--- |
| Train custom YOLO model | Low | No verified real-world dataset available; violates "no synthetic data" rule. |
| Use generic "person" class | Low | Does not distinguish weapon from person; confounds variables. |
| Manual annotation | Low | Prohibitively time-consuming; not reproducible; violates automated pipeline constraints. |
| **Exclude FR-008** | **High** | Maintains data integrity and project timeline; focuses on available, verifiable ROIs. |

## 5. Decision

**Status**: **REJECTED** (Implementation of FR-008 is rejected).

The project will proceed with the following configuration:
- **Included ROIs**: Face, Background.
- **Excluded ROIs**: Weapons.
- **Action**: Update `plan.md` and `spec.md` to reflect this exclusion.

## 6. References

- COCO Dataset Documentation: https://cocodataset.org/
- YOLOv8 Model Zoo: https://docs.ultralytics.com/
- Project Constitution Principle II (Citation Verification)
- Project Constitution Principle V (Data Integrity)

---
*This document serves as the formal record for the exclusion of FR-008.*