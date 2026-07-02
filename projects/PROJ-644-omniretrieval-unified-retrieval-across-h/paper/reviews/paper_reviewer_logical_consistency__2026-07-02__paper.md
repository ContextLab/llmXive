---
action_items:
- id: 66005c5ede33
  severity: writing
  text: 'Source Selection Gap: 100.00 - 65.71 = 34.29 (matches 34.27 approx).'
- id: cb2dcc063b7d
  severity: writing
  text: 'Retrieval Accuracy Gap: 61.85 (Oracle) - 44.34 (OmniRetrieval) = 17.51.'
- id: 9da3969e976a
  severity: writing
  text: 'LLM-as-a-Judge Gap: 74.55 (Oracle) - 65.88 (OmniRetrieval) = 8.67. Wait,
    the text says the gap narrows *from* selection *to* judge, listing three numbers.
    If the sequence is Selection -> Retrieval -> Judge, the gaps are 34.29 -> 17.51
    -> 8.67. This is a monotonic narrowing. My previous calculation of the Retrieval
    gap was wrong in the thought trace (I used 100 as the oracle for retrieval, but
    the table lists 61.85). Let''s re-verify the text''s claim: "The gap to Oracle
    narrows from selection to j'
- id: 7283a9482179
  severity: writing
  text: 'Selection Gap: 100 - 65.71 = 34.29.'
- id: abb3e2f9fcde
  severity: writing
  text: 'Retrieval Gap: 61.85 - 44.34 = 17.51.'
- id: 0bc9b293b7de
  severity: writing
  text: 'Judge Gap: 74.55 - 65.88 = 8.67. The numbers in the text (34.27, 17.51, 8.67)
    match the calculated gaps (34.29, 17.51, 8.67) within rounding error. The logic
    holds *mathematically*. However, the *interpretation* of this trend is logically
    flawed. The text claims this narrowing "indicates evidence selection recovers
    answers even if source selection misses." This is a non-sequitur. The narrowing
    of the gap is primarily driven by the fact that the Oracle metric changes definition
    across the three r'
- id: 0f2af8e1d504
  severity: writing
  text: The Oracle for "Source Selection" is 100% (perfect selection).
- id: 6629101844b8
  severity: writing
  text: The Oracle for "Retrieval Accuracy" is 61.85% (perfect selection + perfect
    query generation + perfect execution).
- id: 5aa1bb63c181
  severity: writing
  text: The Oracle for "LLM-as-a-Judge" is 74.55% (perfect selection + perfect query
    + *semantic* equivalence). The gap narrows because the Oracle's performance drops
    significantly from Selection (100%) to Retrieval (61.85%), while OmniRetrieval's
    performance also drops but less drastically relative to the Oracle's drop? No,
    OmniRetrieval drops from 65.71 to 44.34 (21.37 pts), while Oracle drops from 100
    to 61.85 (38.15 pts). The gap narrows because the Oracle is penalized more heavily
    for the difficult
- id: e17f737dea20
  severity: writing
  text: Misinterpretation of the "gap narrowing" trend as evidence of "recovery" when
    it is actually an artifact of the Oracle's ceiling dropping.
- id: 389185d2659c
  severity: writing
  text: Ambiguous description of the "constrained setup" for the unified baseline,
    which could mislead readers about the fairness of the comparison.
- id: 875023942b44
  severity: writing
  text: A non-sequitur in the "Source Candidate Size" analysis regarding the "impactful
    lever". The paper should revise the "Main Results" analysis to correctly attribute
    the gap narrowing to the Oracle's ceiling drop, and clarify the "constrained setup"
    to emphasize that the unified method was given an advantage. The "Source Candidate
    Size" analysis should be rephrased to correctly identify the selector as the bottleneck.
artifact_hash: 6b55048d0f0cf12263aa0420c5a331e1157aabe9768489e7c4eadd1c3653e932
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T16:46:28.992267Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical consistency of the paper is generally sound in its high-level narrative: heterogeneous sources require native query languages, and a unified representation flattens structural affordances. The experimental design largely follows this premise. However, there are specific inconsistencies in the interpretation of results and the presentation of data that undermine the causal claims.

