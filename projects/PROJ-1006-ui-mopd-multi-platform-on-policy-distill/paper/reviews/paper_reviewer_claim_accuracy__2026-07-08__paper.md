---
action_items:
- id: 41f1e19c35b6
  severity: writing
  text: The paper presents a novel method for cross-platform GUI agents, but several
    factual claims rely on non-existent or unverified external entities, and there
    are minor numerical inconsistencies between sections. First, the data collection
    pipeline relies on specific teacher models that appear to be hallucinated. The
    Appendix (Section "Query Generation") and Section 3.1 explicitly state that "Kimi-K2.6"
    and "Gemini-3.1-Pro" were used to generate queries and trajectories. As of the
    current public re
artifact_hash: c439848c25362cb29ce1d9d26f8d9ad2ccefc577792fd895c77799b18522bbdd
artifact_path: projects/PROJ-1006-ui-mopd-multi-platform-on-policy-distill/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-08T02:54:40.110859Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a novel method for cross-platform GUI agents, but several factual claims rely on non-existent or unverified external entities, and there are minor numerical inconsistencies between sections.

First, the data collection pipeline relies on specific teacher models that appear to be hallucinated. The Appendix (Section "Query Generation") and Section 3.1 explicitly state that "Kimi-K2.6" and "Gemini-3.1-Pro" were used to generate queries and trajectories. As of the current public record, neither "Kimi-K2.6" nor "Gemini-3.1-Pro" exist (current versions are typically Kimi 1.5/2.0 and Gemini 1.5/2.0). Citing non-existent models as the source of the training data undermines the reproducibility of the results. The authors must verify the actual model versions used and correct the text and bibliography accordingly.

Second, there is a minor discrepancy in the reported dataset size. The Introduction states the dataset contains "nearly 10K high-quality cross-platform interaction trajectories," while Appendix Table 1 ("Dataset Composition") lists a total of "~11.5K" trajectories. While "nearly 10K" could be interpreted as a conservative lower bound or a rounding error, the specific number 11.5K in the table suggests the Introduction should be updated to "approximately 11.5K" or "over 11K" for consistency.

Finally, the claim of being the "first method" to introduce multi-teacher on-policy distillation (MOPD) into GUI agents is supported by the Related Work section, which notes MOPD is "largely unexplored in GUI agent." However, the authors should ensure that the specific citation for "MOPD" in the Related Work (e.g., `Mimo-v2`, `GLM-5`) accurately reflects that these are general foundation models and not GUI-specific, to avoid any ambiguity about the novelty claim.

These issues are primarily fixable by correcting the model names and aligning the numbers, but the non-existent model names are a significant barrier to verifying the data construction process.
