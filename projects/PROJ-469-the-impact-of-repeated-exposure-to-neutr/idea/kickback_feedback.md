# Idea rejected as infeasible — propose a CONSTRAINED replacement

Regeneration attempt 1 of 3. The previous idea (below) was judged infeasible for the execution environment. You MUST propose a SUBSTANTIALLY DIFFERENT idea in the same field that satisfies the feasibility constraint — do NOT re-state or lightly rephrase the rejected idea.

**Why it was rejected**: reason: flesh-out judged idea out of GHA-feasible scope
detected_at: 2026-06-21T09:55:31.210780+00:00

**Feasibility constraint**: the entire study must be executable by automated agents inside GitHub-Actions-class compute — public datasets or generated data only, no human subjects, no wet lab, no GPU training runs, no paid services.

## The rejected idea (for reference — do not reuse)

### the-impact-of-repeated-exposure-to-neutr.md

---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Repeated Exposure to Neutral Faces on Implicit Bias

**Field**: psychology

## Research question

How does repeated exposure to neutral faces from stigmatized groups affect implicit bias toward those groups compared to exposure to stereotypically congruent faces, and does this effect differ for individuals with high versus low baseline implicit bias?

## Motivation

Implicit biases toward stigmatized groups persist despite many intervention attempts. Repeated exposure to neutral, non‑stereotypical exemplars may attenuate automatic associations, yet the empirical evidence is sparse. Understanding whether neutral‑face exposure can reshape bias, and for whom it is most effective, would inform low‑cost, scalable prejudice‑reduction programs.

## Literature gap analysis

### What we searched
We queried four combinations of keywords on Semantic Scholar / arXiv / OpenAlex:  
1. “implicit bias repeated exposure faces intervention IAT”  
2. “mere exposure effect racial bias implicit association test”  
3. “counter‑stereotype exposure implicit bias reduction”  
4. “face exposure training prejudice reduction psychological study”

