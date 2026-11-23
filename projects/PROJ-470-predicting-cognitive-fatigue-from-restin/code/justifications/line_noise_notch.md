# Justification for Conditional 50 Hz Notch Filter

## Context
The standard pipeline for EEG preprocessing often includes a notch filter to remove line noise (50 Hz or 60 Hz). However, Constitution Principle VI and FR-002 require that deviations from the "exact pipeline" be justified by data-driven evidence rather than applied blindly.

## Rationale
Line noise is not present in all recordings. It depends on the recording environment, equipment grounding, and shielding. Applying a notch filter indiscriminately can:
1. Remove valid neural signal components near the line frequency.
2. Introduce artifacts (ringing) in the time domain.
3. Reduce the signal-to-noise ratio if the noise floor is already low.

## Implementation Strategy
This implementation (in `code/preprocess.py`) follows a data-driven approach:
1. **PSD Analysis**: Before filtering, the script computes the Power Spectral Density (PSD) of the raw EEG data using Welch's method.
2. **Peak Detection**: It specifically looks for a peak in the 45-55 Hz range.
3. **Thresholding**: A peak is considered significant only if it exceeds the median noise floor by a defined threshold (20 dB).
4. **Conditional Application**:
 - If a significant peak is detected, the 50 Hz notch filter is applied, and this action is logged.
 - If no significant peak is detected, the notch filter is skipped, and a warning is logged.

## Deviation from Standard Pipeline
The deviation is the *conditional* nature of the filter. Instead of a hard-coded "apply notch" step, the pipeline performs an analysis step first. This ensures that the filter is only used when necessary, preserving signal integrity in clean recordings while effectively removing artifacts in noisy ones.

## Reference
- FR-002: Preprocessing must remove line noise but requires justification for deviations.
- Constitution Principle VI: Data-driven decisions over heuristic defaults.