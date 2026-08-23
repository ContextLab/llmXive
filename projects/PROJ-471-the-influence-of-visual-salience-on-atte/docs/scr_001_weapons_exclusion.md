# SCR-001: Exclusion of Weapons (FR-008)

**Status**: Approved
**Date**: 2023-10-27
**Author**: Implementation Team
**Approver**: Review Board

## Reason

The original functional requirement FR-008 ("Analyze attention to weapons") cannot be implemented because the COCO dataset, used as the basis for YOLOv8 segmentation in this project, does not include a "weapon" class. The available classes are limited to standard objects (e.g., person, car, dog). Attempting to detect weapons would require a custom model training pipeline which is out of scope for the current compute budget and timeline.

## Impact

- **Scope Reduction**: The study scope is reduced to analyzing attentional bias towards "Face" regions vs. Background.
- **Hypothesis Adjustment**: The hypothesis regarding "threatening objects" (weapons) is removed. The focus remains on "Face" salience.
- **No Alternative**: No feasible alternative detection method exists within the project constraints (CPU-only, pre-trained models only).

## Action

- Remove all references to "weapons" from `spec.md` and `plan.md`.
- Update `code/processing/segmentation.py` to only target the "Face" class.
- Update documentation to reflect the "Face-only" analysis scope.

## Verification

- Confirmed YOLOv8 COCO classes do not include "weapon".
- Confirmed no custom training data is available in the `data/raw` directory.
- Updated `spec.md` to remove FR-008.
