---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Does VLA Even Know the Basics? Measuring Commonsense and World Knowled"

## Summary of the prior work
The paper introduces Act2Answer, an evaluation protocol that converts standard VLM knowledge benchmarks into embodied tasks where agents must select answers by performing simple object-placement actions, thereby isolating knowledge retention from low-level control failures. Through a large-scale study of VLA models, the authors find that fine-tuning for robotics often degrades performance on rich semantic categories compared to the source VLMs, and that answer-relevant signals peak in middle layers before attenuating in the upper layers. The work establishes that while VLAs retain basic concepts, they suffer significant "catastrophic forgetting" of complex commonsense and world knowledge when adapted for action.

## Proposed extension
**Research Question:** Does the "attenuation" of knowledge signals in upper VLA layers correlate with a specific susceptibility to *contextual interference* (i.e., does adding irrelevant but visually complex distractors to the scene disproportionately degrade performance on knowledge-based actions compared to the original VLM)?

This question matters because the prior work identified *where* knowledge is lost (upper layers) but not *how* that loss manifests under environmental stress; if upper-layer knowledge is fragile, it may collapse entirely in cluttered real-world settings where VLMs would still succeed. This can be tested CPU-tractably by running the policy inference (which is often lightweight for simple placement tasks) on pre-generated static image frames without requiring real-time physics simulation or GPU-accelerated rendering.

## Methodology sketch
**Data:** We will extend the Act2Answer suite by generating a "Distractor Variant" of the existing 1,720 episodes. Using the original VLM benchmark images, we will programmatically overlay 3–5 semantically irrelevant but visually salient distractor objects (e.g., random geometric shapes or unrelated textures) onto the scene background, ensuring the target answer plates and the instruction remain unchanged.

**Procedure:** We will run the same 7 VLA models and 9 VLM baselines on both the "Clean" and "Distractor" variants. Since the task only requires selecting a target plate via a single action, we will simulate the environment using a CPU-based 2D physics engine (or even a static image-based logic check that verifies the model's chosen coordinate against the ground truth) to avoid GPU-heavy rendering. We will measure the "Knowledge Fragility Score," defined as the performance drop (Clean Accuracy - Distractor Accuracy) for each model and knowledge category.

**Expected Result:** We hypothesize that VLA models will exhibit a significantly higher Knowledge Fragility Score than their VLM baselines, particularly in "Rich Semantic" categories (e.g., Social, Normative), confirming that the upper-layer signal attenuation identified in the prior work makes VLAs uniquely vulnerable to environmental noise. We expect this drop to be minimal for "Simple Perceptual" categories, replicating the original paper's findings while adding a new dimension of robustness analysis.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Does VLA Even Know the Basics? Measuring Commonsense and World Knowledge Retention in Vision-Language-Action Models** — Nikita Kachaev, Andrey Moskalenko, Matvey Skripkin, Nikita Kurlaev, Daria Pugacheva, Albina Burlova, Mikhail Kolosov, Denis Shepelev, Andrey Kuznetsov, Elena Tutubalina, Aleksandr I. Panov, Alexey K. Kovalev, Vlad Shakhuro. https://arxiv.org/abs/2606.19297.

```bibtex
@article{orig_arxiv_2606_19297,
  title = {Does VLA Even Know the Basics? Measuring Commonsense and World Knowledge Retention in Vision-Language-Action Models},
  author = {Nikita Kachaev and Andrey Moskalenko and Matvey Skripkin and Nikita Kurlaev and Daria Pugacheva and Albina Burlova and Mikhail Kolosov and Denis Shepelev and Andrey Kuznetsov and Elena Tutubalina and Aleksandr I. Panov and Alexey K. Kovalev and Vlad Shakhuro},
  year = {2026},
  eprint = {2606.19297},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.19297},
  url = {https://arxiv.org/abs/2606.19297}
}
```
