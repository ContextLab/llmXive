# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The power analysis script targets a generic effect size (β≈0.5) and a minimum N ≥ 60, but the plan does not justify why a medium effect is plausible for this paradigm, nor does it specify the number of scenarios, participants per scenario, or the intra‑class correlation expected. Without explicit assumptions about variance components (participant and scenario random effects), the calculated sample size may be insufficient to achieve 80 % power for the CLMM, risking a Type II error.
- The plan cites the **CLIP‑Microscope (csv)** dataset (https://huggingface.co/datasets/ernestoBocini/clip-microscope-imagenet/resolve/main/metadata/neuron_summary.csv) as the source of base images. This dataset consists of microscopy images of neurons and does **not contain human‑centric, socially relevant scenes** required for a moral‑judgment experiment. The specification (spec.md) and user stories explicitly call for open visual datasets such as **Visual Genome** that provide everyday scenes with potential moral ambiguity. Using a neuroscience image set therefore fails to provide appropriate stimulus material, violating the core research question and FR‑001/FR‑008.
