# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Only **5 independent runs per variant** are planned (total 30 runs). This sample size is far too small to achieve adequate statistical power for detecting the claimed ≥60 % CPU‑time reduction and ≥80 % performance‑retention, even with bootstrapping. The plan acknowledges low power (< 0.8) but still expects to meet significance thresholds, which is unsound.
- The fallback to a Kaggle T4 GPU if the model cannot load on CPU introduces a hardware confound. Runs that switch to GPU will have different CPU‑time characteristics, violating the assumption that per‑step CPU cost is comparable across variants.
- Early‑stopping when average reward ≥ 0.8 may cause the Student‑Only variant to terminate earlier than the Baseline. Comparing **per‑step** CPU time under such differing episode counts can conflate convergence speed with computational efficiency, biasing the SC‑002 cost‑reduction claim.
- RQ1 and RQ2 are framed as causal statements (e.g., “Student‑Only gating can replace the teacher‑student confidence gap”). The experimental design is purely comparative/observational and does not control for all pathways that could affect performance, so causal inference is not justified.
- The plan references an extra functional requirement **FR‑007** (Pearson r computation) which does not exist in the specification. This is an over‑reach; either remove the FR‑007 mention or add a corresponding FR to the spec.
- The plan relies on a ‘GPU Escape Hatch’ that automatically switches to a Kaggle T4 GPU if the 8‑bit Qwen2.5‑1.7B model cannot be loaded on the CPU runner. This introduces a dependency on external GPU resources that are not guaranteed to be free, available, or compatible with the GitHub Actions free‑tier environment. The compute feasibility claim (≤ 6 h per run on a 2 vCPU runner) is therefore unsound, and the total workload (5 runs × 3 variants × 2 environments = 30 runs) may exceed the CI time quotas. The methodology must be revised to ensure the entire experiment can be completed within the stipulated free‑CPU constraints without fallback to external GPUs.
