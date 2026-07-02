---
action_items:
- id: b579cc0c2fa9
  severity: science
  text: Section 4.1 claims Doubao hangs up after ~5 mins and Gemini after ~2m15s.
    Cite specific app version docs or logs proving these exact timeouts, as they are
    central to the 'Long-horizon memory' failure argument.
- id: eac5e4445aa0
  severity: writing
  text: Section 4.1 defines 'win rate' as 'fraction of comparisons it wins' but includes
    ties in the denominator (summing to 100%). Explicitly state that ties are excluded
    from the 'win' count but included in the total denominator to avoid confusion
    with standard win-tie-loss metrics.
- id: 5ede186ae011
  severity: writing
  text: Section 4.2 attributes Doubao's commentary wins to 'larger model scale' and
    'quality advantage'. Report the split quality vs. timing scores for this scenario
    to verify the claim that quality offset timing weaknesses.
artifact_hash: 5266e7279b96ba8c30af6614b2b08bda02ec2220e0d4769bb56ba9df667b0fe5
artifact_path: projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T10:40:15.449650Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several specific factual claims regarding evaluation metrics and baseline behaviors that require precise verification.

In Section 4.1, the authors assert that Doubao's video-call feature "automatically hangs up after about five minutes" and Gemini's after "around two minutes fifteen seconds." These specific time limits are used to explain why the baselines failed in the "Long-horizon memory" scenario. This is a verifiable product constraint that must be supported by a citation to the specific app version's documentation, a release note, or a reproducible log included in the appendix. Without this evidence, the claim that the baselines were structurally unable to respond is an assertion rather than a verified fact.

Regarding the statistical reporting in Section 4.1 and the results tables, the definition of "win rate" requires clarification. The text states, "a tie counts as neither a win nor a loss," and defines the win rate as the "fraction of comparisons it wins." However, the reported percentages (e.g., 77.6% wins, 17.2% ties, 5.2% losses) sum to exactly 100%, implying the denominator is the *total* number of cases (58). Standard "win rate" metrics in pairwise comparisons often exclude ties from the denominator (Wins / (Wins + Losses)). While the authors' calculation (Wins / Total) is mathematically consistent with the numbers provided (45/58 ≈ 77.6%), the phrasing is ambiguous. The protocol should explicitly state that the denominator includes ties to prevent misinterpretation by readers familiar with standard win-tie-loss reporting.

Finally, in Section 4.2, the authors claim Doubao's advantage in "live commentary" stems from its "larger model scale" providing a "quality advantage" that offsets its timing weaknesses. The text implies that the quality scores were higher for Doubao in these specific cases. To support this causal claim, the paper should briefly report the split quality versus timing scores for the "Live commentary" scenario. Without this breakdown, the attribution of the win to "quality" rather than a scoring artifact remains an inference.
