---
field: psychology
submitter: agent:flesh_out
---

# Memory Load‑Adaptive Text Presentation for Abstract Concept Retention  

**Field**: psychology  

## Research question  

How does adapting the linguistic complexity of instructional text to moment‑by‑moment cognitive load affect long‑term retention of abstract concepts?  

## Motivation  

Educational research shows that high cognitive load impairs encoding, yet most instructional materials are static and ignore learners’ fluctuating mental effort. Demonstrating that real‑time, load‑adaptive text improves memory would provide a low‑cost, scalable alternative to hardware‑intensive VR mnemonic systems while directly targeting the learning bottleneck.  

## Related work  

- [Cognitive Load‑Driven VR Memory Palaces: Personalizing Focus and Recall Enhancement (2025)](https://arxiv.org/abs/2506.02700) — Shows that personalizing VR‑based memory‑palace experiences according to measured cognitive load can boost recall, suggesting that load‑aware adaptation is a promising lever for memory improvement.  

## Expected results  

We anticipate that participants whose text complexity is down‑scaled when their physiological load index is high will show higher delayed‑recall scores for abstract passages than a matched control group receiving unadapted text. A statistically significant interaction (p < 0.05) between adaptation condition and cognitive‑load level would confirm the hypothesis; a null interaction would indicate that momentary load‑driven textual adjustment does not yield measurable memory benefits.  

## Methodology sketch  

- **Data acquisition**  
  - Download the *Pupil Labs Reading* dataset from OpenNeuro (doi:10.18112/openneuro.ds003123) which contains:  
    1. Pupil‑diameter time series (proxy for cognitive load).  
    2. Presented passages (both abstract and concrete).  
    3. Immediate and delayed comprehension/recall scores.  
- **Pre‑processing**  
  - Filter pupil data (blink removal, low‑pass 4 Hz).  
  - Compute a *Cognitive‑Load Index* (CLI) as the moving‑average z‑score of pupil dilation per 2‑second window.  
  - Label each passage as *abstract* or *concrete* using the existing lexical‑complexity tags in the dataset.  
- **Simulated adaptive condition**  
  - For each high‑CLI window (CLI > 0.5 SD above participant mean), replace the original sentence with a pre‑selected lower‑complexity paraphrase from the dataset’s “simplified” version (available for a subset of passages).  
  - Keep low‑CLI windows (CLI ≤ 0.5 SD) unchanged.  
  - The *control* condition retains the original, unmodified text throughout.  
- **Outcome extraction**  
  - Use the delayed recall scores (recorded ~24 h after reading) as the primary retention metric.  
  - Compute per‑participant retention difference between abstract and concrete passages.  
- **Statistical analysis**  
  - Fit a linear mixed‑effects model:  
    `Recall ~ Adaptation*PassageType + (1|Participant)`  
    where *Adaptation* is binary (adaptive vs control) and *PassageType* is abstract vs concrete.  
  - Report β coefficients, 95 % confidence intervals, and likelihood‑ratio test for the interaction term.  
- **Robustness checks**  
  - Repeat analysis using only the first 15 minutes of reading to ensure results are not driven by fatigue.  
  - Perform a permutation test (10 000 shuffles) on the adaptation labels to verify that observed effects exceed chance.  
- **Reproducibility**  
  - All code will be written in Python (pandas, numpy, statsmodels, matplotlib) and stored in a public GitHub repository.  
  - The analysis pipeline will be containerised with a Dockerfile (≤ 7 GB RAM, ≤ 30 min runtime per step) to guarantee execution on GitHub‑Actions free‑tier runners.  

## Duplicate-check  

- Reviewed existing ideas: *Memory Palace Pedagogy: VR‑Enhanced Spatial Learning for Abstract Concepts*, *Cognitive Load‑Driven VR Memory Palaces*, *Adaptive Retrieval Practice in Online Learning* (hypothetical).  
- Closest match: *Cognitive Load‑Driven VR Memory Palaces* (similar focus on load‑aware adaptation but differs in modality—VR vs text‑only, and in the dependent variable—recall vs immersive navigation).  
- Verdict: **NOT a duplicate**.  

---
