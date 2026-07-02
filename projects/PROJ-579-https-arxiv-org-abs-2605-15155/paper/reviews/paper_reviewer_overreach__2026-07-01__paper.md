---
action_items:
- id: 2aecb6bdc3da
  severity: writing
  text: "The paper makes several strong claims regarding the consistency and robustness\
    \ of the proposed SDAR method that slightly exceed the granularity of the provided\
    \ evidence. First, the abstract and introduction assert that SDAR \"consistently\
    \ outperforms hybrid RL\u2013OPSD baselines across all model scales.\" While the\
    \ aggregate averages in Table 1 support a general improvement, the claim of \"\
    consistent\" outperformance is contradicted by specific sub-task results. For\
    \ instance, on the Qwen2.5-7B model in"
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:57:47.806086Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the consistency and robustness of the proposed SDAR method that slightly exceed the granularity of the provided evidence.

First, the abstract and introduction assert that SDAR "consistently outperforms hybrid RL–OPSD baselines across all model scales." While the aggregate averages in Table 1 support a general improvement, the claim of "consistent" outperformance is contradicted by specific sub-task results. For instance, on the Qwen2.5-7B model in the ALFWorld "Heat" and "Cool" sub-tasks, SDAR (86.7% and 68.2%) underperforms the GRPO+OPSD baseline (87.5% and 76.5%). While the overall average is higher, the use of "consistently" implies uniform superiority across all metrics, which is not strictly supported by the data. The text should be tempered to reflect "average improvement" or "superiority in most settings."

Second, the claim that the method "degrades gracefully with retrieval quality" (Abstract and Section 4.3) suggests a smooth, monotonic relationship between retrieval fidelity and performance. Table 2 shows that while Random Retrieval (83.1%) outperforms the baseline (81.2%), the performance gap between Random and the best retrieval method (UCB, 86.8%) is non-trivial (~3.7%). The term "gracefully" may overstate the robustness, as the method still suffers a noticeable drop when retrieval quality is poor. A more precise phrasing would be that the method is "robust to noisy retrieval" or "maintains a positive signal even with random skills," rather than implying a graceful degradation curve.

Finally, the claim that "negative-gap tokens exceed 50% of the total count" (Introduction) is a specific quantitative assertion based on Figure 3. While the figure supports a significant presence of negative gaps, the exact 50% threshold should be explicitly verified against the underlying data distribution shown in the figure. If the distribution is not clearly bimodal or if the 50% is an approximation, the claim risks over-precision. The authors should either provide the exact statistic or qualify the statement to "a majority" or "a significant portion" to align strictly with the visual evidence.
