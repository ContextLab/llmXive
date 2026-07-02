---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "FashionChameleon: Towards Real-Time and Interactive Human-Garment Vide"

## Summary of the prior work
FashionChameleon introduces a real-time framework for interactive human-garment video customization using autoregressive generation, achieving 23.8 FPS by training a teacher model on single-garment pairs via in-context learning. The core innovations include Streaming Distillation for consistency and a training-free KV Cache Rescheduling mechanism that allows users to switch garments mid-generation while preserving motion coherence without retraining.

## Proposed extension
How can the semantic alignment between user-provided natural language instructions and the visual garment features be dynamically optimized within the existing KV Cache Rescheduling framework to enable "instruction-driven" garment swapping, rather than relying solely on explicit image references? This matters because current interactive systems require users to manually upload new garment images for every switch, whereas a text-guided approach would drastically lower the barrier for e-commerce customization and creative content generation, all while remaining computationally feasible on CPU-only inference engines by leveraging lightweight adapter layers instead of heavy video diffusion backbones.

## Methodology sketch
We will curate a dataset of 5,000 short human-motion video clips paired with synthetic multi-garment descriptions (e.g., "change to a red summer dress") and corresponding garment reference images. The procedure involves freezing the pre-trained FashionChameleon backbone and inserting a lightweight, CPU-optimized cross-attention adapter that maps text embeddings directly to the "reference KV" slots during the rescheduling phase, replacing the need for explicit image input during the switch. We expect the results to show that the text-guided model achieves >85% semantic fidelity in garment changes (measured by CLIP-T similarity) while maintaining motion coherence scores comparable to the image-driven baseline, with inference latency remaining under 50ms per frame on a standard 8-core CPU.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **FashionChameleon: Towards Real-Time and Interactive Human-Garment Video Customization** — Quanjian Song, Yefeng Shen, Mengting Chen, Hao Sun, Jinsong Lan, Xiaoyong Zhu, Bo Zheng, Liujuan Cao. https://arxiv.org/abs/2605.15824.

```bibtex
@article{orig_arxiv_2605_15824,
  title = {FashionChameleon: Towards Real-Time and Interactive Human-Garment Video Customization},
  author = {Quanjian Song and Yefeng Shen and Mengting Chen and Hao Sun and Jinsong Lan and Xiaoyong Zhu and Bo Zheng and Liujuan Cao},
  year = {2026},
  eprint = {2605.15824},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.15824},
  url = {https://arxiv.org/abs/2605.15824}
}
```
