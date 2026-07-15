# Epoch Length Decision

## Rationale
10-second epochs provide sufficient spectral resolution for coherence estimation in the 1-40Hz band, reducing variance compared to 2-second epochs. This deviates from initial FR-002 (2s) which has been formally noted as a ratified assumption in the plan.

## Impact
Increased epoch duration improves signal-to-noise ratio for connectivity metrics but reduces the number of independent epochs per recording. This is acceptable for resting-state analysis.