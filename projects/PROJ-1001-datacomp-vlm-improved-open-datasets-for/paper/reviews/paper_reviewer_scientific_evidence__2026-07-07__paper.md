---
action_items:
- id: a50f002f5227
  severity: writing
  text: The paper presents a rigorous investigation into VLM data curation, particularly
    regarding decontamination and mixing strategies. However, the evidentiary strength
    of the central claims regarding data mixing and filtering is weakened by a lack
    of variance reporting and potential confounds in experimental design. First, the
    headline findings on data mixing (Section 4.2, Figure 3) and learning rate selection
    (Appendix, Table 1) are presented as single-run results. The reported improvements,
    such a
artifact_hash: d4a22931e6b886440cd41104bb215d7473154b2e0677ff1cb31fe0010e81d224
artifact_path: projects/PROJ-1001-datacomp-vlm-improved-open-datasets-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T10:41:45.910923Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a rigorous investigation into VLM data curation, particularly regarding decontamination and mixing strategies. However, the evidentiary strength of the central claims regarding data mixing and filtering is weakened by a lack of variance reporting and potential confounds in experimental design.

First, the headline findings on data mixing (Section 4.2, Figure 3) and learning rate selection (Appendix, Table 1) are presented as single-run results. The reported improvements, such as the shift from "worst" to "best" performance for the Instruction-heavy mix at larger scales, are often in the range of 0.5% to 2.0%. In deep learning training, such margins are frequently indistinguishable from the variance introduced by random weight initialization or data shuffling. Without reporting results across multiple seeds (e.g., mean ± standard deviation), the reader cannot determine if these "scale-aware" effects are robust phenomena or lucky seeds. This is critical for a paper claiming to establish generalizable data mixing laws.

Second, the data mixing experiments (Section 4.2) suffer from a potential confound regarding compute allocation. When the authors shift from a "Caption-heavy" to an "Instruction-heavy" mixture, they change the proportion of data types. However, the total number of tokens processed per epoch or the total training budget per data type is not explicitly controlled to be identical across the mixture variants in a way that isolates the *ratio* effect from the *exposure* effect. If the "Instruction-heavy" model simply sees more instruction tokens (even if the total token budget is fixed, the *density* changes), the gain might be due to increased exposure to that specific data type rather than the optimal *mixing ratio* itself. A control run that matches the exact token count of the baseline for the non-instruction data types (via repetition or subsampling) is needed to isolate the mixing ratio as the causal factor.

Finally, the claim that "filtering rarely helps" (Section 4.1) compares results across different evaluation suites: the small-scale experiments use the 13-task Validation suite, while the medium-scale experiments use the 33-task Core suite. This inconsistency introduces a confound where the observed "diminishing returns" of filtering could be an artifact of the different benchmark distributions (e.g., the Validation suite might be more sensitive to noise reduction than the Core suite) rather than a true scaling law. To robustly support the claim that filtering effects vanish at scale, the authors must report filtering results on a consistent, fixed evaluation suite across all model scales.

Addressing these design gaps—specifically by adding seed variance, controlling for token exposure in mixing experiments, and standardizing the evaluation suite—would significantly strengthen the causal claims regarding data curation strategies.
