---
action_items:
- id: 208e7f894647
  severity: science
  text: The scientific evidence supporting the claim that GARD robustly handles multi-view
    degradation is currently insufficient due to gaps in the experimental design and
    ablation analysis. First, the ablation study in Table 1 (e001) presents a contradiction
    between the text and the data. The authors state that attention alignment yields
    "consistent performance gains" when combined with interpolated flow matching.
    However, the data shows that Model B (Alignment only) performs *worse* than the
    baseline
artifact_hash: 1b009a000ce5ea80de9107001816db5f680b271a1e700e1b78677c55727d55dc
artifact_path: projects/PROJ-632-https-arxiv-org-abs-2605-26230/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T17:38:38.595253Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The scientific evidence supporting the claim that GARD robustly handles multi-view degradation is currently insufficient due to gaps in the experimental design and ablation analysis.

First, the ablation study in Table 1 (e001) presents a contradiction between the text and the data. The authors state that attention alignment yields "consistent performance gains" when combined with interpolated flow matching. However, the data shows that Model B (Alignment only) performs *worse* than the baseline Model A on the ETH3D dataset (66.42 vs 67.30 AUC30). This suggests the attention alignment loss is not inherently beneficial and may even be detrimental without the specific structural priors provided by the interpolated flow matching. The manuscript currently glosses over this negative result, which is critical for understanding the stability of the proposed loss function.

Second, there is a significant disconnect between the training and evaluation protocols regarding the number of views. The "Implementation Details" section (e002) explicitly states that training uses "up to 4 views per iteration." In contrast, the main results (Table 1, e000) and the view-ablation study (Table 2, e001) demonstrate performance gains with 10, 30, and even 50 views. The paper provides no evidence that a model trained exclusively on 4-view subsets can effectively leverage the geometric consistency of 50 views at inference time. Without a training run using higher view counts or a theoretical justification for this generalization, the claim that the method scales effectively with view count is unsupported.

Finally, the construction of the "Attention alignment loss" (Eq. 2, e000) relies on target correspondence maps ($\mathbf{A}^*$) derived from "clean multi-view inputs." The methodology does not clarify if these targets are generated from the ground-truth geometry of the synthetic training set (Hypersim/TartanAir) or if they are estimated from the degraded inputs. If the targets rely on ground-truth geometry (which is unavailable in real-world inference), the model is effectively being trained with an oracle signal that does not exist in the target deployment scenario. This potential data leakage or unrealistic training assumption undermines the claim that the method is robust to real-world degradations where ground-truth geometry is unknown. The authors must clarify the source of $\mathbf{A}^*$ and demonstrate that the method does not rely on inaccessible ground-truth information during the training phase.
