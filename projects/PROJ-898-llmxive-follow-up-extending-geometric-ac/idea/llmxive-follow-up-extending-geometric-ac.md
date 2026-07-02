---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Summary of the prior work
The paper introduces the Geometric Action Model (GAM), a robot policy that repurposes a pretrained Geometric Foundation Model (GFM) by splitting it to insert a causal future predictor, thereby unifying 3D geometry perception, temporal world modeling, and action decoding within a single shared backbone. By operating directly in 3D latent spaces rather than 2D image pixels, GAM achieves superior robustness, accuracy, and efficiency in contact-rich manipulation tasks compared to existing Vision-Language-Action models. The core innovation lies in leveraging the GFM's inherent geometric priors to resolve spatial ambiguities without requiring heavy architectural changes or massive-scale training data.

## Proposed extension
**Research Question:** Can the causal future predictor in GAM be replaced by a lightweight, symbolic geometric planner that operates entirely on CPU-tractable latent representations to achieve zero-shot generalization to novel object topologies without retraining?

This direction matters because GAM currently relies on learning temporal dynamics from data, which limits its ability to handle objects with unseen physical properties (e.g., deformable or articulated structures) unless explicitly trained on them. By shifting from a learned neural predictor to a symbolic solver constrained by the GFM's latent geometry, we can decouple the "what is the object" (perception) from "how does it move" (physics), enabling CPU-only inference and rigorous testing of geometric reasoning capabilities independent of large-scale vision-language priors.

## Methodology sketch
*   **Data:** We will use the existing GAM training dataset but augment it with a synthetic "topology-shift" test set containing objects with novel kinematic chains (e.g., new hinge configurations) and deformable materials not seen during GAM training, rendered in a CPU-based physics simulator like MuJoCo or PyBullet.
*   **Procedure:** We will freeze the GFM's encoder and decoder layers from the original GAM model and replace the learned causal transformer with a differentiable, CPU-optimized symbolic planner that solves rigid-body constraints directly in the latent space. We will then evaluate the system's success rate on novel manipulation tasks (e.g., folding a new type of cloth or opening a unique door mechanism) and measure inference latency on a standard CPU versus the original GPU-accelerated GAM.
*   **Expected Result:** We anticipate that the symbolic-latent approach will match or exceed the original GAM's success rate on novel topologies due to its explicit physical constraints, while reducing inference latency by an order of magnitude and eliminating the need for GPU acceleration, thus proving that geometric reasoning can be decoupled from deep temporal learning for robust, CPU-tractable robot control.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Geometric Action Model for Robot Policy Learning** — Jisang Han, Seonghu Jeon, Jaewoo Jung, René Zurbrügg, Honggyu An, Tifanny Portela, Marco Hutter, Marc Pollefeys, Seungryong Kim, Sunghwan Hong. https://arxiv.org/abs/2606.17046.

```bibtex
@article{orig_arxiv_2606_17046,
  title = {Geometric Action Model for Robot Policy Learning},
  author = {Jisang Han and Seonghu Jeon and Jaewoo Jung and René Zurbrügg and Honggyu An and Tifanny Portela and Marco Hutter and Marc Pollefeys and Seungryong Kim and Sunghwan Hong},
  year = {2026},
  eprint = {2606.17046},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.17046},
  url = {https://arxiv.org/abs/2606.17046}
}
```
