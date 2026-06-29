---
action_items:
- id: f51329f79104
  severity: science
  text: Re-run experiments with multiple random seeds and report standard deviations
    or confidence intervals for all accuracy metrics.
- id: 1ba640f8c15a
  severity: science
  text: Clarify why the 'label-only' baseline outperforms the IPT model on in-distribution
    splits (e.g., EgoDir 73.5% vs 71.7% in Table tab:pt_breakdown).
- id: d49e8ae87329
  severity: science
  text: Expand real-world benchmark sizes (currently 332 questions for Matterport3D)
    or provide bootstrap confidence intervals to support generalization claims.
artifact_hash: c5de9734fccbfd100241f7fc8603c599264726354d7ecbedd4d657c0e121782f
artifact_path: projects/PROJ-681-imaginative-perception-tokens-enhance-sp/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:17:05.257299Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The training data volumes are substantial (e.g., 55,529 Perspective Taking samples, Section `supp_data_pet`), supporting the feasibility of fine-tuning. However, the scientific evidence for the central claim—that Imaginative Perception Tokens (IPT) enhance spatial reasoning—is currently insufficient.

First, baseline comparisons in Table `tab:pt_breakdown` (e001) are ambiguous. The 'Bagel (label-only)' baseline achieves 73.5% accuracy on the AI2-THOR EgoDir split, outperforming the IPT 'Mixed Training' model (71.7%). This suggests IPT does not improve in-distribution performance over standard fine-tuning, contradicting the paper's primary assertion. The benefit appears restricted to out-of-distribution generalization (Real splits: 50.6% vs 46.6%), which requires clearer framing.

Second, statistical rigor is lacking. All reported accuracies (e.g., 73.5, 61.1) are single-point estimates without standard deviations or confidence intervals. No mention of multiple random seeds is found in the methodology. This prevents assessment of result stability or significance, especially given the small real-world test sets (332 questions, Section `supp_data_pt`).

Third, the 'Text CoT' baseline relies on GPT-5.1 using 'ground-truth metadata' (Section `supp_data`). If this metadata leaks into the evaluation pipeline, it risks inflating baseline performance or creating data leakage.

To salvage the central claim, the authors must: (1) Re-run experiments with multiple seeds to report variance; (2) Clarify why IPT underperforms label-only on in-distribution splits; (3) Expand real-world test sets or provide bootstrap confidence intervals. Without these, the evidence for IPT's specific contribution remains inconclusive.
