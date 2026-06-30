---
action_items:
- id: 7ec336b8cabf
  severity: writing
  text: The manuscript relies heavily on domain-specific terminology that creates
    a barrier for non-specialist readers, particularly those in general computer science
    or software engineering who may not be deeply embedded in the LLM benchmarking
    sub-field. In the Introduction, the term "contamination" is used repeatedly to
    describe data leakage issues. While standard in this niche, the paper fails to
    explicitly define it as "the inadvertent inclusion of test data in the model's
    training set," which woul
artifact_hash: 9c6bbf84633b0c3c69b73145c2bd5223d277d92067c1ce8b39448e12105e3959
artifact_path: projects/PROJ-748-multi-lcb-extending-livecodebench-to-mul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T12:57:17.287799Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific terminology that creates a barrier for non-specialist readers, particularly those in general computer science or software engineering who may not be deeply embedded in the LLM benchmarking sub-field.

In the **Introduction**, the term "contamination" is used repeatedly to describe data leakage issues. While standard in this niche, the paper fails to explicitly define it as "the inadvertent inclusion of test data in the model's training set," which would aid broader comprehension. Similarly, "Pass@1" is introduced in Section 4 without defining the underlying sampling procedure (i.e., generating $k$ samples and checking if at least one is correct), assuming the reader already knows the statistical formulation of Pass@k.

**Section 3.1** lists "JIT" (Just-In-Time) compilation as a paradigmatic diversity factor without expansion. While common to developers, it is jargon that should be spelled out for a general academic audience. Furthermore, the phrase "zero-shot prompting" in **Section 3.2** is used without explanation; a plain-language alternative like "prompting without in-context examples" would be more inclusive.

The **Results** section (Section 5) and tables (e.g., Table 1 in e001) frequently reference "Pass@1" and "Pass@10" without reiterating the definition, forcing the reader to search back for the metric's meaning. The acronym "LLM" is also used in the first sentence of the Introduction without the full phrase "Large Language Model" preceding it.

Finally, terms like "functional format" (Section 3) and "STDIN/STDOUT" are used as if they are universally understood concepts in this context, though they represent specific technical constraints that should be briefly contextualized for readers unfamiliar with competitive programming environments.
