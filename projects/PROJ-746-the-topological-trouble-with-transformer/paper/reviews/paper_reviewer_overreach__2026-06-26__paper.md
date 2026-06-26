---
action_items:
- id: 5f971cefc12f
  severity: writing
  text: Qualify theoretical claims in Abstract and Intro to distinguish between theoretical
    bounds and practical limitations.
- id: 666fe67e8b90
  severity: science
  text: Replace anecdotal evidence (Gemini examples) with broader empirical analysis
    or soften claims about 'fundamental limitations'.
- id: 66f14b928960
  severity: writing
  text: Verify or soften the claim regarding empty taxonomy cells in Section 3.
- id: af5ce98949ff
  severity: writing
  text: Reframe prescriptive conclusions to recommendations rather than necessities.
artifact_hash: 924b893a4650c3044c8ebca795788f41846a7a72e06ec4cbf52905fb73429333
artifact_path: projects/PROJ-746-the-topological-trouble-with-transformer/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-26T10:26:52.976955Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling theoretical argument regarding the limitations of feedforward transformers in state tracking. However, there is significant overreach in presenting theoretical bounds as practical inevitabilities without sufficient empirical validation or qualification.

1.  **Abstract & Introduction:** The claim that feedforward models "ultimately exhaust the model's depth" (Abstract) is a strong theoretical assertion. While supported by Figure 1, this is a schematic, not empirical proof. The language should be qualified to reflect that this is a theoretical limitation under specific assumptions, not a proven practical failure mode for all tasks.
2.  **Section 2 (State Tracking):** The argument relies heavily on anecdotal examples from Gemini models (e.g., the "number guessing" and "bank" examples). Generalizing these specific failures to a "fundamental limitation of the core architecture" (Footnote 2) is overreach. Newer models or different training regimes might mitigate these issues. The distinction between architectural limits and training/data limits is blurred.
3.  **Section 3 (Taxonomy):** The claim "We have not succeeded in identifying any examples of work that lies in the empty cells of the taxonomy" is a negative claim that is difficult to verify and risks being incorrect. This should be softened to "We are unaware of..." or similar.
4.  **Conclusions:** The statement "The next generation of foundation models must do more..." is prescriptive and speculative. It should be framed as a recommendation based on the theoretical analysis rather than a necessity.

Overall, the paper is a valuable position piece but needs to temper its claims to distinguish between theoretical expressivity bounds and observed empirical behaviors. The reliance on specific model failures to argue for architectural necessity requires stronger evidence or more cautious language.
