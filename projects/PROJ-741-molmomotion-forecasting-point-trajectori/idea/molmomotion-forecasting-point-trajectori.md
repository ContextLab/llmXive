---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/340
paper_authors:
  - Jianing Zhang
  - Chenhao Zheng
  - Yajun Yang
  - Max Argus
  - Rustin Soraki
  - Winson Han
  - Taira Anderson
  - Chun-Liang Li
  - Shuo Liu
  - Jiafei Duan
  - Zhongzheng Ren
  - Jieyu Zhang
  - Ranjay Krishna
---

# MolmoMotion: Forecasting Point Trajectories in 3D with Language Instruction

**Field**: computer science

## Research question

How does conditioning a 3‑D point‑trajectory forecasting model on natural‑language instructions affect its prediction accuracy compared with a vision‑only baseline?

## Motivation

Anticipating how objects will move enables robots and embodied agents to plan safe and efficient actions. While visual cues capture geometry and dynamics, language can convey high‑level goals (e.g., “pick up the red cup”) that are not directly observable. Determining whether language instructions provide a measurable benefit for 3‑D motion forecasting will clarify how multimodal grounding can improve downstream robotic planning.

## Related work

- [MolmoMotion: Forecasting Point Trajectories in 3D with Language Instruction (2026)](https://arxiv.org/abs/2606.18558) — Introduces a large‑scale dataset and a language‑conditioned transformer for 3‑D point‑trajectory prediction; serves as the baseline system we will extend and evaluate.
- [Cruise Missile Target Trajectory Movement Prediction based on Optimal 3D Kalman Filter with Firefly Algorithm (2018)](https://arxiv.org/abs/1807.07006) — Proposes a classical Kalman‑filter pipeline for 3‑D trajectory prediction; provides a non‑learning baseline for comparison.
- [Semi-supervised Semantics‑guided Adversarial Training for Trajectory Prediction (2022)](https://arxiv.org/abs/2205.14230) — Shows how semantic cues and adversarial training improve robustness of trajectory predictors; informs our design of language‑guided regularization.
- [Trajectory Prediction Meets Large Language Models: A Survey (2025)](https://arxiv.org/abs/2506.03408) — Surveys recent efforts to integrate LLMs into trajectory prediction, highlighting open questions about the quantitative impact of language conditioning; motivates our focused empirical study.

## Expected results

We anticipate that the language‑conditioned model will achieve lower average displacement error (ADE) and final displacement error (FDE) than the vision‑only baseline on the PointMotionBench benchmark. A statistically significant improvement (p < 0.05 via paired bootstrap) would confirm that language provides complementary information; a null result would suggest that current language embeddings do not translate into measurable motion‑forecasting gains.

## Methodology sketch

- **Data acquisition**  
  - Download the PointMotionBench benchmark (training/validation/test splits) from its public HuggingFace repository: `https://huggingface.co/datasets/pointmotionbench`.  
  - Retrieve the MolmoMotion‑1M annotation files (JSON) from the same repo; these contain per‑clip language instructions and 3‑D point tracks.  
- **Pre‑processing**  
  - Parse each clip to extract (i) RGB frames, (ii) 3‑D point clouds (XYZ coordinates), and (iii) the associated natural‑language instruction.  
  - Normalize coordinates to meters and align all clips to a common world frame (camera static after t₀).  
  - Split the training set into 5‑fold cross‑validation folds for hyper‑parameter tuning.  
- **Model variants**  
  1. **Vision‑only transformer** – identical architecture to MolmoMotion but without the language token stream.  
  2. **Language‑conditioned transformer** – prepend a frozen CLIP‑text encoder embedding of the instruction to the visual token sequence (as in MolmoMotion).  
- **Training**  
  - Use PyTorch 2.2 on the GitHub Actions CPU runner (no GPU).  
  - Optimize with AdamW (lr = 1e‑4, weight decay = 1e‑2) for 3 epochs; each epoch processes ≤ 200 k samples to stay within the 6‑hour runtime limit.  
  - Apply gradient accumulation to simulate a batch size of 64 while keeping memory ≤ 6 GB.  
- **Evaluation**  
  - Compute ADE and FDE on the held‑out test split for both variants.  
  - Perform a paired bootstrap test (10 000 resamples) to assess whether differences are statistically significant.  
  - Report per‑category breakdowns (e.g., “pick‑and‑place”, “throw‑and‑catch”) to identify instruction types that benefit most.  
- **Ablations**  
  - Remove the language token to confirm the contribution of language.  
  - Replace CLIP‑text embeddings with randomly initialized embeddings to test the importance of semantic grounding.  
- **Reproducibility**  
  - All scripts, a `requirements.txt` (exact version pins), and a `run.sh` wrapper are stored in a public GitHub repository (`https://github.com/ContextLab/molmomotion-fork`).  
  - Random seeds (42, 123, 2026) are fixed for training, data shuffling, and bootstrap sampling; seeds are logged in each run.  

## Duplicate-check

- Reviewed existing ideas: *none*.
- Closest match: *MolmoMotion: Forecasting Point Trajectories in 3D with Language Instruction* (identical title) – however, the present idea reframes the question to isolate the effect of language conditioning and provides a concrete, reproducible CPU‑only experimental plan, which differs from the original manuscript’s broader scope.
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-24T23:37:27Z
**Outcome**: exhausted
**Original term**: MolmoMotion: Forecasting Point Trajectories in 3D with Language Instruction computer science
**Verified citation count**: 4

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | MolmoMotion: Forecasting Point Trajectories in 3D with Language Instruction computer science | 0 |
| 1 | language‑conditioned 3D trajectory prediction | 4 |
| 2 | multimodal motion forecasting with textual prompts | 0 |
| 3 | point cloud trajectory prediction guided by language | 0 |
| 4 | text‑driven 3D motion synthesis | 0 |
| 5 | language‑based 3D trajectory generation | 0 |
| 6 | instruction‑aware motion forecasting in 3D space | 0 |
| 7 | natural language guided point trajectory forecasting | 0 |
| 8 | cross‑modal trajectory prediction using language embeddings | 0 |
| 9 | textual instruction for 3D motion planning | 0 |
| 10 | language‑to‑motion translation for point trajectories | 0 |
| 11 | multimodal trajectory generation from language cues | 0 |
| 12 | language‑informed 3D point cloud dynamics prediction | 0 |
| 13 | conditional motion forecasting with textual commands | 0 |
| 14 | language‑augmented 3D trajectory modeling | 0 |
| 15 | text‑conditioned spatiotemporal point prediction | 0 |
| 16 | vision‑language motion prediction for 3D points | 0 |
| 17 | neural trajectory forecasting with language input | 0 |
| 18 | language‑supervised 3D motion prediction | 0 |
| 19 | instruction‑driven point trajectory synthesis | 0 |
| 20 | multimodal language‑vision motion forecasting | 0 |

### Verified citations

1. **MolmoMotion: Forecasting Point Trajectories in 3D with Language Instruction** (2026). Jianing Zhang, Chenhao Zheng, Yajun Yang, Max Argus, Rustin Soraki, et al.. arXiv. [2606.18558](https://arxiv.org/abs/2606.18558). PDF-sampled: No.
2. **Cruise Missile Target Trajectory Movement Prediction based on Optimal 3D Kalman Filter with Firefly Algorithm** (2018). Mahdi Mir. arXiv. [1807.07006](https://arxiv.org/abs/1807.07006). PDF-sampled: No.
3. **Semi-supervised Semantics-guided Adversarial Training for Trajectory Prediction** (2022). Ruochen Jiao, Xiangguo Liu, Takami Sato, Qi Alfred Chen, Qi Zhu. arXiv. [2205.14230](https://arxiv.org/abs/2205.14230). PDF-sampled: No.
4. **Trajectory Prediction Meets Large Language Models: A Survey** (2025). Yi Xu, Ruining Yang, Yitian Zhang, Jianglin Lu, Mingyuan Zhang, et al.. arXiv. [2506.03408](https://arxiv.org/abs/2506.03408). PDF-sampled: No.
