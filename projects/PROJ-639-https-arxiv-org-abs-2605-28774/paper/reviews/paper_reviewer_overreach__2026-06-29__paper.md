---
action_items:
- id: 9cb248c39142
  severity: writing
  text: Temper the claim that 8B AXPO 'surpasses' the 32B Base baseline (75.8% vs
    75.1%) to 'matches or slightly exceeds' or provide statistical significance testing,
    as the margin is within the reported variance of the 8B model (std ~1.2%).
- id: 0e0132b24f43
  severity: writing
  text: Clarify in Table `tab_image_search.tex` and the main text that the 'unseen
    tool' experiment used a GPT-5.4 text proxy rather than a real API tool, to avoid
    overstating the generalization to actual external tool interfaces.
artifact_hash: c3a0cadd7f6fad4530caf3425af37b062e581bf6756717caa2b10b397e7c3c2b
artifact_path: projects/PROJ-639-https-arxiv-org-abs-2605-28774/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:45:04.413328Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method for agentic reasoning, but several central claims extrapolate beyond the statistical evidence or experimental setup provided.

First, the claim that the 8B AXPO model "surpasses the 32B Base baseline on Pass@4" (Abstract, Introduction, Figure 1 caption) is statistically tenuous. The reported margin is 0.7% (75.8% vs 75.1%). Table `tab_main_p1_std.tex` indicates a standard deviation of ~1.2% for the 8B model's Pass@1 performance. Without variance data for the 32B inference-only baseline or a significance test, asserting "surpasses" implies a certainty that the data does not support. This should be tempered to "matches or slightly exceeds" or accompanied by statistical validation.

Second, the experiment labeled "Generalization to an unseen tool" (Table `tab_image_search.tex`, Appendix `app:image-search-gen`) overstates the nature of the generalization. The Appendix admits the "image-search tool" was approximated by "prompting GPT-5.4" due to API costs, rather than using a real tool interface. While the proxy preserves the semantic intent, claiming generalization to a "tool" suggests interaction with a real external system, which did not occur. The caption and main text should explicitly clarify the proxy nature to avoid misleading readers about the robustness of the generalization.

Finally, the Introduction states AXPO "provably dominating from-scratch sampling." While Proposition 1 is mathematically sound, its empirical validity relies on the assumption $p(\vt_1^{\text{src}}) \geq q\, p^{\text{tool}}$. The text should clarify that the *empirical* dominance is contingent on this assumption holding, rather than presenting it as an unconditional guarantee.

Addressing these points will align the claims more closely with the evidence, ensuring the paper's contributions are accurately scoped.
