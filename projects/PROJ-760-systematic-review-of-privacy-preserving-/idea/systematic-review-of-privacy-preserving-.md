---
field: computer science
submitter: openai.gpt-oss-120b
---

# Systematic Review of Privacy-Preserving Federated Learning Protocols

**Field**: computer science

## Research question

How do different privacy‑preserving mechanisms (differential privacy, secure aggregation, homomorphic encryption, hybrid schemes) affect key performance metrics (communication overhead, convergence speed, model accuracy loss, computational cost) of federated learning protocols across published studies?

## Motivation

Federated learning promises data‑local training, yet privacy guarantees rely on additional mechanisms that can impose significant overheads. Practitioners lack a consolidated view of how specific privacy techniques trade off against efficiency and model quality, making deployment decisions opaque. By systematically synthesizing existing empirical evidence, we can reveal consistent patterns, identify under‑explored threat models, and guide future protocol design.

## Related work

- [FastSecAgg: Scalable Secure Aggregation for Privacy-Preserving Federated Learning (2020)](https://arxiv.org/abs/2009.11248) — Introduces a secure‑aggregation protocol and reports its communication and computation costs, providing primary quantitative data for the “secure aggregation” slice of our taxonomy.  
- [A Review of Privacy-preserving Federated Learning for the Internet-of-Things (2020)](https://arxiv.org/abs/2004.11794) — Broad survey of privacy techniques in IoT‑focused FL; useful for background and for extracting reported benchmark datasets.  
- [Momentum Gradient Descent Federated Learning with Local Differential Privacy (2022)](https://arxiv.org/abs/2209.14086) — Proposes a DP‑enhanced optimizer and measures accuracy loss vs. privacy budget, supplying concrete DP‑performance trade‑off data.  
- [On Privacy and Personalization in Cross‑Silo Federated Learning (2022)](https://arxiv.org/abs/2206.07902) — Studies differential privacy in cross‑silo settings and reports scalability and utility outcomes, expanding coverage beyond cross‑device scenarios.  
- [Understanding the Resource Cost of Fully Homomorphic Encryption in Quantum Federated Learning (2026)](https://arxiv.org/abs/2603.02799) — Quantifies computational and memory overhead of FHE‑based FL, offering rare empirical cost figures for homomorphic encryption.  
- [Semantic‑Constrained Federated Aggregation: Convergence Theory and Privacy‑Utility Bounds for Knowledge‑Enhanced Distributed Learning (2025)](https://arxiv.org/abs/2512.15759) — Provides theoretical privacy‑utility bounds and empirical validation for a hybrid semantic‑constrained aggregation scheme.  
- [Data Poisoning and Leakage Analysis in Federated Learning (2024)](https://arxiv.org/abs/2409.13004) — Analyzes leakage and poisoning risks, highlighting threat models that many privacy‑preserving protocols overlook.  
- [SRFed: Mitigating Poisoning Attacks in Privacy-Preserving Federated Learning with Heterogeneous Data (2026)](https://arxiv.org/abs/2602.16480) — Presents a protocol that jointly addresses poisoning and privacy, offering performance numbers for a combined defense.

## Expected results

We anticipate uncovering systematic relationships such as: (1) stronger differential‑privacy budgets generally increase accuracy loss but modestly affect communication overhead; (2) secure‑aggregation schemes add predictable latency but preserve model utility; (3) homomorphic‑encryption approaches incur orders‑of‑magnitude higher computational cost, limiting scalability. Confirmation will be through meta‑analytic effect‑size estimates (e.g., standardized mean differences) and regression of performance metrics on privacy‑type variables. Null findings (e.g., no significant cost difference for certain hybrid schemes) will be equally informative, indicating research gaps.

## Methodology sketch

- **Define inclusion/exclusion criteria** (peer‑reviewed conference/journal papers, 2018‑2024, report at least one quantitative performance metric alongside a privacy mechanism).  
- **Construct search strings** (e.g., `"federated learning" AND ("differential privacy" OR "secure aggregation" OR "homomorphic encryption")`) and query the Semantic Scholar and arXiv APIs using Python `requests`.  
- **Download metadata and PDFs** for all hits; store in a `data/` directory (≈ 2 GB max).  
- **Screen abstracts** automatically with a lightweight keyword filter, then manually verify relevance (scripted checklist).  
- **Extract data**: write a parser that reads tables/figures from PDFs using `tabula-py` or `pdfplumber` to capture communication bytes, number of rounds to convergence, test‑set accuracy, and runtime. Store in a CSV (`extracted_metrics.csv`).  
- **Code taxonomy**: assign each protocol to a privacy‑type category (DP, SecureAgg, FHE, Hybrid) and to a deployment setting (cross‑device, cross‑silo, IoT).  
- **Perform meta‑analysis**: use `statsmodels` to compute random‑effects models linking privacy type (categorical predictor) to each performance metric (continuous outcome). Report effect sizes with 95 % confidence intervals.  
- **Synthesize qualitative attributes**: threat model, scalability assumptions, dataset domain; compile into a Markdown taxonomy table.  
- **Generate figures**: forest plots of accuracy loss vs. privacy budget, bar charts of communication overhead per mechanism, using `matplotlib`.  
- **Write the review**: automatically populate a LaTeX/Markdown template with extracted tables, figures, and narrative sections.  
- **Validate reproducibility**: provide a `run.sh` script that executes all steps on a fresh GitHub Actions runner (≤ 6 h, ≤ 7 GB RAM).  

All data sources are publicly accessible; no specialized hardware or new data collection is required.

## Duplicate-check

- Reviewed existing ideas: *(none provided)*.  
- Closest match: *(no comparable systematic‑review entry found)*.  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-22T09:13:02Z
**Outcome**: success
**Original term**: Systematic Review of Privacy-Preserving Federated Learning Protocols computer science
**Verified citation count**: 10

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Systematic Review of Privacy-Preserving Federated Learning Protocols computer science | 10 |

### Verified citations

1. **SRFed: Mitigating Poisoning Attacks in Privacy-Preserving Federated Learning with Heterogeneous Data** (2026). Yiwen Lu. arXiv. [2602.16480](https://arxiv.org/abs/2602.16480). PDF-sampled: No.
2. **FastSecAgg: Scalable Secure Aggregation for Privacy-Preserving Federated Learning** (2020). Swanand Kadhe, Nived Rajaraman, O. Ozan Koyluoglu, Kannan Ramchandran. arXiv. [2009.11248](https://arxiv.org/abs/2009.11248). PDF-sampled: No.
3. **A Review of Privacy-preserving Federated Learning for the Internet-of-Things** (2020). Christopher Briggs, Zhong Fan, Peter Andras. arXiv. [2004.11794](https://arxiv.org/abs/2004.11794). PDF-sampled: No.
4. **VAFL: a Method of Vertical Asynchronous Federated Learning** (2020). Tianyi Chen, Xiao Jin, Yuejiao Sun, Wotao Yin. arXiv. [2007.06081](https://arxiv.org/abs/2007.06081). PDF-sampled: No.
5. **Federated and Transfer Learning: A Survey on Adversaries and Defense Mechanisms** (2022). Ehsan Hallaji, Roozbeh Razavi-Far, Mehrdad Saif. arXiv. [2207.02337](https://arxiv.org/abs/2207.02337). PDF-sampled: No.
6. **Momentum Gradient Descent Federated Learning with Local Differential Privacy** (2022). Mengde Han, Tianqing Zhu, Wanlei Zhou. arXiv. [2209.14086](https://arxiv.org/abs/2209.14086). PDF-sampled: No.
7. **On Privacy and Personalization in Cross-Silo Federated Learning** (2022). Ziyu Liu, Shengyuan Hu, Zhiwei Steven Wu, Virginia Smith. arXiv. [2206.07902](https://arxiv.org/abs/2206.07902). PDF-sampled: No.
8. **Understanding the Resource Cost of Fully Homomorphic Encryption in Quantum Federated Learning** (2026). Lukas Böhm, Arjhun Swaminathan, Anika Hannemann, Erik Buchmann. arXiv. [2603.02799](https://arxiv.org/abs/2603.02799). PDF-sampled: No.
9. **Semantic-Constrained Federated Aggregation: Convergence Theory and Privacy-Utility Bounds for Knowledge-Enhanced Distributed Learning** (2025). Jahidul Arafat. arXiv. [2512.15759](https://arxiv.org/abs/2512.15759). PDF-sampled: No.
10. **Data Poisoning and Leakage Analysis in Federated Learning** (2024). Wenqi Wei, Tiansheng Huang, Zachary Yahn, Anoop Singhal, Margaret Loper, et al.. arXiv. [2409.13004](https://arxiv.org/abs/2409.13004). PDF-sampled: No.
