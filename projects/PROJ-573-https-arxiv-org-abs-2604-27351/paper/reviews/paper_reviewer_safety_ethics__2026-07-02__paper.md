---
action_items:
- id: d5d5a2589ed4
  severity: writing
  text: The manuscript lacks an explicit statement regarding Institutional Review
    Board (IRB) or ethics committee approval for the construction of EywaBench, particularly
    given its derivation from human-generated datasets (MMLU-Pro, DeepPrinciple).
    While the data is public, the aggregation and potential re-identification risks
    in the new benchmark schema should be addressed in the Ethics or Data Availability
    section.
- id: 244c70d6c9f2
  severity: writing
  text: The paper claims to use 'gpt-5-nano' and 'gpt-5-mini' (Section 5.2, Appendix
    A.1). As these model versions do not currently exist in public APIs, this raises
    concerns regarding the reproducibility of the safety evaluation and the potential
    for hallucinated results. The authors must clarify the exact model versions used
    or provide a path to reproduce the specific API calls.
- id: 0183c2f6b3c8
  severity: writing
  text: The 'Case Study A' (Appendix) demonstrates the system's ability to predict
    financial signals (NASDAQ). The authors should explicitly discuss the dual-use
    risk of this capability, specifically the potential for automated market manipulation
    or high-frequency trading strategies that could harm market stability, and include
    a mitigation statement in the Limitations or Discussion section.
artifact_hash: 6f6f16bf33fe17a682df44afbf900ee0d80c1586f03954b67f158a9d54f94900
artifact_path: projects/PROJ-573-https-arxiv-org-abs-2604-27351/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:38:52.561750Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a framework for integrating domain-specific foundation models into agentic systems, which introduces specific safety and ethical considerations that require clarification before publication.

First, regarding **data privacy and consent**, the authors construct `EywaBench` by aggregating samples from public datasets like MMLU-Pro and DeepPrinciple (Appendix `data_analysis.tex`). While these source datasets are public, the creation of a new, unified benchmark involving structured time-series and tabular data (e.g., financial signals, clinical data) necessitates a clear statement on data governance. The paper currently lacks an explicit declaration of IRB or ethics committee review, even if waived, and does not discuss whether the aggregation process introduces new re-identification risks or violates the original terms of use of the source datasets. A dedicated paragraph in the "Ethics Statement" or "Data Availability" section addressing these points is required.

Second, there is a significant **reproducibility and transparency concern** regarding the model versions cited. Section 5.2 and Appendix A.1 repeatedly reference "gpt-5-nano" and "gpt-5-mini" as the backbone language models. As of the current date, these model versions do not exist in public APIs (OpenAI currently offers the GPT-4 series). This discrepancy casts doubt on the validity of the reported safety and performance metrics. If these are internal or future models, the authors must clarify their status and provide a mechanism for independent verification, such as using a currently available model (e.g., GPT-4o) for the safety-critical ablation studies.

Third, the paper touches upon **dual-use risks** in the "Case Study A" (Appendix `experiment_details.tex`), where the system is used to forecast financial time series (NASDAQ). While the authors frame this as a scientific benchmark, the capability to automate financial prediction and execution via an agentic framework carries inherent risks of market manipulation or algorithmic trading instability. The manuscript should include a discussion in the "Limitations" or "Future Work" section acknowledging these dual-use potentials and outlining any safeguards or ethical guidelines the authors propose for deploying such systems in financial contexts.

Finally, the use of the "Avatar" analogy (Section 1) is creative but should not obscure the technical reality of the "Tsaheylu" interface. The authors must ensure that the description of the interface does not imply a level of "neural bonding" or direct cognitive access that could be misinterpreted as a safety risk in human-AI interaction contexts, although the current text seems to treat it as a metaphor.

Addressing these points will strengthen the paper's ethical standing and ensure that the claims regarding safety and reproducibility are robust.
