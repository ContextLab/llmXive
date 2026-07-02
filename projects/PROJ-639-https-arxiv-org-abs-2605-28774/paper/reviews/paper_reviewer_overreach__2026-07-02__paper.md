---
action_items:
- id: 36781bc73231
  severity: science
  text: The claim that AXPO 'provably dominates' raw sampling (Introduction, Contribution
    2) relies on Proposition 1, which assumes the selected prefix satisfies p(prefix)
    >= q * p^tool. The paper does not empirically verify that the uncertainty-based
    selection strategy consistently yields prefixes meeting this threshold across
    all benchmarks. Without this verification, the 'provably' claim overreaches the
    demonstrated evidence.
- id: 98ab02b6cf6a
  severity: writing
  text: The abstract and introduction state that the 8B AXPO model 'surpasses the
    32B Base baseline' on Pass@4. While Table 4 shows 75.8 vs 75.1, the 32B model
    is an inference-only baseline without the SFT+RL pipeline. Comparing a trained
    8B model to an untrained 32B model conflates architectural scale with training
    efficacy, potentially overstating the method's standalone contribution relative
    to scaling laws.
- id: c42ce8d8e0ab
  severity: writing
  text: The paper claims AXPO 'concentrates exploration precisely where the gap manifests'
    (Introduction). However, the analysis in Section 2.2 (Fig 3) diagnoses the gap
    using GRPO rollouts. The paper does not explicitly demonstrate that the specific
    prefixes selected for resampling in AXPO training are the exact same ones that
    would have been 'all-wrong' under a pure GRPO regime, leaving a slight logical
    gap between the diagnosis and the targeted intervention.
artifact_hash: c3a0cadd7f6fad4530caf3425af37b062e581bf6756717caa2b10b397e7c3c2b
artifact_path: projects/PROJ-639-https-arxiv-org-abs-2605-28774/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T05:16:33.706456Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling diagnosis of the "Thinking-Acting Gap" and a novel method (AXPO) to address it. However, there are instances where the claims extend slightly beyond the strictly demonstrated evidence, particularly regarding theoretical guarantees and the nature of the baselines used for comparison.

First, the claim in the contributions list that AXPO "provably dominates from-scratch sampling" (Introduction, bullet 2) is technically supported by Proposition 1 in Section 3.1. However, the proposition's validity is conditional on the selected prefix satisfying $p(\vt_1^{\text{src}}) \geq q\, p^{\text{tool}}$. While the authors argue that uncertainty-based selection targets high-yield prefixes, the paper does not provide an empirical analysis confirming that the *actual* prefixes selected during training consistently meet this mathematical threshold across all benchmarks and training steps. Without this verification, the absolute claim of "provably dominating" is an overreach; the method is *designed* to dominate under this condition, but the condition's universal satisfaction is not proven.

Second, the headline claim that the 8B AXPO model "surpasses the 32B Base" (Abstract, Introduction, Conclusion) is statistically true based on the reported numbers (75.8 vs 75.1 Pass@4). However, the 32B model is an "inference-only baseline" (Table 4 caption) that has not undergone the SFT+RL training pipeline. Comparing a heavily post-trained 8B model to a raw 32B model conflates the benefits of the training recipe with the benefits of the method itself. A more rigorous claim would compare against a 32B model that has undergone the same SFT+GRPO pipeline, or explicitly frame the comparison as "surpassing a 4x larger *untrained* baseline." The current phrasing risks overstating the efficiency gains by ignoring the potential performance of a 32B model with the same training regimen.

Finally, the narrative that AXPO targets the "all-wrong tool-using subgroups" identified in Section 2.2 assumes that the failure modes observed in the GRPO baseline persist identically in the AXPO training loop. While highly likely, the paper does not explicitly show a correlation between the prefixes selected for resampling and the specific "all-wrong" trajectories that would have occurred under a standard GRPO rollout for the same questions. A brief analysis confirming this overlap would strengthen the causal link between the diagnosis and the solution.

These are minor issues of precision rather than fundamental flaws. The core science is sound, but tightening the language around the theoretical conditions and the baseline comparison would eliminate the overreach.
