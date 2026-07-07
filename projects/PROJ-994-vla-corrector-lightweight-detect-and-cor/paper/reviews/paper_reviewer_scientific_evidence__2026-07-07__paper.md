---
action_items:
- id: 199237c34b56
  severity: writing
  text: The paper presents a compelling framework for adaptive action horizons, but
    the experimental design in the main results tables lacks the necessary statistical
    rigor to fully support the magnitude of the claimed improvements. 1. Missing Variance
    and Seed Counts in Main Benchmarks The central claims regarding performance gains
    on MetaWorld (Table 1) and LIBERO (Table 2) rely on single-point success rates
    (e.g., 64.35% vs 48.70%). The paper mentions in the appendix that multi-seed data-scaling
    anal
artifact_hash: d7358417426c747fa4ca8d918e3157dfcd577dc0f92cbf50c88254f4dca67f3f
artifact_path: projects/PROJ-994-vla-corrector-lightweight-detect-and-cor/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T03:35:34.578548Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling framework for adaptive action horizons, but the experimental design in the main results tables lacks the necessary statistical rigor to fully support the magnitude of the claimed improvements.

**1. Missing Variance and Seed Counts in Main Benchmarks**
The central claims regarding performance gains on MetaWorld (Table 1) and LIBERO (Table 2) rely on single-point success rates (e.g., 64.35% vs 48.70%). The paper mentions in the appendix that multi-seed data-scaling analyses used seeds {42, 123, 999}, but it does not explicitly state that the *main* benchmark results in Tables 1 and 2 were averaged over these seeds, nor does it report the standard deviation. In VLA research, success rates can vary significantly (often ±3-5%) across seeds due to initialization and stochasticity. A 15-point gain is likely real, but without reported variance (mean ± SD) and a clear statement of the number of seeds (n), a skeptical reader cannot rule out that the reported numbers are the result of a "lucky seed" or an outlier run. The design currently fails to distinguish a robust effect from sampling noise.

**2. Aggregated Variance in Real-World Results**
In the real-world evaluation (Table 3), the authors report "Mean ± SD across tasks" (e.g., 73.3 ± 6.5). This is a methodological flaw in the evidence design. Aggregating variance across three distinct task groups (Pick-and-place, Alignment, Disturbance) with different difficulty levels obscures the true reliability of the method on any single task. A method could have high variance on the "Disturbance" tasks (where it is most needed) but low variance on "Pick-and-place," resulting in a misleadingly low overall SD. To support the claim of robustness, the paper must report the success rate and standard deviation *across the 20 trials* for each individual task, not just the average across tasks.

**3. Baseline Tuning Asymmetry**
The ablation study in Table 4 isolates the components (Truncation vs. OGG), but the comparison against the "Baseline" in the main tables (Table 1) does not explicitly confirm that the baseline policies were subjected to the same hyperparameter search (e.g., learning rate, action horizon tuning) as the VLA-Corrector variants. If the baseline was a "vanilla" run while the proposed method benefited from implicit tuning during the development of the corrector, the reported gains may be confounded by the tuning effort rather than the mechanism itself. The evidence design requires a "fair baseline" control where the baseline is re-tuned with the same budget to isolate the contribution of the detect-and-correct mechanism.

Addressing these points by reporting seed counts, per-task trial variance, and ensuring fair baseline tuning will significantly strengthen the evidentiary support for the paper's central claims.
