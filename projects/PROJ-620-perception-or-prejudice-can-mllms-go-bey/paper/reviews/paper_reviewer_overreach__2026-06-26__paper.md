---
action_items:
- id: 574dbc83404c
  severity: science
  text: Temper the claim '51% of correct ratings are not grounded' in Abstract/Intro
    to acknowledge MCQ limitations (Appendix E).
- id: 4df4c142ef16
  severity: writing
  text: Align 'Reasoning-capable models dominate' claim in Abstract/Intro with 'observational/confounded'
    language in Appendix H.
- id: 52de3d5e996d
  severity: writing
  text: Clarify EU AI Act claim regarding 'per-prediction explainability' to avoid
    over-interpreting the regulation (Intro).
artifact_hash: 37d4da743146174451c6b81c250d33af63eaf988a8502062dfca5a6325ae068a
artifact_path: projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-26T01:03:33.546861Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes a compelling case for the "Prejudice Gap," but several claims in the Abstract and Introduction overreach the evidence provided by the MCQ-based grounding metric.

1. **Grounding Proxy vs. Fact:** The Abstract states "51% of correct ratings are not grounded in retrieved cues" (Abstract, line 12). This treats the T3 MCQ failure as definitive proof of ungrounded reasoning. However, Appendix E (Ethics) admits "a high Prejudice Rate may in part reflect MCQ-design choices." The main text should qualify this claim (e.g., "51% of correct ratings fail to align with *MCQ-grounded* cues") to avoid implying the model's internal state is known with certainty. Without this, the "Prejudice Gap" is conflated with "MCQ Failure Rate."

2. **Reasoning Capability Claim:** The Abstract claims "recent reasoning-capable MLLMs dominate the upper leaderboard" (Abstract, line 18). Appendix H explicitly labels this analysis "observational" and "confounded" by model age/size. The main text should reflect this uncertainty (e.g., "reasoning-capable variants *tend* to lead") to match the appendix's caution. Presenting a confounded correlation as a primary finding risks misleading readers about the causal drivers of performance.

3. **Regulatory Claim:** The Introduction cites the EU AI Act as mandating "an explainable evidence trail for each deployed prediction" (Intro, line 35). This is a strong interpretation of the regulation; the Act focuses on risk management systems rather than per-prediction explainability in all contexts. Precision here would strengthen the justification for the task without overstating legal requirements.

These are primarily framing issues. The core data supports the gap, but the language implies more certainty than the methodology allows. Adjusting the Abstract and Introduction to align with the Appendix's caveats will ensure the claims are robustly supported.
