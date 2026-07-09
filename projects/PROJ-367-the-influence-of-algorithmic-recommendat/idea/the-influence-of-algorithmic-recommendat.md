---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

**Field**: psychology

## Research question

How does the content diversity of algorithmic recommendations (logged separately from user clicks) predict subsequent learner course topic diversity, controlling for baseline interests?

## Motivation

Online learning platforms increasingly rely on recommendation algorithms optimized for engagement, yet the extent to which these systems constrain or facilitate intellectual curiosity remains empirically unverified. This question addresses a critical gap between algorithmic design goals (maximizing time-on-platform via relevance) and educational outcomes (broad skill development). Understanding this dynamic is essential for designing platforms that support both learner retention and diverse knowledge acquisition.

## Literature gap analysis

### What we searched

Searched Semantic Scholar, arXiv, and OpenAlex using queries: (1) "algorithmic recommendation diversity online learning" and (2) "recommendation system exploration exploitation learner behavior." Retrieved 2 papers total; results primarily addressed theoretical models of agency or social dilemma tasks rather than empirical analysis of recommendation diversity effects on human learner behavior in educational contexts.

### What is known

- [Improved cooperation by balancing exploration and exploitation in intertemporal social dilemma tasks (2021)](https://arxiv.org/abs/2111.09152) — Establishes that exploration-exploitation tradeoffs operate in human decision-making contexts, though not specifically in online learning environments or regarding algorithmic curation.
- [Active Inference as a Model of Agency (2024)](https://arxiv.org/abs/2401.12917) — Provides a theoretical framework for agency and behavior selection that could inform how learners respond to external constraints, but does not empirically test recommendation system effects.

### What is NOT known

No published work has quantitatively measured how the *content diversity* of a logged recommendation feed (distinct from user interaction) predicts subsequent learner topic diversity in online education. There is a lack of empirical evidence distinguishing whether algorithmic curation narrows learning paths through content filtering or if learners maintain agency to explore diverse topics despite homogeneous recommendations.

### Why this gap matters

Platform designers and policymakers need empirical evidence to balance engagement metrics with educational breadth. If recommendation diversity is a causal driver of learning diversity, platforms could optimize for serendipity without sacrificing engagement; conversely, if learners self-curate regardless of recommendations, interventions might focus elsewhere.

### How this project addresses the gap

This project will analyze public enrollment datasets with available recommendation logs to isolate the effect of recommendation content diversity on subsequent learner behavior, controlling for baseline interests. By separating the input (recommendations) from the output (enrollments), we provide the first direct test of whether algorithmic curation drives exploration-exploitation tradeoffs in this domain.

## Expected results

We expect to observe a positive correlation between recommendation content diversity and subsequent learner course topic diversity, even after controlling for baseline interests. A statistically significant effect (p<0.05, partial eta-squared > 0.05) would confirm that algorithmic exposure shapes learning paths; a null result would suggest learner agency overrides algorithmic influence. Either outcome would be publishable as it constrains current assumptions about the power of recommendation systems in educational settings.

## Methodology sketch

- Download public course enrollment datasets with recommendation logs from OpenML or Zenodo (e.g., "MOOC Recommendation Logs" or similar repositories); explicitly verify the presence of distinct columns for "recommended items" and "enrolled items."
- Preprocess data to compute a "Recommendation Diversity Score" for each user session using Shannon entropy on the category distribution of the *recommended* list (independent of clicks).
- Compute a "Learner Diversity Score" for the subsequent session using Shannon entropy on the *enrolled* course categories.
- Derive a "Baseline Interest Vector" for each user from their pre-study enrollment history (prior to the observation window) to control for intrinsic topic preferences.
- Fit a linear mixed-effects model: `Learner_Diversity ~ Recommendation_Diversity + Baseline_Interest + (1|User_ID)`, ensuring the predictor (recommendations) and outcome (enrollments) are temporally and logically distinct.
- Perform a robustness check using a permutation test where recommendation diversity labels are shuffled to ensure the observed effect is not due to unmeasured user-level confounders.
- Validate model assumptions (normality of residuals, homoscedasticity) and report effect sizes (Cohen's f²) alongside p-values.
- Visualize results using partial regression plots showing the relationship between recommendation diversity and learner diversity at fixed levels of baseline interest.
- Document all data sources with DOIs/URLs and provide reproducible code for the entire pipeline in a public repository.

## Duplicate-check

- Reviewed existing ideas: [N/A — no existing fleshed-out ideas in corpus]
- Closest match: [None]
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-09T16:48:14Z
**Outcome**: exhausted
**Original term**: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning psychology
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning psychology | 0 |
| 1 | algorithmic curation effects on learner curiosity | 0 |
| 2 | recommender systems and exploratory behavior in education | 3 |
| 3 | exploitation bias in adaptive learning platforms | 0 |
| 4 | filter bubbles and knowledge exploration in students | 0 |
| 5 | algorithmic nudging versus self-directed learning | 0 |
| 6 | impact of personalized feeds on cognitive exploration | 0 |
| 7 | reinforcement learning trade-offs in educational technology | 0 |
| 8 | algorithmic determinism in online course navigation | 0 |
| 9 | recommendation algorithms and serendipity in learning | 0 |
| 10 | confirmation bias induced by educational recommenders | 0 |
| 11 | passive versus active learning with algorithmic support | 0 |
| 12 | diversity of content exposure in adaptive tutoring | 0 |
| 13 | algorithmic influence on information seeking strategies | 0 |
| 14 | narrowing of learning paths due to predictive analytics | 0 |
| 15 | user agency in algorithmically mediated learning environments | 0 |
| 16 | exploration-exploitation dilemma in digital pedagogy | 0 |
| 17 | algorithmic homogenization of student knowledge acquisition | 0 |
| 18 | effects of feed-based learning on critical thinking | 0 |
| 19 | computational personalization and learner autonomy | 0 |
| 20 | algorithmic feedback loops in educational decision making | 0 |

### Verified citations

1. **Improved cooperation by balancing exploration and exploitation in intertemporal social dilemma tasks** (2021). Zhenbo Cheng, Xingguang Liu, Leilei Zhang, Hangcheng Meng, Qin Li, et al.. arXiv. [2111.09152](https://arxiv.org/abs/2111.09152). PDF-sampled: No.
2. **Active Inference as a Model of Agency** (2024). Lancelot Da Costa, Samuel Tenka, Dominic Zhao, Noor Sajid. arXiv. [2401.12917](https://arxiv.org/abs/2401.12917). PDF-sampled: No.
