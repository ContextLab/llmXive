# Downstream review concerns (address in this revision)

A downstream convergence panel kicked this project back to the idea stage. You MUST revise the idea — especially the `Methodology sketch` — to RESOLVE each concern below, not merely re-state the idea.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'methodology'. Routing to 'flesh_out_in_progress' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-008 mandates a custom PyTorch training loop avoiding libraries like `stable-baselines3`, but the Methodology Sketch (section 'Methodology sketch') proposes using `stable-baselines3` for the CPU‑optimized RL loop, creating a direct contradiction about allowed implementation tools.
- FR-017 mandates the use of the Wilcoxon signed‑rank test for *all* statistical comparisons, yet the Idea Md section (Methodology sketch) mentions a paired t‑test. This discrepancy could lead to inappropriate test selection if not reconciled.
