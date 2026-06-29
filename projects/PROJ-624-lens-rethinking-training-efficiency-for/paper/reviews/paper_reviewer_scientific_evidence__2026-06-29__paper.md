---
action_items:
- id: 0bb6b7bc2dc5
  severity: science
  text: Clarify compute normalization (MFU vs Peak TFLOPS) to substantiate the 19.3%
    efficiency claim.
- id: 1255069c432b
  severity: science
  text: Explicitly state reasoner usage in Table 2 and ensure competitors are evaluated
    with comparable modules.
- id: 02dcc0fd01e5
  severity: science
  text: Justify Toy Model ablation scaling or run key ablations on the full 3.8B model.
- id: cc0f433521f3
  severity: science
  text: Add error bars or statistical significance testing to benchmark scores.
artifact_hash: ee50a22651a80bef159316dc0dc914d3939b89b46e64d966972efb2307431ada
artifact_path: projects/PROJ-624-lens-rethinking-training-efficiency-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T04:09:33.275654Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The central claim of training efficiency relies on a compute comparison between 192K A100 hours and 314K H800 hours, normalized by peak BF16 TFLOPS (Introduction, footnote 1). While the authors acknowledge MFU differences, using peak TFLOPS to derive the "19.3%" figure introduces significant uncertainty, as actual training efficiency depends heavily on architecture-specific MFU and communication overhead. A more robust metric would be total FLOPs consumed or energy usage to substantiate the efficiency claim.

The main benchmark results in Table 2 (Comparison with State-of-the-art Models) report scores for "Lens (20-step)" that match the "Lens w/ GPT-5.5" row in Appendix Table "tab:different reasoners". However, the table does not explicitly state that a reasoner is active, nor does it clarify if competing models (e.g., Z-Image, FLUX.2) were evaluated with comparable reasoner modules. If the reasoner contributes significantly to the GenEval score (0.930 vs 0.843 w/o reasoner), this confounds the model's intrinsic generation capability with the prompt-rewriting module, potentially inflating the perceived advantage of the 3.8B backbone.

Ablation studies for VAE, Language Encoder, and Caption Density (Section 3.1, Figures 3-6) are conducted on "Lens-Toy" (1.2B backbone) rather than the full 3.8B model. While this reduces cost, the scaling behavior of these components is not guaranteed to be linear. For instance, the benefit of a semantic VAE might differ at larger scales. The RL ablation (Table 1) uses the full model, which is stronger, but the pre-training ablations remain a limitation regarding the generalizability of the findings to the final architecture.

Finally, benchmark scores are reported as single point estimates without error bars or statistical significance testing across multiple seeds. Given the variance inherent in generative model evaluation, confidence intervals are necessary to support claims of "surpassing" larger models. Without this, the observed differences could be within the noise floor of the evaluation metrics.
