---
action_items:
- id: b2054564dcaa
  severity: writing
  text: The paper makes several claims that extend slightly beyond the immediate evidence
    provided, particularly regarding the generalizability of scaling effects and the
    robustness of the proposed method's improvements. First, the Introduction states
    that "larger or more capable models sometimes perform worse at timely abstention."
    While the results section (Section 6.2) does show that Qwen3-235B has lower timely
    recall than smaller Qwen variants in specific instances, the paper does not provide
    a stat
artifact_hash: 38d0e8e4fb458c680aadb1d4bcdffd2c4f641f3bec33db525a174585bed1f06b
artifact_path: projects/PROJ-808-agentic-abstention-do-agents-know-when-t/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T01:29:04.060152Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend slightly beyond the immediate evidence provided, particularly regarding the generalizability of scaling effects and the robustness of the proposed method's improvements.

First, the Introduction states that "larger or more capable models sometimes perform worse at timely abstention." While the results section (Section 6.2) does show that Qwen3-235B has lower timely recall than smaller Qwen variants in specific instances, the paper does not provide a statistical analysis to support this as a general trend across the evaluated models. The data is sparse (only a few models per family), and the effect might be specific to the Qwen architecture or training data rather than a universal property of model scale. The claim should be qualified to reflect that this is an observed phenomenon in specific cases rather than a broad scaling law.

Second, the proposed method, \method, is claimed to significantly improve timely recall (e.g., from 26.7% to 57.4% for Llama-3.3-70B on WebShop) based on training on only 20 trajectories. While the improvement is notable, the small training set size raises concerns about overfitting and the stability of the result. The paper does not report variance, confidence intervals, or results from multiple random seeds, which are necessary to substantiate the claim that the method is robust and data-efficient. The conclusion should be tempered to acknowledge the limited training data and the need for further validation on larger datasets.

Third, the claim that "lessons from smaller models (8B) transfer effectively to larger models (70B)" is supported by the data in Table 2, but the magnitude of the transfer (55.3% vs. 57.4% for 70B-to-70B) is relatively small. The phrasing "transfer effectively" suggests a strong generalization capability that the data only partially supports. A more nuanced discussion of the transferability, perhaps highlighting the specific conditions under which it works best, would be more accurate.

Finally, the definition of "Timely Recall" is inconsistent across benchmarks: AbsRec@1 for request-based tasks and AbsRec@2 for environment-based tasks. This inconsistency makes direct comparisons between benchmarks difficult and risks over-claiming the comparability of results. The paper should either unify the metric definition or provide a clear justification for why a delay of one step is acceptable in environment-based tasks but not in request-based tasks.
