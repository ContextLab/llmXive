---
action_items:
- id: a06a81ce1ce7
  severity: science
  text: Provide quantitative compute budget table (FLOPs/wall-clock) comparing 1T
    MoE LoRA RL vs full-finetuning baselines to substantiate the 10% cost claim (Section
    3.3).
- id: 0cc05be81c7b
  severity: science
  text: Re-run rank-1 standard LoRA baseline with equivalent hyperparameter sweep
    (LR, alpha) to isolate initialization effects from tuning sensitivity (Figure
    5).
- id: c8c2815d56f5
  severity: science
  text: Report confidence intervals or p-values for the majority voting accuracy gains
    (k=198) to confirm statistical significance over repetition baselines (Section
    6).
artifact_hash: 98f7fcdee505c1b0d734c7251a396631b218366acf62d66b7a26c51efa8d758b
artifact_path: projects/PROJ-655-https-arxiv-org-abs-2606-02437/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T21:57:40.523569Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The paper presents a comprehensive three-axis framework, but the scientific evidence supporting the central claims requires strengthening.

**Scale Up (Trillion-Scale RL):** The claim that LoRA RL reduces compute footprint to "approximately 10% of conventional full-parameter RL" (Section 3.3) is currently supported only by qualitative training curves (Figure `scale_up/large_scale.png`) and system descriptions. Without a quantitative table detailing FLOPs, GPU hours, or parameter counts for the 1T MoE baseline versus the LoRA variant, this efficiency claim remains unverifiable. The "proof of existence" framing is insufficient for a scaling law paper; empirical cost data is required.

**Scale Down (Rank Stability):** The conclusion that rank-1 adapters are fundamentally unstable and require OLoRA-tail (Figure `rank1_8b_30b_results`) may be confounded by hyperparameter sensitivity. The standard LoRA baseline shows degradation across batch sizes, but the text does not confirm whether a dedicated learning rate and alpha sweep was performed for the rank-1 standard LoRA configuration. If the baseline was under-tuned, the observed instability could be a tuning artifact rather than a capacity limit necessitating a new initialization method.

**Scale Out (Population Voting):** The majority voting results (Section 6, Figure `model-count-majority-vote`) report a gain from 0.3644 to 0.4867 accuracy with 198 models. While the R^2 is high, the paper lacks p-values or confidence intervals for the difference between "Collaboration" (distinct models) and "Repetition" (same model). Given the high variance often seen in LLM sampling, statistical significance testing is necessary to rule out noise. Additionally, the training protocol for the 198 distinct adapters (e.g., seed diversity vs. data diversity) is not fully detailed, which impacts the interpretation of "diversity."

Finally, most benchmark tables (e.g., `tab:delta-mem-baseline`) report point estimates without standard errors, despite the use of multiple seeds in other sections. Standardizing error reporting across all experiments is required to assess robustness.
