---
action_items:
- id: 1f2e61eb8921
  severity: writing
  text: '"The paper makes several strong claims regarding the novelty and difficulty
    of its proposed benchmark and the resulting model performance that appear to overreach
    the provided evidence.\n\nFirst, the Introduction asserts that the VideoKR-Eval
    benchmark is \"filtered to require genuine video reasoning\" specifically because
    \"single-frame probing fails for all three frontier models.\" This is a definitive
    claim about the nature of the data that is not substantiated by the results presented.
    Table'
artifact_hash: 442b60f42997ea4620ca51b6cec07f843dd48ca52b119472ba764f9d3b1bfbac
artifact_path: projects/PROJ-667-https-arxiv-org-abs-2606-05259/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:02:33.472357Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

"The paper makes several strong claims regarding the novelty and difficulty of its proposed benchmark and the resulting model performance that appear to overreach the provided evidence.\n\nFirst, the Introduction asserts that the VideoKR-Eval benchmark is \"filtered to require genuine video reasoning\" specifically because \"single-frame probing fails for all three frontier models.\" This is a definitive claim about the nature of the data that is not substantiated by the results presented. Table 2 shows that Qwen3-VL-32B-Thinking achieves 50.2% on VideoKR-Eval, a score that suggests the model is successfully solving a significant portion of the tasks. Without a dedicated ablation or analysis showing the specific performance drop when using single-frame inputs versus full video inputs for these specific models, the claim that single-frame probing \"fails\" is an overreach. The authors must either provide the single-frame probing data or soften the claim to reflect that the benchmark is *challenging* rather than *impossible* for single-frame methods.\n\nSecond, the Abstract and Introduction claim the method yields \"state-of-the-art performance\" on knowledge-intensive video tasks. While VideoKR achieves the best score within the specific group of models based on Qwen2.5-VL-7B or Qwen3-VL-8B (Table 2), it is substantially outperformed by larger open models (e.g., Qwen3-VL-32B-Thinking at 57.4% average vs. VideoKR's 44.2% on knowledge-intensive tasks) and closed-source models (GPT-5.4 at 71.3%). Using the unqualified term \"state-of-the-art\" implies a global leadership that the data does not support. The claim should be restricted to \"state-of-the-art among 7B/8B models\" or similar to be accurate.\n\nFinally, the claim that \"Human experts... validate all pipeline steps\" (Introduction) for a corpus of 315,000 examples is likely an overstatement of the actual human effort involved. While seed examples are curated, validating every step of a pipeline generating hundreds of thousands of examples is logistically improbable without massive sampling. The paper should clarify the scope of human validation (e.g., \"validated a representative sample\" or \"curated seeds and validated the pipeline logic\") to avoid misleading readers about the level of human oversight in the data generation process."
