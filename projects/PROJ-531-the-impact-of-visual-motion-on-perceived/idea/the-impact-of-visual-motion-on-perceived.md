---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Visual Motion on Perceived Agency in Virtual Interactions

**Field**: psychology

## Research question

How do visual motion characteristics of virtual avatars (e.g., smoothness, responsiveness delay, and anticipatory lead cues) influence users' subjective sense of agency during virtual interactions?

## Motivation

Agency—the feeling of control over one's actions and their consequences—is well-studied in physical embodied contexts but remains underexplored when interactions occur solely through visual motion cues in virtual environments. Understanding which motion features predict agency could inform design principles for more intuitive virtual reality, telepresence, and human-robot interfaces. This gap matters because poor agency experiences in virtual systems undermine usability and trust, yet current design guidelines lack evidence-based motion specifications.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using search terms including "visual motion agency virtual reality," "avatar motion perception control," "embodied agency VR," and "virtual interaction motion cues." The searches returned approximately 15–20 results across all sources, but the majority focused on general VR usability, presence, or immersion rather than agency specifically. Only one broadly relevant source was identified in the verified literature block.

### What is known

- [Enhancing Our Lives with Immersive Virtual Reality (2016)](https://doi.org/10.3389/frobt.2016.00074) — This review establishes VR hardware and design foundations but does not specifically address the relationship between motion characteristics and perceived agency.

### What is NOT known

No published work has systematically measured how specific visual motion parameters (e.g., latency, smoothness, anticipatory cues) predict subjective agency ratings in virtual avatar interactions. The existing VR literature focuses on presence and immersion rather than the control-feeling dimension of agency. There is also no consensus on which motion features should be prioritized when designing for agency.

### Why this gap matters

Filling this gap would enable evidence-based motion design for virtual environments where users interact with avatars (e.g., telepresence, remote collaboration, virtual training). Improved agency experiences could increase trust and engagement in virtual systems, with practical implications for VR industry standards and human-robot interaction protocols.

### How this project addresses the gap

This project will analyze publicly available human-avatar interaction datasets to quantify correlations between measurable motion features (response latency, trajectory smoothness, lead time) and validated agency scale scores. The methodology extracts motion parameters from interaction logs and applies statistical modeling to identify which features most strongly predict agency ratings.

## Expected results

We expect to identify 1–2 motion features that significantly predict agency ratings (e.g., response latency below 100ms or smoothness above a threshold), while other features show weak or no correlation. A null result (no motion features predict agency) would be equally informative, suggesting agency in virtual contexts may depend on other factors (e.g., task design, prior experience). We will use regression models with cross-validation to establish the level of evidence needed for robust claims.

## Methodology sketch

- Download publicly available human-avatar interaction datasets from OpenML or HuggingFace Datasets (search for "VR interaction," "avatar," or "human-computer interaction" datasets with motion logs and questionnaire responses).
- Extract motion features from interaction logs: response latency (ms), trajectory smoothness (jerk metric), and anticipatory lead time (ms).
- Clean and preprocess agency scale responses (e.g., Likert-scale agency questionnaires) to create a continuous outcome variable.
- Split data into training (70%) and test (30%) sets to prevent overfitting.
- Fit multiple linear regression and random forest models to predict agency scores from motion features.
- Perform 5-fold cross-validation to assess model stability and generalizability.
- Compute feature importance scores and partial dependence plots to interpret which motion features drive agency predictions.
- Conduct statistical significance testing (t-tests or ANOVA) comparing agency ratings across motion feature quartiles.
- Generate visualizations: scatter plots of motion features vs. agency scores, model performance metrics, and feature importance rankings.
- Document all code, data sources, and analysis steps for reproducibility on GitHub Actions runners.

## Duplicate-check

- Reviewed existing ideas: [None provided in input — unable to perform semantic similarity check]
- Closest match: [No existing ideas to compare]
- Verdict: NOT a duplicate (no corpus provided for comparison; requires existing_idea_paths input for proper duplicate detection)
