---
action_items:
- id: 82c192463f82
  severity: writing
  text: In Section 5 (Experiments), the text states 'GPT-5.4 and Qwen3.5-397B tie
    at ~47-50% win rate' in the Duel setting. However, Table 2 shows GPT-5.4 at 50.0%
    and Qwen3.5-397B at 46.7%. The text should clarify that these are distinct values
    or adjust the phrasing to avoid implying a statistical tie where the data shows
    a difference.
- id: ab12eb4bcac8
  severity: writing
  text: In Section 5.2 (Diagnostic Analysis), the sentence 'Text-only solves Matching
    Pairs (100%) and 3D Maze (GS ~70%)' is ambiguous. It is unclear if 'solves' implies
    perfect performance or merely high performance. Given the context of '100%', it
    likely means perfect, but 'GS ~70%' is not a 'solution' in the same sense. Rephrase
    for precision, e.g., 'Text-only inputs achieve 100% on Matching Pairs and ~70%
    GS on 3D Maze.'
- id: eb8f34effa48
  severity: writing
  text: In the Appendix (More Analysis), the phrase 'Tabs.~\ref{tab:rq1_board_size_match}
    and~\ref{tab:rq1_board_size_maze} report the per-size numbers' uses 'Tabs.' as
    an abbreviation for 'Tables'. While common in some contexts, standard academic
    prose usually spells out 'Tables' or uses 'Table' if referring to a single one.
    Ensure consistency with the main text style, which spells out 'Table' in captions
    and text.
artifact_hash: 2dace62b4db749210548d655003e141d33d2469d6916df6eba8fda5f05abc5c8
artifact_path: projects/PROJ-742-beyond-the-current-observation-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:43:52.646660Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_writing_quality
score: 0.0
verdict: minor_revision
---

The manuscript is generally well-written, with a clear structure and logical flow that effectively communicates the benchmark design and experimental results. The abstract and introduction successfully set the stage for the problem of non-Markov evaluation in MLLMs. However, there are specific instances where precision in language and data reporting could be improved to prevent minor ambiguities for the reader.

In Section 5.1, the summary of the Duel results states that GPT-5.4 and Qwen3.5-397B "tie at ~47-50% win rate." While the range is technically correct, the phrasing "tie" suggests statistical equivalence, whereas Table 2 explicitly lists 50.0% for GPT-5.4 and 46.7% for Qwen3.5-397B. A more precise phrasing, such as "perform similarly with win rates of 50.0% and 46.7% respectively," would better reflect the data without implying a formal tie.

Additionally, in Section 5.2, the claim that "Text-only solves Matching Pairs (100%) and 3D Maze (GS ~70%)" conflates two different performance metrics under the verb "solves." While 100% implies a complete solution, a Game Score of ~70% does not necessarily constitute a "solution" in the same absolute sense. Clarifying this distinction (e.g., "achieves perfect scores on Matching Pairs and ~70% GS on 3D Maze") would enhance the accuracy of the claim.

Finally, the Appendix uses the abbreviation "Tabs." when referring to multiple tables. For consistency with the main body of the paper, which spells out "Table" in text and captions, the authors should consider using the full word "Tables" to maintain a uniform academic tone throughout the document. These are minor stylistic and precision issues that do not detract significantly from the overall readability but are worth addressing for a polished final version.
