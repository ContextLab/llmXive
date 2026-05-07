---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

**Field**: psychology

## Research question

How does exposure to idealized self-presentation in online social environments affect subsequent self-evaluation among users?

## Motivation

Social comparison is a well-established psychological mechanism, but the prevalence of highly-curated, selectively-edited self-presentation online creates conditions where upward comparison may be systematically amplified. Understanding whether and how exposure to idealized profiles predicts negative self-evaluation indicators is critical for both theoretical models of social comparison and practical interventions for digital well-being. Current research has not adequately isolated the specific impact of idealized content exposure from general social media use.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using search terms including "social comparison online self-evaluation," "idealized self-presentation social media impact," and "social comparison theory digital environments." Two papers were returned that intersect with online social environments but do not directly address the core research question.

### What is known

- [Understanding Online Polarization Through Human-Agent Interaction in a Synthetic LLM-Based Social Network (2025)](http://arxiv.org/abs/2506.15866v1) — This work establishes methodological approaches for studying human behavior in synthetic online environments, though it focuses on polarization rather than self-evaluation.
- [Information Consumption and Boundary Spanning in Decentralized Online Social Networks: the case of Mastodon Users (2022)](http://arxiv.org/abs/2203.15752v3) — This research examines information patterns in decentralized social networks but does not investigate psychological outcomes of social comparison.

### What is NOT known

No published work has directly measured the correlation between exposure frequency to idealized self-presentations and self-evaluation indicators using publicly available social media data. Existing studies either focus on centralized platforms without isolating idealized content exposure, or examine behavioral patterns without psychological outcome measures. There is no established baseline for how upward social comparison manifests linguistically in user-generated content.

### Why this gap matters

Filling this gap would enable evidence-based interventions for digital well-being, inform platform design decisions around content moderation and recommendation algorithms, and provide empirical grounding for theories of social comparison in digital contexts. Understanding the specific mechanisms of online social comparison could support mental health initiatives and policy decisions around social media use.

### How this project addresses the gap

Our methodology will quantify exposure to idealized content using publicly available social media datasets and measure self-evaluation indicators through linguistic analysis, directly testing the correlation between these two variables. This provides the first empirical baseline for the relationship between idealized content exposure and self-evaluation in online environments.

## Expected results

We expect to find a moderate positive correlation between frequency of exposure to idealized self-presentations and linguistic indicators of negative self-evaluation. Confirmation would support theoretical models of upward social comparison in digital contexts; a null result would suggest that idealized content exposure may be less impactful than general social media use, prompting alternative explanatory models. Either outcome would provide novel empirical evidence for this research area.

## Methodology sketch

- Download publicly available Reddit comment datasets from Pushshift archive (https://pushshift.io/reddit-datasets/) focusing on self-disclosure and mental health subreddits
- Download Twitter/X public dataset samples from HuggingFace Datasets (https://huggingface.co/datasets) for cross-platform validation
- Develop text classification model to identify idealized self-presentation content (using pre-trained BERT model from HuggingFace, no fine-tuning required)
- Apply NLP sentiment analysis and self-reference detection (using NLTK or spaCy) to identify self-evaluation indicators in user comments
- Calculate exposure frequency metrics for each user based on idealized content visibility in their timeline/feed
- Perform statistical correlation analysis (Pearson's r or Spearman's rho) between exposure frequency and self-evaluation indicator scores
- Control for confounding variables (total social media usage time, demographic factors where available) using multiple regression
- Generate visualizations (scatter plots, correlation matrices) using matplotlib/seaborn
- Document all data sources, preprocessing steps, and statistical parameters for reproducibility
- Validate results across multiple subreddits/platforms to assess generalizability

## Duplicate-check

- Reviewed existing ideas: Social Comparison in Digital Environments, Online Self-Presentation and Well-being, Digital Social Media Psychological Impact.
- Closest match: Social Comparison in Digital Environments (similarity sketch: both address online social comparison but this project specifically isolates idealized content exposure).
- Verdict: NOT a duplicate
