---
action_items:
- id: e85759b7070a
  severity: writing
  text: Temper the claim in the Abstract and Experiment section that model performance
    drops expose a 'persistent gap in robust computer automation.' This conflates
    metric strictness with capability; clarify that stricter verification naturally
    lowers pass rates compared to looser benchmarks.
- id: aab4cf1d0d16
  severity: writing
  text: Qualify the Conclusion's claim that the framework preserves 'the diversity
    and realism of real software workflows.' Acknowledge that visually-grounded workflows
    (excluded per Appendix/limitations.tex) are part of realistic workflows but omitted
    for verifiability.
artifact_hash: 0d09bbe6836d7c3ba38dc0386a722fbaec7b727145cadfcb8e187e60eeb63fee
artifact_path: projects/PROJ-607-https-arxiv-org-abs-2605-19769/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-12T11:19:40.912235Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper generally demonstrates good restraint in its limitations section (`Appendix/limitations.tex`), explicitly acknowledging that 17 generated tasks required visual judgments and were excluded from the main benchmark because they could not be fully reduced to programmatic checks. This honesty mitigates overreach regarding the completeness of the verification stack. However, there is mild overreach in the interpretation of comparative model performance.

In the Abstract and Experiment section (lines 28-30, 148-150), the authors state that open-source models "exhibit sharp drops... exposing a persistent gap in robust computer automation." This phrasing attributes the performance drop primarily to agent capability gaps. However, the drop (e.g., GUI-OWL from 52.3% to 5.7%) likely reflects the stricter, state-grounded verification of OpenComputer compared to OSWorld-Verified, which may rely on looser or LLM-based criteria. While the paper argues verifiers are more accurate, claiming the drop exposes a "persistent gap" in automation conflates metric sensitivity with capability deficits. The conclusion should temper this language to acknowledge that stricter verification naturally lowers pass rates.

Furthermore, the Conclusion (lines 240-242) claims the framework preserves "the diversity and realism of real software workflows." This slightly overclaims given the exclusion of visually-grounded tasks described in `Appendix/limitations.tex`. Real desktop workflows often involve visual alignment (e.g., Draw.io arrows) which the benchmark explicitly excludes. The claim should be qualified to "realism within the bounds of executable verification" to avoid implying comprehensive coverage of all realistic workflows. Finally, the self-evolving verification claim (Section 3.1.2) suggests the layer "improves verifier reliability," supported by an 89.4% repair rate on 76 cases. While supported, the generalization that this solves verifier brittleness broadly should be tempered, as 8 cases remained unresolved within the budget.