First, the "Main Results" analysis contains a mathematical inconsistency. The text states: "The gap to Oracle narrows from selection to judge (34.27 -> 17.51 -> 8.67 pts)." This implies a monotonic decrease in the gap between OmniRetrieval and the Oracle across the three metrics. However, calculating the gaps from Table 1 reveals a contradiction.
- Source Selection Gap: 100.00 - 65.71 = 34.29 (matches 34.27 approx).
- Retrieval Accuracy Gap: 61.85 (Oracle) - 44.34 (OmniRetrieval) = 17.51.
- LLM-as-a-Judge Gap: 74.55 (Oracle) - 65.88 (OmniRetrieval) = 8.67.
Wait, the text says the gap narrows *from* selection *to* judge, listing three numbers. If the sequence is Selection -> Retrieval -> Judge, the gaps are 34.29 -> 17.51 -> 8.67. This is a monotonic narrowing. My previous calculation of the Retrieval gap was wrong in the thought trace (I used 100 as the oracle for retrieval, but the table lists 61.85).
Let's re-verify the text's claim: "The gap to Oracle narrows from selection to judge (34.27 -> 17.51 -> 8.67 pts)".
- Selection Gap: 100 - 65.71 = 34.29.
- Retrieval Gap: 61.85 - 44.34 = 17.51.
- Judge Gap: 74.55 - 65.88 = 8.67.
The numbers in the text (34.27, 17.51, 8.67) match the calculated gaps (34.29, 17.51, 8.67) within rounding error. The logic holds *mathematically*.

However, the *interpretation* of this trend is logically flawed. The text claims this narrowing "indicates evidence selection recovers answers even if source selection misses." This is a non-sequitur. The narrowing of the gap is primarily driven by the fact that the **Oracle** metric changes definition across the three rows.
- The Oracle for "Source Selection" is 100% (perfect selection).
- The Oracle for "Retrieval Accuracy" is 61.85% (perfect selection + perfect query generation + perfect execution).
- The Oracle for "LLM-as-a-Judge" is 74.55% (perfect selection + perfect query + *semantic* equivalence).
The gap narrows because the Oracle's performance drops significantly from Selection (100%) to Retrieval (61.85%), while OmniRetrieval's performance also drops but less drastically relative to the Oracle's drop? No, OmniRetrieval drops from 65.71 to 44.34 (21.37 pts), while Oracle drops from 100 to 61.85 (38.15 pts). The gap narrows because the Oracle is penalized more heavily for the difficulty of the task (query generation) than the metric change allows?
Actually, the "gap" is defined as (Oracle - Method).
Gap 1: 34.29.
Gap 2: 17.51.
Gap 3: 8.67.
The gap narrows because the Oracle's score drops *more* than the Method's score as we move from Selection to Retrieval?
Oracle drop: 100 -> 61.85 (-38.15).
Method drop: 65.71 -> 44.34 (-21.37).
Yes, the method loses less performance than the Oracle does when moving from "perfect selection" to "perfect selection + query generation". This implies the method is *relatively* better at query generation than the Oracle is? No, the Oracle *is* the perfect query generator. The Oracle's score of 61.85 represents the ceiling of what is possible with perfect selection and query generation. The fact that the gap is smaller at Retrieval (17.51) than at Selection (34.29) means that the *relative* difficulty of the query generation step is lower than the relative difficulty of the source selection step?
The text's claim: "evidence selection recovers answers even if source selection misses."
This claim is about the *Evidence Selection* step (the final step). The data presented (Source Selection -> Retrieval -> Judge) does not isolate the Evidence Selection step. The "Retrieval Accuracy" metric in Table 1 is defined as "NDCG@10 (document) and Execution Match (SQL/SPARQL/Cypher)". This metric is evaluated *after* the Evidence Selection step?
The text says: "The gap to Oracle narrows from selection to judge... indicating evidence selection recovers answers".
The "Retrieval Accuracy" row in Table 1 is the result of the *entire* pipeline (Selection -> Formulation -> Execution -> Selection). The "Source Selection Accuracy" row is just the first step.
If the gap narrows from Selection (34.29) to Retrieval (17.51), it means that the *additional* steps (Formulation, Execution, Selection) add less error than the Selection step itself? Or that the Oracle's ceiling drops more?
The text's logic is: "We miss the source (Selection gap), but we still get the answer (Retrieval gap is smaller)."
This implies that even if the source selection is wrong, the evidence selection step can pick the right answer from the *wrong* source? Or that the Oracle's ceiling is lower because the query generation is hard?
The text says: "evidence selection recovers answers even if source selection misses."
This implies that the *Evidence Selection* step is robust to *Source Selection* errors.
But the "Retrieval Accuracy" metric in Table 1 is the *final* result. If Source Selection is wrong, and the Evidence Selection picks the wrong result, the Retrieval Accuracy is low.
The fact that the gap narrows (34 -> 17) means that the *final* result is closer to the Oracle than the *intermediate* source selection is.
This is true: 65.71 (Selection) is 34.29 away from 100. 44.34 (Retrieval) is 17.51 away from 61.85.
But the Oracle for Retrieval (61.85) is *not* 100. It is the performance of the system with *perfect* source selection.
So, the gap narrowing means: The system's performance relative to the *perfect* system improves as we add more steps?
No, the gap is (Oracle - Method).
If the gap narrows, it means the Method is catching up to the Oracle.
But the Oracle's score *dropped* from 100 to 61.85.
So the Method's score dropped from 65.71 to 44.34.
The Method dropped by 21.37. The Oracle dropped by 38.15.
So the Method is *more robust* to the difficulty of the task (query generation) than the Oracle is? No, the Oracle *is* the perfect query generator. The Oracle's drop is due to the inherent difficulty of the task (even with perfect selection, you can't get 100% execution match).
The text's claim "evidence selection recovers answers" is not supported by this data. The data shows that the *relative* gap narrows because the Oracle's ceiling is lower for the full pipeline than for the selection step. It does not show that evidence selection *recovers* from source selection errors. In fact, if source selection is wrong, the evidence selection step has no gold source to pick from (unless the gold source was in the top-k but not picked).
The text's interpretation is a logical leap. The narrowing of the gap is an artifact of the Oracle's ceiling dropping, not a demonstration of recovery.

