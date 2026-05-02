---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Visual Attention on False Memory Formation

**Field**: psychology

## Research question

Does heightened visual attention to salient but irrelevant scene elements during encoding increase the likelihood of forming false memories for those elements during later recall?

## Motivation

False memories undermine the reliability of eyewitness testimony and everyday recollection. While extensive work has documented the reconstructive nature of memory, the contribution of moment‑to‑moment visual attention to false memory generation remains under‑explored. Demonstrating a link between attentional capture and false recall would clarify a mechanistic pathway and suggest simple attentional‑training interventions to mitigate memory distortions.

## Related work

- [Attention Guided CAM: Visual Explanations of Vision Transformer Guided by Self-Attention (2024)](http://arxiv.org/abs/2402.04563v1) — Shows how self‑attention maps in vision transformers can be interpreted as visual saliency, providing a computational proxy for human attentional focus.  
- [Deep Visual Attention Prediction (2017)](http://arxiv.org/abs/1705.02544v3) — Presents a CNN‑based model that predicts human eye‑fixation locations on natural scenes, offering an off‑the‑shelf saliency estimator for datasets lacking eye‑tracking data.

## Expected results

We anticipate a positive correlation between the saliency (or predicted fixation density) of a scene element and the rate at which participants falsely report that element during recall. A statistically significant Pearson r > 0.3 (p < 0.01) would support the hypothesis; a non‑significant correlation would falsify it. Effect‑size estimates (Cohen’s d) will guide the required sample size for future replication.

## Methodology sketch

- **Dataset acquisition**  
  - Download the Visual Genome scene–question–answer dataset (https://visualgenome.org/api/v0/api.html) – includes images and region descriptions.  
  - Obtain the corresponding human recall annotations from the “Memory for Scenes” subset (if publicly available) or use the “Free Recall” annotations from the OpenNeuro dataset ds003166.  
- **Saliency estimation**  
  - Apply the Deep Visual Attention Prediction model (code released at https://github.com/linzhengyu/DeepVisualAttention) to each image to generate fixation probability maps.  
  - Validate the model on the SALICON benchmark (http://salicon.net) to ensure reasonable performance on natural scenes.  
- **Feature extraction**  
  - Identify “salient but irrelevant” objects per image: compute the average saliency within each annotated object mask and select the top‑10 % that are not mentioned in the ground‑truth scene description.  
- **False memory scoring**  
  - For each participant’s recall transcript, code whether any of the selected irrelevant objects are reported (binary false‑memory flag).  
  - Compute per‑image false‑memory rate = (number of participants reporting the object) / (total participants).  
- **Statistical analysis**  
  - Correlate object‑level saliency scores with false‑memory rates using Pearson’s r.  
  - Fit a mixed‑effects logistic regression with random intercepts for participants and items to control for individual differences.  
  - Perform permutation testing (10 000 shuffles) to confirm robustness of the correlation.  
- **Robustness checks**  
  - Replicate the analysis using Attention‑Guided CAM saliency maps from a pretrained Vision Transformer (ViT‑B/16) to ensure results are not model‑specific.  
  - Conduct a split‑half reliability analysis on participants to verify consistency of false‑memory reporting.  
- **Reproducibility**  
  - All code will be containerized (Docker) and executed in a GitHub Actions workflow limited to ≤6 h runtime, ≤7 GB RAM, and ≤2 CPU cores.  
  - Results and figures will be saved to the repository’s `results/` folder.

## Duplicate-check

- Reviewed existing ideas: (none provided).  
- Closest match: N/A.  
- Verdict: **NOT a duplicate**.
