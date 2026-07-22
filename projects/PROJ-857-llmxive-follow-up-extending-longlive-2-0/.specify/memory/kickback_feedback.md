# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan uses a 'downsampled subset' of Kinetics-400 (e.g., 500 clips) to fit memory constraints. However, the research question targets 'narrative consistency' in video generation. Kinetics-400 is an action recognition dataset, not a narrative consistency dataset. The construct validity of using action labels or generic clips to measure 'narrative consistency' is unproven. The plan does not define how 'narrative' is constructed or measured in these clips, risking a mismatch between the measured metric (CLIP temporal coherence) and the intended construct (narrative consistency).
- The plan states: 'Stochastic rounding is implemented via Python/NumPy masking and noise injection on 32-bit tensors.' This simulates the *noise* of low-bit precision but does not simulate the *memory footprint* or *bandwidth* constraints of actual NVFP4 hardware. The claim that this approach validates 'NVFP4 Parallel Infrastructure' is methodologically weak; it only validates the *numerical stability* of the algorithm, not the infrastructure's performance or memory efficiency claims. The 'memory footprint' claim relies on a theoretical formula, not the simulation, creating a disconnect between the simulation's purpose and its output.
