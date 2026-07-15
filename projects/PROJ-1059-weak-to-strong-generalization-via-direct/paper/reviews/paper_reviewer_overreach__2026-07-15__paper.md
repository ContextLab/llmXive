---
action_items:
- id: 82a4dde13b81
  severity: writing
  text: 'Abstract: The claim ''boosts Qwen3-1.7B... in just 4 hours'' presents a specific
    result from one teacher pair as a general method capability. Scope this to ''in
    our primary setting'' or clarify it applies to the JustRL pair to avoid implying
    universal efficiency.'
- id: 2691e24532d5
  severity: writing
  text: 'Introduction: The comparison to Polaris (''at least a week'') relies on external
    estimates rather than an internal matched experiment. Clarify this is a comparison
    to reported external results, not a direct internal ablation, to avoid overstating
    the empirical basis.'
- id: af6ad80362a8
  severity: writing
  text: 'Conclusion: The claim ''outperforms step-matched direct RL'' is broad. The
    data only supports this for specific pairs (R1-Distill 1.5B->7B, Qwen3 1.7B->4B).
    Narrow the claim to ''in our tested teacher-student pairs'' to match the evidence
    scope.'
artifact_hash: fe03c20c23e17e66c41241fcf88a5ad32b5f8c89483ca27ec649ff3d3b355988
artifact_path: projects/PROJ-1059-weak-to-strong-generalization-via-direct/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T02:38:58.312749Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method for weak-to-strong generalization, but the rhetoric in the abstract, introduction, and conclusion occasionally exceeds the specific scope of the experimental evidence provided.

The primary issue lies in the generalization of specific efficiency and performance gains. The abstract highlights a specific result: "boosts Qwen3-1.7B from 48.3% to 58.3% on AIME 2024 in just 4 hours." While this result is accurate for the JustRL teacher pair (Table 1a), the phrasing presents it as a headline capability of the method without immediately qualifying that this specific efficiency profile is tied to the specific teacher-student configuration tested. The method's performance and speed are shown to be sensitive to the teacher pair and KL coefficient (Section 5.4), so presenting a single data point as the definitive "efficiency" of the method is slightly overreaching.

Similarly, the Introduction compares the method's efficiency to "Polaris" running for "at least a week." This is a comparison to an external report rather than a controlled, internal experiment where the authors ran direct RL on the same hardware for the same duration. While the direction of the argument is sound, framing it as a direct "comparable" result without the authors' own matched baseline on the same infrastructure risks overstating the empirical basis of the efficiency claim.

Finally, the Conclusion states the method "outperforms step-matched direct RL." The evidence for this (Section 4.2) is limited to two specific transfer scenarios (R1-Distill 1.5B->7B and Qwen3 1.7B->4B). The claim is presented as a general property of the method, whereas the data only supports it for the specific model families and scales tested. The paper would be more rigorous by explicitly limiting this claim to the tested regimes or acknowledging that the superiority is demonstrated within the specific experimental bounds.

These are primarily issues of scope and framing rather than factual errors. The results are strong, but the language should be tightened to ensure the claims track precisely with the boundaries of the experiments performed.
