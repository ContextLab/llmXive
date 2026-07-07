---
action_items:
- id: 5a289b378484
  severity: writing
  text: Abstract claims 'instruction-heavy mixtures scale better' generally, but evidence
    (Sec 5) only tests Qwen2.5 backbones. Scope claim to 'within Qwen2.5 family' or
    add evidence from other architectures.
- id: e7cc7470a982
  severity: writing
  text: Abstract states 63.6% accuracy is enabled by the dataset, but results (Table
    1) depend on the specific InternVL training recipe. Clarify that this performance
    is specific to the InternVL architecture and recipe used.
- id: b0ee62f8d906
  severity: writing
  text: Paper excludes grounding benchmarks (Sec 2.1) yet presents results as comprehensive.
    Add a limitations paragraph stating that gains are unverified for spatial grounding
    tasks, preventing over-generalization.
artifact_hash: d4a22931e6b886440cd41104bb215d7473154b2e0677ff1cb31fe0010e81d224
artifact_path: projects/PROJ-1001-datacomp-vlm-improved-open-datasets-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T10:29:03.402461Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper generally maintains a strong alignment between its claims and the evidence provided, particularly in its detailed ablation studies and decontamination protocols. However, there are three instances where the framing in the abstract and conclusion slightly exceeds the specific scope of the experimental evidence.

First, the claim that "instruction-heavy mixtures scale better than caption-heavy ones" is presented as a general principle in the abstract. The evidence (Section 5, Figure 2) supports this robustly for the Qwen2.5-Base and Qwen2.5-Instruct backbones, but the paper does not test other model families (e.g., Llama-based or proprietary architectures). While the control experiments suggest robustness to the *type* of instruction initialization, the claim of general "scaling better" across all VLMs is not fully licensed by the single-family study. Narrowing this to "within the Qwen2.5 family" or adding a qualifier about the tested architectures would align the claim with the evidence.

Second, the abstract highlights the 63.6% accuracy on the 33-task suite as a result of the dataset ("The resulting DataComp-VLM-Baseline enables..."). While the dataset is the primary variable, the specific performance is inextricably linked to the specific training recipe (InternVL architecture, specific hyperparameters, image resolution) detailed in Appendix A. The phrasing risks implying that the dataset alone is sufficient to achieve this result on any 8B model, whereas the evidence only supports this for the specific InternVL training pipeline. Clarifying that this performance is achieved "using the InternVL training recipe" would be more precise.

Finally, the paper makes a deliberate methodological choice to exclude grounding benchmarks (RefCOCO, etc.) due to contamination risks (Section 2.1). While this is a sound scientific decision, the conclusion presents the results on the remaining 33 tasks as a broad validation of the dataset's improvements. This creates a scope gap: the paper claims to benchmark "improved open datasets" but omits a significant domain (spatial grounding) where the data mixing strategy might behave differently. The paper should include a limitations statement explicitly acknowledging that the reported gains and the "instruction-heavy" finding have not been validated on grounding tasks, preventing readers from over-generalizing the dataset's utility to all VLM capabilities.

These are primarily framing issues that can be resolved by tightening the language in the abstract and adding a specific limitations paragraph, rather than requiring new experiments.
