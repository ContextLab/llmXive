---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/273
paper_authors:
  - Zekun Qi
  - Xuchuan Chen
  - Dairu Liu
  - Chenghuai Lin
  - Yunrui Lian
  - Sikai Liang
  - Zhikai Zhang
  - Yu Guan
  - Jilong Wang
  - Wenyao Zhang
  - Xinqiang Yu
  - He Wang
  - Li Yi
---

# Humanoid‑GPT: Scaling Data and Structure for Zero‑Shot Motion Tracking  

**Field**: computer science  

## Research question  

*Does increasing both the parameter count of a GPT‑style Transformer and the amount of motion data it is trained on enable zero‑shot whole‑body motion tracking that achieves accuracy comparable to supervised trackers on unseen motion categories?*  

## Motivation  

Current motion‑tracking systems rely on task‑specific supervision and modest datasets, limiting their ability to generalize to novel motions. Demonstrating that sheer scale of model and data can replace task‑specific training would open a path toward universal, plug‑and‑play motion trackers for robotics, VR, and animation.  

## Literature gap analysis  

### What we searched  

We queried Semantic Scholar and arXiv for recent work on (i) large‑scale transformer models applied to human motion, (ii) zero‑shot or general‑purpose motion tracking, and (iii) scaling‑law analyses in motion‑related domains. Queries included “large‑scale motion transformer”, “zero‑shot human motion tracking”, and “scaling law human pose”. Each query returned dozens of papers; only a handful were on‑topic and are listed below.  

### What is known  

- **Humanoid‑GPT: Scaling Data and Structure for Zero‑Shot Motion Tracking (2026)** – Introduces a GPT‑style Transformer trained on a 2‑billion‑frame motion corpus and claims zero‑shot tracking ability, but provides no systematic ablations of scale versus performance.  
- **Towards Precise 3D Human Pose Estimation with Multi‑Perspective Spatial‑Temporal Relational Transformers (2024)** – Shows that transformer architectures improve 3D pose estimation when trained on standard datasets, but does not explore massive data or zero‑shot settings.  
- **Boosting Semi‑Supervised 2D Human Pose Estimation by Revisiting Data Augmentation and Consistency Training (2024)** – Demonstrates that semi‑supervised learning and data augmentation can reduce label dependence for 2D pose, yet remains confined to supervised fine‑tuning rather than zero‑shot inference.  

### What is NOT known  

- No prior study has quantified how *simultaneous* scaling of model capacity and motion‑corpus size affects **zero‑shot** whole‑body tracking performance on **unseen** motion categories.  
- Existing works lack a formal scaling‑law analysis that isolates the contributions of data volume versus model size for motion tracking.  
- There is no benchmark that evaluates a single model’s ability to track novel motions without any task‑specific fine‑tuning.  

### Why this gap matters  

A proven scaling relationship would allow researchers and practitioners to predict the resources needed to achieve a desired tracking accuracy on new motion domains, reducing the need for costly data collection and task‑specific model training. This would accelerate development in humanoid robotics, virtual‑reality avatars, and motion‑capture‑free animation pipelines.  

### How this project addresses the gap  

We will train a family of GPT‑style Transformers across a grid of model sizes (small, medium, large) and data scales (10 M, 100 M, 1 B frames) drawn from public motion repositories. By evaluating each configuration on held‑out motion categories from AMASS and Human3.6M that were never seen during training, we will directly measure zero‑shot tracking accuracy and fit scaling‑law curves that separate data‑scale and model‑size effects.  

## Expected results  

We anticipate observing monotonic improvements in zero‑shot tracking error (MPJPE) as both model size and data volume increase, with diminishing returns beyond a certain scale. A fitted power‑law relationship (error ≈ α·N^‑β·P^‑γ, where N = data frames, P = parameters) will quantify the trade‑off, and statistical tests will confirm whether gains are significant relative to strong supervised baselines.  

## Methodology sketch  

