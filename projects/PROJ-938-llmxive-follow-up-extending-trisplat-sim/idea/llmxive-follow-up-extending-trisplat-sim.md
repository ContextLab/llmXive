---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "TriSplat: Simulation-Ready Feed-Forward 3D Scene Reconstruction"

## Summary of the prior work
TriSplat introduces a feed-forward neural network that reconstructs 3D scenes directly into oriented triangle meshes from sparse, unposed images, bypassing the need for post-hoc conversion required by Gaussian-based methods. By constructing geometry normals from predicted point maps and refining them with an image-conditioned head, the method produces simulation-ready outputs suitable for physics engines in a single pass. This approach achieves geometry-faithful reconstructions on datasets like RealEstate10K and DL3DV while maintaining competitive novel-view synthesis quality.

## Proposed extension
How can we adapt TriSplat's triangle-based feed-forward architecture to run efficiently on CPU-only edge devices by replacing the heavy image-conditioned normal refinement head with a lightweight, differentiable ray-casting module that enforces geometric consistency without backpropagating through a deep CNN? This extension matters because it would democratize simulation-ready 3D reconstruction for robotics and embodied AI on low-power hardware where GPU inference is currently a bottleneck.

## Methodology sketch
We will utilize the RealEstate10K validation set, downsampling images to 320x240 resolution to reduce computational load, and replace TriSplat's normal refinement head with a differentiable, CPU-optimized ray-surface intersection layer that calculates normals based on local triangle connectivity and depth gradients. The procedure involves training the modified model on a standard CPU cluster (e.g., 64-core AMD EPYC) using a curriculum that gradually introduces the ray-casting constraint while freezing the backbone to isolate the efficiency gains. We expect to observe a 10-15x reduction in inference latency compared to the GPU baseline while retaining over 90% of the original mesh fidelity (measured by Chamfer Distance) and novel-view rendering PSNR.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **TriSplat: Simulation-Ready Feed-Forward 3D Scene Reconstruction** — Weijie Wang, Zimu Li, Jinchuan Shi, Zeyu Zhang, Botao Ye, Marc Pollefeys, Donny Y. Chen, Bohan Zhuang. https://arxiv.org/abs/2605.26115.

```bibtex
@article{orig_arxiv_2605_26115,
  title = {TriSplat: Simulation-Ready Feed-Forward 3D Scene Reconstruction},
  author = {Weijie Wang and Zimu Li and Jinchuan Shi and Zeyu Zhang and Botao Ye and Marc Pollefeys and Donny Y. Chen and Bohan Zhuang},
  year = {2026},
  eprint = {2605.26115},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.26115},
  url = {https://arxiv.org/abs/2605.26115}
}
```
