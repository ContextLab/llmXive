---
action_items:
- id: b3682bcdaf52
  severity: writing
  text: 'The paper presents a compelling hypothesis: that self-generated interaction
    context can serve as a system identifier for VLA models. The experimental design
    is generally sound in its use of controlled baselines (MV, EXP) and ablation studies
    (w/o actions, w/o images). However, the evidentiary strength of the central quantitative
    claims is currently undermined by a lack of reported variance and potential confounds
    in the training setup. First, the headline result in Table 2 (25.0% vs 19.8% OOD
    su'
artifact_hash: 1607b7a56c94fa04d6447f07acdf09cff37e83d8d846355c78db174b7f1d3ac9
artifact_path: projects/PROJ-796-in-context-world-modeling-for-robotic-co/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T20:10:21.829816Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling hypothesis: that self-generated interaction context can serve as a system identifier for VLA models. The experimental design is generally sound in its use of controlled baselines (MV, EXP) and ablation studies (w/o actions, w/o images). However, the evidentiary strength of the central quantitative claims is currently undermined by a lack of reported variance and potential confounds in the training setup.

First, the headline result in Table 2 (25.0% vs 19.8% OOD success) is presented as a single aggregate number. In robotic manipulation benchmarks, performance can fluctuate significantly based on random seeds, initialization, and the specific distribution of test episodes. Without reporting the standard deviation across multiple seeds (e.g., 3-5 runs), it is impossible to determine if the 5.2% absolute gain is a robust effect or within the noise floor of the evaluation protocol. The "false context" ablation is a strong qualitative control, but it does not substitute for statistical rigor on the primary metric.

Second, there is a potential confound in the comparison between ICWM and the Multi-View (MV) baseline. The ICWM model is trained with $N=5$ interaction clips prepended to every sample, effectively increasing the context window length and the computational cost per training step compared to the MV baseline, which processes only the task query. While the authors argue the gain comes from the *content* of the context, the design does not rule out that the gain comes from the *capacity* to attend to a longer sequence or the implicit regularization of processing more tokens. A fair comparison requires a baseline that also processes $N=5$ tokens (e.g., dummy tokens or repeated observations) to ensure the "context" benefit is not merely a "longer context" benefit.

Finally, the real-world results (Section 4.3) rely on a single aggregate success rate across 600 trials. While the sample size is decent, the lack of per-viewpoint variance reporting makes it difficult to assess stability. If the baseline failed catastrophically on just two of the six viewpoints while performing well on the others, the aggregate drop might be misleading. Reporting the mean and standard deviation across the 6 viewpoints (or the 6 seeds if multiple seeds were used) would provide a clearer picture of the method's reliability.

Addressing these points—specifically by adding seed variance to the main tables and clarifying the compute/context length control—would significantly strengthen the claim that the observed improvements are due to the proposed mechanism rather than experimental noise or confounding factors.
