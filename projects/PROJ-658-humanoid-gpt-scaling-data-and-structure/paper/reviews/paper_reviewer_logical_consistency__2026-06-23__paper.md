---
action_items:
- id: caae0f5290c8
  severity: science
  text: "Provide a controlled ablation that isolates the contribution of video\u2011\
    estimated motion data versus purely mocap data (Section\u202F3.1). Without this,\
    \ the claim of \u201Csystematic evidence that video\u2011estimated motion materially\
    \ improves tracking\u201D is not logically supported."
- id: 568b735c0e8e
  severity: science
  text: "Clarify whether performance gains reported in Table\u202F2 are primarily\
    \ due to increased model capacity, data scale, or both. An experiment holding\
    \ model size constant while varying data (or vice\u2011versa) would resolve the\
    \ logical ambiguity."
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T12:58:47.266127Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling narrative that scaling both motion data (to 2 B frames) and model capacity (Transformer‑based) yields a humanoid tracker with zero‑shot generalization. Overall, the logical flow from hypothesis to experimental validation is coherent, but several key conclusions are not fully substantiated by the presented evidence.

1. **Claim of video‑estimated motion benefit (Section 3.1).** The authors state that “video‑estimated motion can materially improve tracking when the model and the training set are scaled appropriately.” However, the experimental sections (e.g., Table 2, Fig. 4) never isolate the effect of video‑derived clips from the purely mocap sources. All reported results use the full 2 B‑frame corpus, making it impossible to attribute any performance gain specifically to the video‑estimated component. This constitutes a logical gap: the conclusion exceeds the data shown.

2. **Balanced diversity argument (Section 3.1, Fig. 2).** The paper introduces Harmonic Motion Embedding (HME) and reports higher “gstd” and “log‑volume” for the curated dataset, arguing that both diversity and balance are necessary. While the correlation between higher diversity metrics and improved zero‑shot performance is suggestive, the causal link is not demonstrated. An ablation where the same amount of data is sampled with and without the HME‑based balanced sampling would be needed to support the claim that balance, not just sheer quantity, drives the observed gains.

3. **Scaling law attribution (Table 2, Section 4.2).** The authors attribute performance improvements to “scaling both data and model capacity.” Yet Table 2 simultaneously varies data size (2 M → 2 B tokens) and model size (MLP 0.25 M → GPT‑L 80 M parameters). Without a controlled experiment that holds one factor constant, the logical inference that data scaling alone yields the observed gains is unsupported. The same applies to the claim that Transformers scale more gracefully than MLPs; the comparison conflates architecture with parameter count.

4. **Zero‑shot superiority over baselines (Table 3, Fig. 5).** The paper demonstrates lower MPJPE/MPJVE on four unseen dance motions compared to GMT, TWIST, and Any2Track. This supports the claim of better zero‑shot tracking within the evaluated set. However, the baselines are limited to MLP‑style trackers; newer transformer‑based or diffusion‑style controllers are not considered. The conclusion that Humanoid‑GPT is “unprecedented” is therefore logically limited to the selected baselines and should be qualified accordingly.

5. **Inference latency claim (Fig. 5).** The statement that the final optimization is “about 5 times faster than TWIST” lacks a baseline measurement for TWIST under comparable hardware and software conditions. While not a fatal logical error, the claim would be stronger with explicit numbers.

In summary, the paper’s central thesis—that scaling data and model yields zero‑shot humanoid tracking—is plausible and largely supported, but several subsidiary claims are not logically justified by the current evidence. Addressing the above points with targeted ablations and clearer experimental controls will strengthen the logical consistency of the manuscript.
