---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

## Summary of the prior work
The paper identifies that Zero-Shot Compositional Action Recognition (ZS-CAR) models often fail by relying on object-driven shortcuts rather than temporal verb cues, leading to poor generalization on unseen verb-object pairs. To mitigate this, the authors propose RCORE, a framework combining Co-occurrence Prior Regularization (CPR) to penalize frequent training co-occurrences and Temporal Order Regularization (TORC) to enforce sensitivity to action sequencing. Their experiments on Sth-com and EK100-com datasets demonstrate that these regularizations significantly reduce shortcut reliance and improve compositional generalization.

## Proposed extension
Can we improve the robustness of verb representations in ZS-CAR by explicitly modeling the *negation* of object-driven shortcuts through a "Counterfactual Object Masking" task, where the model must correctly identify an action even when the primary object is synthetically occluded or replaced with a semantically similar but action-incompatible distractor? This direction matters because while RCORE penalizes co-occurrence priors, it does not explicitly test or train the model's ability to distinguish actions based solely on motion dynamics when visual object cues are ambiguous or misleading, potentially leaving a residual reliance on object features in edge cases.

## Methodology sketch
We will construct a CPU-tractable evaluation and training extension using the existing Sth-com dataset by generating synthetic "counterfactual" samples: for every training video, we will create a variant where the bounding box of the target object is replaced with a static patch of a different, co-occurring object class (e.g., replacing "cup" with "bowl" in a "pour" action) while keeping the motion trajectory intact. The procedure involves training a lightweight, frozen-feature extractor (e.g., pre-trained ResNet-18 features averaged over time) with a simple linear classifier, augmented by a new "Counterfactual Consistency Loss" that penalizes the model if its prediction changes when the object is swapped but the motion remains the same. We expect the resulting model to show a significantly higher accuracy drop on standard object-replacement tests compared to RCORE, but a smaller drop on the specific counterfactual test set, proving that the new loss function successfully forces reliance on temporal motion cues over static object identity.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero-Shot Compositional Action Recognition** — Geo Ahn, Inwoong Lee, Taeoh Kim, Minho Shim, Dongyoon Wee, Jinwoo Choi. https://arxiv.org/abs/2601.16211.

```bibtex
@article{orig_arxiv_2601_16211,
  title = {Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero-Shot Compositional Action Recognition},
  author = {Geo Ahn and Inwoong Lee and Taeoh Kim and Minho Shim and Dongyoon Wee and Jinwoo Choi},
  year = {2026},
  eprint = {2601.16211},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2601.16211},
  url = {https://arxiv.org/abs/2601.16211}
}
```
