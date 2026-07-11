---
action_items:
- id: 5fbc7b6d57b5
  severity: writing
  text: The paper presents a compelling diagnosis of object-driven shortcuts in Zero-Shot
    Compositional Action Recognition (ZS-CAR) and proposes a method (RCORE) to mitigate
    them. The experimental design is generally sound, utilizing two datasets (Sth-com,
    EK100-com) and multiple backbones. However, the evidentiary strength of the reported
    improvements is weakened by a lack of statistical robustness and incomplete isolation
    of the proposed components' effects. First, the primary results in Tables 1 and
artifact_hash: f098ae707662ea7ce696ff8b8606006fdddb80c25be82361ec114d13c9a397ed
artifact_path: projects/PROJ-1037-why-can-t-i-open-my-drawer-mitigating-ob/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:12:35.985086Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling diagnosis of object-driven shortcuts in Zero-Shot Compositional Action Recognition (ZS-CAR) and proposes a method (RCORE) to mitigate them. The experimental design is generally sound, utilizing two datasets (Sth-com, EK100-com) and multiple backbones. However, the evidentiary strength of the reported improvements is weakened by a lack of statistical robustness and incomplete isolation of the proposed components' effects.

First, the primary results in Tables 1 and 2 report single-point accuracy improvements (e.g., +3.8% on unseen compositions for Sth-com with CLIP) without any indication of variance. In deep learning benchmarks, especially with complex training objectives like RCORE, performance can fluctuate significantly across random seeds. A 3-4 point gain is meaningful but could plausibly arise from a lucky initialization or a specific random seed if not averaged over multiple runs. The paper should report results as mean ± standard deviation (or standard error) across at least 3-5 independent training runs with different seeds. Without this, the reader cannot distinguish a robust methodological improvement from statistical noise.

Second, the ablation studies, while detailed, do not fully isolate the contribution of the data augmentation strategy in Co-occurrence Prior Regularization (CPR) from the regularization loss itself. Section 4.1 describes synthesizing new videos by mixing frames (Eq. 1). Table 3(c) compares the full method against a "Full Open-world" baseline and a "Closed-world" baseline, but it does not include a control run that applies the *same* frame-mixing augmentation to the baseline model *without* the specific CPR margin loss ($L_{CPR}$). It is possible that the performance gain attributed to CPR comes simply from the regularization effect of training on augmented data (a form of Mixup/CutMix) rather than the specific mechanism of penalizing frequent co-occurrences. To claim that the *specific* CPR design is responsible, the authors must show that the augmentation alone (without the loss) yields less improvement than the full CPR method.

Finally, the Temporal Order Regularization (TORC) relies on specific hyperparameters, notably the temperature $\tau$ in the entropy loss and the specific permutation strategy for shuffling. The ablation in Table 3(b) isolates the loss terms ($L_{cos}$ vs $L_{ent}$) but does not explore the sensitivity to $\tau$ or the nature of the shuffling. If the gain is highly sensitive to a specific $\tau$ value or a specific shuffling distribution, the robustness of the claim is reduced. A brief sensitivity analysis or a justification for the chosen $\tau$ would strengthen the evidence that the method is not over-tuned to a specific configuration.

Addressing these points—specifically adding seed variance and a control for the CPR augmentation—would significantly bolster the claim that RCORE's improvements are due to the proposed mechanisms rather than experimental artifacts or luck.
