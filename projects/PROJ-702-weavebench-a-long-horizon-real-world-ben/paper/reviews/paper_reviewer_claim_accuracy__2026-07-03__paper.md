---
action_items:
- id: 0b9b091adc7b
  severity: writing
  text: Section 4.2 claims a '+31.6pp' hybrid gain for WeaveBench generally, but this
    figure is specific to Claude Opus 4.7 (35.1% vs 3.5%). GPT-5.5 shows ~30.7pp.
    Clarify if this is a model-specific or average gain to avoid overgeneralization.
- id: d50dc869f60c
  severity: writing
  text: Section 4.3 states the judge removes '10.3 to 20.2' points across four GPT
    backbones. While 20.2pp for GPT-5.5 is shown, the text lacks the specific inflated
    scores for the other three backbones needed to verify the 10.3pp lower bound.
    List these scores.
- id: d4364db7f2e2
  severity: writing
  text: Appendix C claims CLI and Vision are 'on par' (79.1% vs 77.3%) and CLI takes
    'half the steps' (14.3 vs 29.0). Qualify 'on par' as 'statistically comparable'
    and 'half' as 'approximately half' to maintain numerical precision.
artifact_hash: fe47fd5151ed0fa01e324bf6a3d1eb3486f522739d02266159e873e4cf63e576
artifact_path: projects/PROJ-702-weavebench-a-long-horizon-real-world-ben/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T06:05:49.743538Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents strong quantitative claims, but several narrative statements overgeneralize specific model results or omit necessary data points for verification.

In Section 4.2, the text asserts that "the hybrid gain is +31.6pp" as a general property of WeaveBench. This figure is derived exclusively from the Claude Opus 4.7 results (35.1% Hybrid vs 3.5% CLI). However, Table 4.1 shows GPT-5.5 achieves a gain of 30.7pp (33.3% vs 2.6%). Presenting the single best model's gain as the benchmark's general characteristic risks misleading readers about the average difficulty or the consistency of the hybrid requirement across different architectures. The authors should clarify that this figure represents the gain for the strongest model or provide an average across the tested backbones.

In Section 4.3, the claim that the trajectory-aware judge removes "between 10.3 and 20.2 PassRate points across the four GPT backbones" is difficult to verify from the provided text. While the 20.2pp drop for GPT-5.5 (from 53.5% to 33.3%) is explicitly supported by Table 4.2 and Figure 4.2, the text does not list the corresponding "outcome-only" inflated scores for GPT-5.4, 5.3, and 5.2. Without these specific numbers, the lower bound of 10.3pp remains an unsupported assertion in the narrative. The authors should include the specific inflated scores for the other backbones in the text or a referenced table to substantiate the claimed range.

Finally, in Appendix C, the statement that CLI and Vision channels are "on par" (79.1% vs 77.3%) and that CLI takes "half the steps" (14.3 vs 29.0) lacks the precision expected in a benchmark paper. While 1.8% is a small difference, "on par" is a qualitative judgment that should be qualified (e.g., "statistically comparable") or supported by a significance test. Similarly, 14.3 is approximately 49% of 29.0; phrasing this as "half" is a slight exaggeration. Using "approximately half" and "statistically comparable" would align the prose more rigorously with the data.
