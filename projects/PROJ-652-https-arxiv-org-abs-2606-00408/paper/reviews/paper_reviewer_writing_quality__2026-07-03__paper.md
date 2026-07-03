---
action_items:
- id: 435f2a38572e
  severity: writing
  text: In Section 5.1 (Trade-Off), the phrase 'broken queries (correct -> wrong)'
    is ambiguous. Clarify that this refers to queries that were correct without masking
    but became incorrect with masking.
- id: ef5d17025723
  severity: writing
  text: Section 5.2.1 states 'Reasoning absorbs 53.7% of attention budget vs 25.6%
    for observations'. Ensure the sum of these percentages is explained or that other
    attention targets (e.g., system prompt, tool calls) are accounted for to avoid
    confusion.
- id: b4ef4fcdf4e3
  severity: writing
  text: The caption for Figure 1 (teaser) uses 'Whereas' to start a sentence ('Whereas,
    the retriever bottleneck...'). This is grammatically awkward; rephrase to 'In
    contrast, the retriever bottleneck...' or similar.
- id: 90e5dd303d50
  severity: writing
  text: In Table 1, the column header '$\Delta$ calls/q$^\downarrow$' uses a down
    arrow to indicate lower is better, but the values are positive increases. Clarify
    if the arrow refers to the desirability of the metric or the direction of change,
    as the current notation is slightly confusing.
artifact_hash: 0662f086c971957827b984215e812ef5eb19c982637f2c1511efa72d77075eda
artifact_path: projects/PROJ-652-https-arxiv-org-abs-2606-00408/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T02:29:51.482909Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_writing_quality
score: 0.0
verdict: minor_revision
---

The manuscript is generally well-written, with a clear narrative flow and precise technical terminology appropriate for the field. The abstract effectively summarizes the core findings, and the introduction sets up the research question clearly. However, there are a few areas where clarity and grammatical precision can be improved to ensure the reader fully grasps the nuances of the results.

First, in Section 5.1 ("The Trade-Off"), the description of "broken queries" as "(correct -> wrong)" is slightly ambiguous without immediate context. While the surrounding text explains the concept, explicitly stating that this refers to queries where the baseline (No-CM) was correct but the masked version failed would prevent any momentary confusion for the reader.

Second, in Section 5.2.1 ("Attention Evidence"), the claim that "Reasoning absorbs 53.7% of attention budget vs 25.6% for observations" leaves a significant portion of the attention budget unaccounted for. While this is likely due to attention on system prompts, tool calls, or other tokens, the text does not explicitly mention this. A brief clarification or a note that the remaining percentage is distributed among other components would improve the completeness of the statement.

Third, the caption for Figure 1 (teaser) contains a grammatical awkwardness: "Whereas, the retriever bottleneck weakens the baseline signal..." The use of "Whereas" to start a sentence in this manner is non-standard. Rephrasing to "In contrast, the retriever bottleneck..." or integrating the clause into the previous sentence would improve readability.

Finally, in Table 1, the column header "$\Delta$ calls/q$^\downarrow$" uses a down arrow to suggest that lower values are better. However, the values listed are positive increases in tool calls. While the context implies that fewer extra calls are preferable, the notation could be slightly misleading. Clarifying that the arrow indicates the *desirability* of the metric (i.e., lower is better) rather than the direction of the change would eliminate potential ambiguity.

Overall, the paper is strong, and these minor revisions will further polish the presentation.