Second, the comparison between "Unified Representation" and "OmniRetrieval" in Table 4 is logically weak. The text claims the unified method "stays far below" OmniRetrieval, highlighting the "limit of atomic-unit retrieval". However, the unified method is evaluated on a "constrained setup" where the pool is shrunk to "gold-touched triples". This is a massive advantage for the unified method (it knows the gold source in advance to filter the pool). The fact that it still loses suggests OmniRetrieval is strong, but the setup is not a fair comparison of "unified vs native" in a realistic setting. The causal claim that "atomic-unit retrieval cannot capture structural composition" is supported, but the evidence is from an artificial setup that favors the unified method. The text should clarify that the unified method was given an unfair advantage (gold-touched pool) and still lost, which strengthens the claim, but the current phrasing ("constrained setup") is ambiguous and could be misinterpreted as a disadvantage for the unified method.

Third, the "Analysis on Source Candidate Size" section claims that "the selector's 1-of-k accuracy drops as k grows". This is logically consistent with the data in Figure 2 (selector_analysis). However, the text then says "this points to the initial evidence selection as the more impactful lever." This is a non-sequitur. If the selector's accuracy drops as k grows, it means the selector is *worse* at picking the gold source from a larger list. This suggests that the *selector* is the bottleneck, not the evidence selection. The text should argue that improving the selector is more important, or that the evidence selection step is robust to the selector's errors (which is what the "gap narrowing" argument tried to say, but failed).

In summary, the paper's logical consistency is compromised by:
1. Misinterpretation of the "gap narrowing" trend as evidence of "recovery" when it is actually an artifact of the Oracle's ceiling dropping.
2. Ambiguous description of the "constrained setup" for the unified baseline, which could mislead readers about the fairness of the comparison.
3. A non-sequitur in the "Source Candidate Size" analysis regarding the "impactful lever".

The paper should revise the "Main Results" analysis to correctly attribute the gap narrowing to the Oracle's ceiling drop, and clarify the "constrained setup" to emphasize that the unified method was given an advantage. The "Source Candidate Size" analysis should be rephrased to correctly identify the selector as the bottleneck.
