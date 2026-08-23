# Spec Change Request (SCR) 001: Exclusion of Weapons (FR-008)

**Date:** 2023-10-27
**Author:** Automated Science Pipeline
**Status:** Applied

## Background

Functional Requirement FR-008 specified the extraction of attentional metrics for "Weapons" regions of interest (ROIs) in stimulus images. The initial plan relied on YOLOv8 with COCO classes to perform semantic segmentation.

## Problem Statement

The COCO dataset, which serves as the pre-trained weights source for standard YOLOv8 models, does not include a "Weapons" class. The available classes include "Person", "Car", "Animal", etc., but no specific category for weapons. Attempting to detect weapons would require:
1. Training a custom object detection model (high cost, data scarcity).
2. Using a generic "Person" detector and inferring weapon presence (high error rate).
3. Relying on manual annotation (not scalable for this pipeline).

## Decision

**FR-008 is EXCLUDED** from the project scope.

## Impact Analysis

- **Scope Reduction:** The study will now focus exclusively on "Face" vs "Background" ROIs.
- **Methodology:** The pipeline will use the "Face" class from COCO (available in YOLOv8) for segmentation.
- **Scientific Validity:** While the exclusion reduces the breadth of ROI analysis, it ensures the reliability of the segmentation step. The "Face" ROI is a standard and robust proxy for social attention in moral judgement studies.
- **Deliverables:** No artifacts related to weapon detection will be generated.

## Alternative Solutions Considered

- **Custom Training:** Rejected due to lack of labeled weapon datasets and time constraints.
- **Generic Detection:** Rejected due to high false-positive rates.

## Action Items

- [x] Update `spec.md` to remove FR-008.
- [x] Update `plan.md` to explicitly state FR-008 is excluded.
- [x] Ensure `code/processing/segmentation.py` only targets "Face" class.
- [x] Update documentation to reflect this scope change.

## References

- COCO Dataset Classes: https://cocodataset.org/#format-data
- YOLOv8 Documentation: https://docs.ultralytics.com/
