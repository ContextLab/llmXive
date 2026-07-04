---
action_items:
- id: f69d7a59bea4
  severity: writing
  text: 'Title and Abstract claim ''Reaching Trillion-Parameter Performance'' and
    ''match the performance of 1T models.'' Table 1 shows the model is outperformed
    by 1T models (GPT-5.5, Kimi-K2.6) on 6 of 14 benchmarks (e.g., MLE-Bench-Lite:
    43.9 vs 72.7; SciCode: 44.3 vs 56.1). Replace ''match'' with ''compete with on
    specific long-horizon benchmarks'' and qualify the title to reflect performance
    parity only on a subset of tasks, not a general equivalence.'
- id: 6180ea9175ac
  severity: writing
  text: Abstract states the method 'reaches trillion-parameter-level performance'
    based on results from a single 35B model family (Qwen3.5 derivatives). The conclusion
    implies this scaling path is a general solution for 'any' agent. Add a limitation
    explicitly stating that the 'trillion-parameter' claim is specific to the tested
    benchmarks and model architecture, and that generalization to other domains or
    model families remains untested.
- id: 8dfc734dc770
  severity: writing
  text: The Introduction and Abstract frame the work as a 'practical path' to replace
    parameter scaling. However, the results show the method fails to close the gap
    on engineering tasks (MLE-Bench) where parameter scaling clearly wins. The narrative
    omits this failure mode. Add a sentence in the Limitations section acknowledging
    that for tasks requiring deep internal knowledge or complex engineering workflows,
    parameter scaling still outperforms horizon scaling in the current regime.
artifact_hash: 7516b8f83d13246ad4b3942c0933109bd30bd10fff09ade393f2aa0326228eae
artifact_path: projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T01:29:03.772164Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes a bold rhetorical claim in its title and abstract: that a 35B model can "reach trillion-parameter performance" and "match" 1T models. While the results demonstrate impressive gains on specific long-horizon benchmarks (e.g., SEAL-0, HiPhO, FS-O), the evidence does not support a universal claim of parity. Table 1 explicitly shows the model trailing behind 1T baselines (GPT-5.5, Kimi-K2.6) on significant portions of the evaluation suite, particularly in engineering tasks (MLE-Bench-Lite: 43.9 vs 72.7) and general coding (SciCode: 44.3 vs 56.1).

The rhetoric of "reaching" or "matching" trillion-parameter performance suggests a general equivalence that the data does not support. The paper successfully argues that horizon scaling is a viable *alternative* for specific long-horizon, tool-use, and reasoning tasks, but it overgeneralizes this to imply a broader performance equivalence. The conclusion and abstract should be narrowed to reflect that the model matches 1T performance *on specific long-horizon benchmarks* rather than generally.

Furthermore, the paper frames the "failure" on engineering tasks as a specific limitation of the current training recipe ("MLE optimization is not a static problem-solving task") rather than a fundamental boundary of the horizon-scaling approach compared to parameter scaling. A more honest assessment would acknowledge that for tasks requiring deep internalized knowledge or complex, multi-stage engineering workflows, parameter scaling currently remains superior, and the "trillion-parameter" claim is conditional on the task type. The limitations section is present but too brief to adequately contextualize these significant performance gaps against the headline claims.