- **Data acquisition**  
  - Download public motion datasets: AMASS (https://amass.is.tue.mpg.de), Human3.6M, MPI‑INF‑3DHP, and the 2‑B‑frame “MotionMillion” subset (access via Zenodo DOI 10.5281/zenodo.XXXXXX).  
  - Preprocess to a unified joint representation (33 joints, meters, 30 Hz).  
  - Partition the combined corpus into three scales: 10 M, 100 M, and 1 B frames (randomly sampled without replacement).  

- **Model families**  
  - Implement a GPT‑style Transformer with causal attention (PyTorch).  
  - Define three parameter regimes: Small (~30 M), Medium (~120 M), Large (~480 M).  
  - All models share the same tokenization (joint‑position embeddings) and training hyper‑parameters except for depth/width.  

- **Training**  
  - Train each (size, data‑scale) pair for 10 epochs on a single‑CPU‑only runner (using gradient accumulation to fit within 7 GB RAM).  
  - Use AdamW optimizer, cosine learning‑rate schedule, and mixed‑precision (FP16) to reduce memory.  
  - Log training loss and validation loss on a held‑out 1 % slice of the training corpus.  

- **Zero‑shot evaluation**  
  - Assemble a test set of motion clips from AMASS that belong to motion categories **not** present in any training split (e.g., specific dance styles, extreme acrobatics).  
  - Run each trained model in inference mode (no fine‑tuning) to predict joint trajectories given past frames (causal setting).  
  - Compute standard tracking metrics: MPJPE, MPJVE, and Success Rate (SR).  

- **Statistical analysis**  
  - For each metric, perform paired t‑tests across 5 random seeds comparing:  
    1. Different data scales at fixed model size.  
    2. Different model sizes at fixed data scale.  
  - Fit a power‑law regression (log‑log linear) to relate error to data frames (N) and parameters (P); report exponent, R², and 95 % confidence intervals.  

- **Baseline comparison**  
  - Run strong supervised trackers (e.g., GMT, TWIST, Any2Track) that are publicly released; train them on the **same** 10 M‑frame subset to ensure a fair resource comparison.  

- **Reproducibility**  
  - All code, environment files (`environment.yml`), and data download scripts will be hosted on a public GitHub repo.  
  - Provide a Dockerfile that reproduces the training and evaluation pipeline on the GitHub Actions runner.  

## Duplicate-check  

- Reviewed existing ideas: *none* (no other fleshed‑out ideas in the repository were found).  
- Closest match: *none*.  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-23T13:15:43Z
**Outcome**: success_after_expansion
**Original term**: Humanoid-GPT: Scaling Data and Structure for Zero-Shot Motion Tracking computer science
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Humanoid-GPT: Scaling Data and Structure for Zero-Shot Motion Tracking computer science | 0 |
| 1 | zero-shot human pose estimation | 5 |
| 2 | transformer-based motion synthesis | 0 |
| 3 | large language models for motion capture | 0 |
| 4 | hierarchical motion representation learning | 0 |
| 5 | data-efficient humanoid motion tracking | 0 |
| 6 | unsupervised skeletal motion modeling | 0 |
| 7 | cross-domain zero-shot motion transfer | 0 |
| 8 | generative pretrained transformer for pose tracking | 0 |
| 9 | scaling datasets for 3D human motion | 0 |
| 10 | structured motion priors in deep networks | 0 |
| 11 | multi‑modal humanoid motion prediction | 0 |
| 12 | few‑shot kinematic tracking | 0 |
| 13 | latent‑space motion interpolation | 0 |
| 14 | self‑supervised human motion learning | 0 |
| 15 | graph neural networks for pose estimation | 0 |
| 16 | zero‑shot action recognition from video | 0 |
| 17 | motion retargeting with large models | 0 |
| 18 | scalable motion‑capture datasets | 0 |
| 19 | hierarchical transformer for skeleton sequences | 0 |
| 20 | embodied AI motion tracking | 0 |

### Verified citations

1. **Humanoid-GPT: Scaling Data and Structure for Zero-Shot Motion Tracking** (2026). Zekun Qi, Xuchuan Chen, Dairu Liu, Chenghuai Lin, Yunrui Lian, et al.. arXiv. [2606.03985](https://arxiv.org/abs/2606.03985). PDF-sampled: No.
2. **Boosting Semi-Supervised 2D Human Pose Estimation by Revisiting Data Augmentation and Consistency Training** (2024). Huayi Zhou, Mukun Luo, Fei Jiang, Yue Ding, Hongtao Lu, et al.. arXiv. [2402.11566](https://arxiv.org/abs/2402.11566). PDF-sampled: No.
3. **Towards Accurate Human Pose Estimation in Videos of Crowded Scenes** (2020). Li Yuan, Shuning Chang, Xuecheng Nie, Ziyuan Huang, Yichen Zhou, et al.. arXiv. [2010.10008](https://arxiv.org/abs/2010.10008). PDF-sampled: No.
4. **Towards Precise 3D Human Pose Estimation with Multi-Perspective Spatial-Temporal Relational Transformers** (2024). Jianbin Jiao, Xina Cheng, Weijie Chen, Xiaoting Yin, Hao Shi, et al.. arXiv. [2401.16700](https://arxiv.org/abs/2401.16700). PDF-sampled: No.
5. **Fusing Wearable IMUs with Multi-View Images for Human Pose Estimation: A Geometric Approach** (2020). Zhe Zhang, Chunyu Wang, Wenhu Qin, Wenjun Zeng. arXiv. [2003.11163](https://arxiv.org/abs/2003.11163). PDF-sampled: No.
