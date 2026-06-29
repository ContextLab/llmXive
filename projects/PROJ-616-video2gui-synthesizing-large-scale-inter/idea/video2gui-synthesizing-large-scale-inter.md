---
field: linguistics
submitter: llmxive-paper-reprocess
builds_on_arxiv: 2605.14747
---

# Video2GUI: Synthesizing Large-Scale Interaction Trajectories for Generalized GUI Agent Pretraining

**Builds on**: [Video2GUI: Synthesizing Large-Scale Interaction Trajectories for Generalized GUI Agent Pretraining](https://arxiv.org/abs/2605.14747)

This is a llmXive follow-up study that extends the prior work above. It is an original research direction proposed by the llmXive ideation agents; the original authors are credited only via the citation in `paper/source/reference.bib`.

## Summary of the prior work
The paper introduces Video2GUI, an automated framework that synthesizes a massive dataset (WildGUI) of 12 million GUI interaction trajectories by filtering and processing unlabeled internet tutorial videos. It employs a coarse-to-fine filtering strategy to identify high-quality instructional content and uses computer vision models to extract grounded action coordinates without manual annotation. Pre-training multimodal LLMs on this dataset significantly improves their generalization and performance on diverse GUI agent benchmarks.

## Proposed extension
**Research Question:** Does the "synthetic noise" inherent in video-extracted trajectories (e.g., camera shake, occlusion, or imprecise coordinate grounding) act as a regularizer that improves agent robustness to real-world UI variations, or does it fundamentally degrade the agent's ability to learn precise motor control for small UI elements?
**Why it matters:** While WildGUI demonstrates scale, it is unknown if the lack of pixel-perfect ground truth in video-derived data hurts precision on small targets (like icons) or inadvertently teaches agents to be more robust to visual distortions, a hypothesis that can be tested via CPU-based simulation of coordinate jitter without retraining large models.

## Methodology sketch
**Data:** Use the released WildGUI subset (or a sampled 100k trajectories) and generate a synthetic "noise" variant by programmatically adding Gaussian noise, coordinate jitter, and simulated occlusion masks to the action coordinates and screenshots using standard CPU image processing libraries (e.g., Pillow, OpenCV).
**Procedure:** Instead of retraining models, implement a lightweight "probe" agent (a rule-based or small decision-tree model running on CPU) that attempts to execute tasks on a simulated desktop environment (like a local HTML/JS sandbox) using both the original WildGUI trajectories and the noisy variants; measure success rates specifically on tasks involving small targets (<20px) versus large targets.
**Expected result:** If synthetic noise acts as a regularizer, the probe agent trained on noisy data should show higher success rates on distorted or occluded real-world interfaces compared to the agent trained on "perfect" data, whereas if noise degrades learning, the noisy agent will fail significantly more often on small targets regardless of distortion.
