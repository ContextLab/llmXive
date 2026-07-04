---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "ABot-Earth 0.5: Generative 3D Earth Model"

## Summary of the prior work
The paper introduces ABot-Earth 0.5, a generative framework that synthesizes seamless, large-scale 3D environments directly from satellite imagery using a native 3D Gaussian Splatting (3DGS) representation. By training on diverse urban reconstructions, the model achieves high-fidelity geometry and texture generation with hierarchical Level-of-Detail (LOD) structures, enabling real-time web-based visualization and bridging the sim-to-real gap for Embodied AI tasks like UAV navigation.

## Proposed extension
How does the geometric and textural fidelity of ABot-Earth 0.5's generated 3DGS scenes degrade when the conditioning satellite imagery is restricted to low-resolution, cloud-contaminated, or temporally stale inputs, and can a lightweight CPU-based "contextual inpainting" module restore these features without retraining the generative model? This question matters because real-world satellite data is often imperfect, and determining if the current model's robustness relies on ideal training data is critical for deploying the system in resource-constrained, non-GPU environments where retraining is impossible.

## Methodology sketch
We will curate a dataset of 500 $1\text{~km}^2$ urban regions where we synthetically degrade the input satellite imagery to simulate cloud cover, low resolution, and seasonal mismatches. The procedure involves running the existing ABot-Earth 0.5 inference pipeline on these degraded inputs to generate baseline 3DGS scenes, then applying a novel CPU-tractable, texture-aware 3DGS editing algorithm that uses a pre-trained, small-scale diffusion prior (quantized to run on CPU) to inpaint missing geometric details based on the known 2D context. We expect to quantify a significant drop in reconstruction quality (measured by PSNR and geometric consistency against ground truth LiDAR) with degraded inputs, and demonstrate that the proposed CPU-based inpainting module recovers >85% of the lost fidelity, proving that high-quality 3D generation can be maintained on edge devices with imperfect data.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **ABot-Earth 0.5: Generative 3D Earth Model** — Ming Qian, Tianjian Ouyang, Mingchao Sun, Zijian Wang, Jincheng Xiong, Jiarong Han, Yongchang Zhang, Jiawei Zhang, Xu Wang, Yu Liu, Luyang Tang, Fei Yu, Zengye Ge, Mengmeng Du, Yuan Liu, Nianfei Fan, Song Wang, Yingliang Peng, Chunxue Jia, Yang Liu, Shiying Zeng, Haozhe Shi, Junnan Lai, Hongyu Pan, Zheng Wu, Ning Guo, Mu Xu, Hang Zhang. https://arxiv.org/abs/2606.09967.

```bibtex
@article{orig_arxiv_2606_09967,
  title = {ABot-Earth 0.5: Generative 3D Earth Model},
  author = {Ming Qian and Tianjian Ouyang and Mingchao Sun and Zijian Wang and Jincheng Xiong and Jiarong Han and Yongchang Zhang and Jiawei Zhang and Xu Wang and Yu Liu and Luyang Tang and Fei Yu and Zengye Ge and Mengmeng Du and Yuan Liu and Nianfei Fan and Song Wang and Yingliang Peng and Chunxue Jia and Yang Liu and Shiying Zeng and Haozhe Shi and Junnan Lai and Hongyu Pan and Zheng Wu and Ning Guo and Mu Xu and Hang Zhang},
  year = {2026},
  eprint = {2606.09967},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.09967},
  url = {https://arxiv.org/abs/2606.09967}
}
```
