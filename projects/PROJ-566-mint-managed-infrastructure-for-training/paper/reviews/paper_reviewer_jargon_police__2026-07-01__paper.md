---
action_items:
- id: 2253d16cf93f
  severity: writing
  text: Define 'MLA' (Multi-Latent Attention) and 'DSA' (Dynamic Sparse Attention)
    at first use in the Abstract and Introduction. These acronyms are used without
    definition, excluding readers unfamiliar with specific model families like GLM-5
    or Kimi K2.
- id: db55982988fd
  severity: writing
  text: Replace 'rollout correction' with a plain-language explanation (e.g., 'adjusting
    training weights based on probability mismatches') in the Abstract and Section
    4. The term is used as a noun phrase without context for non-specialists.
- id: 3770e50babc5
  severity: writing
  text: Define 'IcePop' when first mentioned in Section 4. It is currently treated
    as a known entity ('IcePop-style rollout correction') without citation or explanation
    of the mechanism, assuming prior knowledge of a specific paper or technique.
- id: a892bca38bed
  severity: writing
  text: Clarify 'Tinker-compatible' in the Abstract and Introduction. While 'Tinker'
    is cited, the specific nature of the compatibility (API surface, data formats,
    or control plane) is not explained, making the claim opaque to readers outside
    the specific ecosystem.
- id: aca3f5a26f6d
  severity: writing
  text: Replace 'hot working sets' with 'active data in memory' or similar plain language
    in the Abstract and Section 4. 'Hot' is jargon that may confuse readers not versed
    in cache hierarchy terminology.
- id: 36fc7bdae766
  severity: writing
  text: Define 'TP' (Tensor Parallelism) and 'EP' (Expert Parallelism) at first use
    in Section 4 and the tables. These acronyms are used frequently without expansion,
    hindering readability for general systems researchers.
- id: a49be93735e3
  severity: writing
  text: Replace 'fanout' with 'number of objects' or 'object count' in Section 4 and
    Table 4. 'Fanout' is a specific networking/storage term that is used here to describe
    tensor object counts, which may be ambiguous.
- id: 2b3cef46fef0
  severity: writing
  text: Define 'MoE' (Mixture-of-Experts) at its first occurrence in the Abstract.
    While common in the field, the paper claims to address a broad audience, and the
    acronym is used immediately without definition.
artifact_hash: 9b74dd1f4b8f2d4815ea056f5e26899cdd80d0bb7bac2914c7ef2512791b5d74
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:07:53.336932Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: full_revision
---

The paper suffers from significant jargon overuse, particularly regarding acronyms and domain-specific shorthand that are not defined at first use. This creates a barrier to entry for non-specialist readers and even for systems researchers outside the immediate LLM post-training niche.

In the **Abstract**, the terms **MLA** (Multi-Latent Attention) and **DSA** (Dynamic Sparse Attention) appear without definition. These are specific architectural features of models like GLM-5 and Kimi K2, not universal standards. Similarly, **MoE** (Mixture-of-Experts) is used immediately without expansion. The phrase "rollout correction" is used as a technical noun without explaining the underlying mechanism (probability masking), and **IcePop** is referenced as a known style of correction without defining the method or citing the specific paper at that point.

In **Section 4 (Scaling)**, the text relies heavily on unexpanded acronyms: **TP** (Tensor Parallelism), **EP** (Expert Parallelism), and **DSA** again. The term "hot working sets" is used to describe active memory states; while standard in OS literature, "active data in memory" would be more accessible. The phrase "small-object fanout" in Section 4 and Table 4 uses "fanout" in a way that might be confused with network fanout; "object count" or "tensor fragmentation" would be clearer.

The term **Tinker-compatible** is used repeatedly (Abstract, Introduction, Section 3) to imply a specific API contract, but the nature of this compatibility is never explicitly defined for the reader. Is it a REST API? A Python library? A data format? Without this definition, the claim is opaque.

Finally, **Section 5** and the **Appendix** continue this trend with terms like "hotset," "cold churn," and "p95" (which, while common, should be defined as "95th percentile" on first use in a formal paper). The reliance on "rank-1" and "rank-32" without explaining that "rank" refers to the low-rank matrix dimension in LoRA also assumes prior knowledge.

To meet the standard of a general systems or AI infrastructure paper, every acronym must be defined at first use, and every specialized term (like "fanout" in this context, "hotset," or "rollout correction") must be briefly explained in plain English.
