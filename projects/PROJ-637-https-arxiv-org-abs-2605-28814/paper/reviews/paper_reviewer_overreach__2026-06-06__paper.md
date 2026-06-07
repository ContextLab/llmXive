---
action_items:
- id: 5d64986d8ca8
  severity: science
  text: Temper theoretical claims in Abstract and Section 3 to reflect that assumptions
    (e.g., sub-goal independence) are not empirically validated on the models used.
- id: b95399fd677c
  severity: writing
  text: Revise cost analysis claims in Section 4.3; characterize the ~40% API cost
    increase more accurately rather than as 'modest'.
artifact_hash: d74e7ce3cbfe7aea4f0dad766af5b0e41093c35f05a067517ae8e48026ef85b2
artifact_path: projects/PROJ-637-https-arxiv-org-abs-2605-28814/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T15:36:41.459651Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents strong theoretical motivations in Section 3 and Appendix A, but these claims extend beyond the empirical validation provided. Specifically, Theorem 1 (Shell Confinement) and Theorem 2 (Exponential Advantage) rely on assumptions (Assumptions 1-3 in Appendix A) that are asserted to be "naturally satisfied in practice" but are not empirically verified on the models used in Section 4. For instance, Assumption 3 (Linear block total correlation) and the independence assumption in Theorem 2 are critical for the "exponential advantage" claim. In complex reasoning tasks (e.g., MuSiQue), sub-goals are typically dependent, violating the independence assumption required for the $O(p_{\min}^{-1}\log(m/\delta))$ bound. Claiming the theory explains the empirical gains without verifying these assumptions on the actual policy distributions constitutes overreach regarding the theoretical justification of the method's success.

Additionally, the cost analysis in Table 5 and Section 4.3 claims "modest additional API costs" for the inference benchmarks. However, for the Heilbronn task, \ours\ costs \$13.7 vs ShinkaEvolve's \$11.5 (approx 19% increase), and for Circle Packing (Square), \$18.6 vs \$13.0 (approx 43% increase). Characterizing a ~40% cost increase as "modest" while highlighting performance gains risks overclaiming efficiency, especially given the sensitivity of open-problem solving to compute budgets.

The limitations section (Appendix) acknowledges weak model constraints but does not address the theoretical assumption validity. To mitigate overreach, the authors should either empirically validate the theoretical assumptions on their models or temper the claims to reflect that the theory provides *motivation* rather than *proof* of the observed gains. The abstract should also be revised to avoid implying the theory *proves* the empirical outcomes without qualification.
