# Epoch Length Decision

## Rationale

Longer epochs provide sufficient spectral resolution for coherence estimation in the 1-40Hz band, reducing variance compared to shorter epochs. This deviates from initial FR-002 (2s) which has been formally noted as a ratified assumption in the plan via T014a.

## Impact

Increased epoch duration improves signal-to-noise ratio for connectivity metrics but reduces the number of independent epochs per recording. This is acceptable for resting-state analysis.

## Spec Reference

This decision formally ratifies the modification of `spec.md` requirement FR-002, changing the epoch length from "2-second" to "10-second" epochs. This change is reflected in `code/config.py` (`epoch_length_sec = 10`).