---
action_items:
- id: e390b785c9d0
  severity: science
  text: Table 1 reports single-point estimates without confidence intervals. Re-run
    evaluations with multiple seeds (n>=5) per task or provide bootstrap CIs to validate
    that performance drops are not due to stochasticity.
- id: 2ee0ace98d28
  severity: science
  text: The LLM-based Verifier has 0.75 recall, risking invalid tasks. Provide a human
    audit of a random sample of accepted/rejected tasks to confirm the ground truth
    validity of the benchmark.
- id: 357e5fda3fe5
  severity: science
  text: Difficulty is defined by LLM failure, risking noise artifacts. Include a human
    baseline on a subset of evolved tasks to ensure difficulty is structural, not
    a generation artifact.
artifact_hash: 004a982517336ff5bb70731546f888ea558d17b145625434a810ca9028fcd39c
artifact_path: projects/PROJ-653-https-arxiv-org-abs-2605-28556/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T08:54:21.660166Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling methodology (TASTE) for addressing benchmark saturation in LLM agents, with a clear focus on coverage and difficulty. The experimental design is generally sound, utilizing a large pool of sampled sequences (N=2000) and clustering to ensure diversity. However, the scientific evidence supporting the central claims requires strengthening in three specific areas regarding statistical rigor and validity guarantees.

First, the lack of statistical significance testing is a critical gap. The NeurIPS Checklist (Item 7) admits to omitting error bars due to API costs, yet the main results (Table 1, Section 5.1) rely entirely on single-point estimates. LLM agent performance is notoriously stochastic; a single run per task is insufficient to distinguish between a genuine capability gap and random variance. The reported drops (e.g., -52.8% for Gemini-3-Flash) are large, but without confidence intervals or a multi-seed evaluation, the robustness of these claims is unproven. The authors should re-run the evaluation with multiple seeds to provide error bars or perform a bootstrap analysis.

Second, the validity of the benchmark relies heavily on an LLM-based "Verifier agent" (Section 4.3). While the authors report high precision, the recall is only 0.75–0.83. This means a significant fraction of potentially valid tasks are discarded, or the verifier's definition of "valid" is too strict. More concerning is the risk that the verifier itself hallucinates solvability. The claim that all tasks are "verifiable and have a reachable gold final state" is not fully supported by an LLM-only check. A manual audit of a random sample of tasks (both accepted and rejected) by human experts is necessary to confirm the ground truth.

Third, the "difficulty" of the evolved tasks is defined by the failure of other LLMs. This introduces a potential confound: if the evolution process (also LLM-driven) introduces nonsensical constraints or "hallucinated" logic that no agent can solve, the benchmark measures robustness to noise rather than genuine task complexity. The paper mentions "manual inspection of 15 failed tasks" (Checklist Item 15), but this sample size is too small to generalize. A human baseline evaluation on a subset of the evolved tasks would provide a crucial sanity check to ensure the difficulty is structural and not an artifact of the synthesis pipeline.

Addressing these points—specifically by adding statistical variance metrics and a human validation of the task validity/difficulty—would significantly strengthen the scientific evidence.
