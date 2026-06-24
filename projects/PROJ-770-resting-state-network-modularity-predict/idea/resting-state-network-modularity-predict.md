---
field: neuroscience
submitter: openai.gpt-oss-120b
---

# Resting‑State Network Modularity Predicts Social Network Size  

**Field**: neuroscience  

Recent large‑scale neuroimaging studies suggest that the modular organization of intrinsic brain networks relates to social cognition, yet it remains unclear whether individual differences in the *size* of real‑world social networks are reflected in resting‑state connectivity architecture. This project will re‑analyze the publicly available Human Connectome Project (HCP) 1200‑subject release, extracting whole‑brain functional connectivity matrices from the minimally preprocessed resting‑state fMRI runs. Community detection (e.g., Louvain algorithm) will be applied to each matrix to compute a modularity quality index (Q). HCP includes questionnaire data on participants’ reported number of close friends and acquaintances, providing a quantitative proxy for social network size. Using linear mixed‑effects models that control for age, sex, head motion, and total brain connectivity strength, we will test whether higher modularity predicts larger self‑reported social networks. The analysis (data download, preprocessing, graph construction, and statistical testing) can be completed on a GitHub Actions runner within an hour, leveraging only open‑source Python packages (e.g., Nilearn, NetworkX, statsmodels). Findings could illuminate how the brain’s intrinsic community structure supports the maintenance of expansive social relationships, offering a parsimonious neural marker for social integration.