### What is known
- **[Neural Correlates of Face Familiarity Perception (2022)](https://arxiv.org/abs/2208.00352)** — Demonstrates neural signatures of face familiarity, providing a mechanistic basis for how repeated face exposure alters perceptual processing.  
- **[Optimal information gain at the onset of habituation to repeated stimuli (2023)](https://arxiv.org/abs/2301.12812)** — Shows how habituation to repeated stimuli modulates information processing, relevant for modeling the dynamics of exposure‑based interventions.

### What is NOT known
No published work has directly measured the impact of **repeated exposure to neutral faces from stigmatized groups** on **implicit bias** (as quantified by the Implicit Association Test), nor has any study compared this effect against exposure to **stereotypically congruent faces**. Moreover, it is unclear whether baseline levels of implicit bias moderate any observed change.

### Why this gap matters
Answering these questions would reveal whether a simple, low‑resource exposure regimen can meaningfully reduce automatic prejudice. Positive findings could be deployed in educational settings, corporate diversity training, and public‑health campaigns without requiring intensive or costly interventions.

### How this project addresses the gap
The proposed study will (1) use publicly available face image sets (e.g., the Chicago Face Database) to create neutral‑face and stereotypically‑congruent exposure streams, (2) leverage existing open‑access IAT datasets from Project Implicit, and (3) apply statistical models to test bias change and moderation by baseline bias—directly supplying the missing empirical evidence identified above.

## Expected results

We anticipate detecting a modest reduction in IAT scores after neutral‑face exposure relative to the congruent‑face control, with a larger effect for participants who start with higher baseline bias. A statistically significant interaction (exposure × baseline bias) would confirm that the intervention’s efficacy depends on initial prejudice levels. Null results would still be informative, indicating limits of mere‑exposure approaches.

## Methodology sketch

*The following steps respect the GitHub Actions free‑tier constraints (≤2 CPU cores, 7 GB RAM, no GPU, ≤6 h total runtime) and avoid any new data collection.*

1. **Download public resources**  
   - `wget` the Chicago Face Database (CFD) image archive and metadata (CC‑BY 4.0).  
   - `wget` the OpenPsych “Implicit Association Test” dataset (baseline IAT scores, publicly released under CC‑0).  
2. **Construct stimulus sets**  
   - From CFD, select neutral‑expression faces belonging to stigmatized racial groups (e.g., Black, Asian) and a matched set of neutral faces from non‑stigmatized groups.  
   - Create a “stereotypically congruent” set by pairing faces with affective expressions historically linked to stereotypes (e.g., angry Black faces, happy White faces) using the CFD affect‑rating labels.  
3. **Simulate exposure**  
   - For each participant record, generate a synthetic “exposure score” by counting how many times the participant’s demographic group appears in the neutral‑face set versus the congruent set, using the publicly available exposure‑simulation scripts from the OpenPsych repository. (No actual participants are recruited.)  
4. **Compute bias change**  
   - Estimate post‑exposure IAT scores by applying the published “exposure‑adjustment model” (available in the OpenPsych supplementary code) to baseline scores and the synthetic exposure scores.  
5. **Statistical analysis**  
   - Fit a mixed‑effects linear model: `post_IAT ~ exposure_type * baseline_IAT + (1|participant_id)`.  
   - Test the interaction term with a likelihood‑ratio test (α = 0.05).  
6. **Robustness checks**  
   - Repeat the analysis with bootstrapped resampling (1 000 iterations) to assess stability of the effect size.  
   - Conduct sensitivity analyses varying the proportion of neutral versus congruent faces (e.g., 70/30, 50/50).  
7. **Output**  
   - Save model summaries, effect‑size tables, and a concise PDF report (≤5 MB) in the repository’s `results/` folder.  

*All code will be written in Python (≥3.9) using `pandas`, `numpy`, `statsmodels`, and `matplotlib`, which run comfortably within the allotted resources.*

## Duplicate-check

- Reviewed existing ideas: *(none)*.  
- Closest match: *(none)*.  
- Verdict: **rejected — out of scope** (the methodology requires simulated exposure that does not correspond to real‑world experimental manipulation, violating the “no new data collection” rule).


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-21T09:55:18Z
**Outcome**: success_after_expansion
**Original term**: The Impact of Repeated Exposure to Neutral Faces on Implicit Bias psychology
**Verified citation count**: 6

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | The Impact of Repeated Exposure to Neutral Faces on Implicit Bias psychology | 0 |
| 1 | implicit bias modulation through repeated neutral face exposure | 0 |
| 2 | habituation to neutral facial stimuli and unconscious prejudice | 1 |
| 3 | repeated presentation of neutral faces and automatic bias | 2 |
| 4 | neutral face priming effects on implicit attitudes | 0 |
| 5 | face familiarity and implicit stereotyping | 1 |
| 6 | repeated neutral facial image exposure and implicit prejudice | 0 |
| 7 | exposure frequency of neutral faces and bias strength | 2 |
| 8 | visual exposure to neutral faces and implicit social cognition | 0 |
| 9 | neutral facial stimulus repetition and bias attenuation | 0 |
| 10 | repeated neutral face viewing and implicit racial bias | 0 |
| 11 | face exposure training for reduction of unconscious bias | 0 |
| 12 | implicit association changes after neutral face exposure | 0 |
| 13 | repeated facial exposure and automatic prejudice | 0 |
| 14 | visual habituation to faces and implicit attitude shift | 0 |
| 15 | repeated presentation of non‑emotional faces and implicit bias | 0 |
| 16 | neutral face exposure paradigm and implicit bias measurement | 0 |
| 17 | repeated neutral face exposure and implicit evaluation shifts | 0 |
| 18 | face exposure frequency effects on implicit bias | 0 |
| 19 | habituation to neutral faces and implicit stereotype activation | 0 |
| 20 | repeated neutral facial stimulus viewing and unconscious bias mitigation | 0 |

### Verified citations

1. **Optimal information gain at the onset of habituation to repeated stimuli** (2023). Giorgio Nicoletti, Matteo Bruzzone, Samir Suweis, Marco Dal Maschio, Daniel Maria Busiello. arXiv. [2301.12812](https://arxiv.org/abs/2301.12812). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Entity-Based Evaluation of Political Bias in Automatic Summarization** (2023). Karen Zhou, Chenhao Tan. arXiv. [2305.02321](https://arxiv.org/abs/2305.02321). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **On Measuring Gender Bias in Translation of Gender-neutral Pronouns** (2019). Won Ik Cho, Ji Won Kim, Seok Min Kim, Nam Soo Kim. arXiv. [1905.11684](https://arxiv.org/abs/1905.11684). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Neural Correlates of Face Familiarity Perception** (2022). Evan Ehrenberg, Kleovoulos Leo Tsourides, Hossein Nejati, Ngai-Man Cheung, Pawan Sinha. arXiv. [2208.00352](https://arxiv.org/abs/2208.00352). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **Fragmentation of the photoabsorption strength in neutral and charged metal microclusters** (2009). C. Yannouleas, R. A. Broglia, M. Brack, P. -F. Bortignon. arXiv. [0910.4576](https://arxiv.org/abs/0910.4576). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
6. **On temporal correlations in high-resolution frequency counting** (2016). Tim Dunker, Harald Hauglin, Ole Petter Rønningen. arXiv. [1604.05076](https://arxiv.org/abs/1604.05076). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*

