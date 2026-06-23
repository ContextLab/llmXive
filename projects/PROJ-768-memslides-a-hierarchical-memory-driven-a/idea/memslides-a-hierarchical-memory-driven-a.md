---
field: linguistics
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/351
paper_authors:
  - Ye Jin
  - Yangyang Xu
  - Jun Zhu
  - Yibo Yang
---

# MemSlides: A Hierarchical Memory‑Driven Agent Framework for Personalized Slide Generation with Multi‑turn Local Revision  

**Field**: linguistics  

## Research question  

How does the inclusion of a hierarchical memory architecture (persistent user‑profile memory + session‑level working memory) in a language‑model‑based agent affect (i) the personalization of generated slide content to a user’s stated preferences and (ii) the coherence of the deck across multi‑turn local revisions, compared with a flat‑memory baseline?  

## Motivation  

Personalized slide decks are increasingly produced by LLM agents, yet current systems struggle to retain user preferences over a dialogue and to keep revisions globally coherent. A memory hierarchy that separates long‑term persona information from short‑term interaction state offers a principled way to address these gaps, but its actual impact on slide quality has not been empirically demonstrated.  

## Related work  

- [Training Language Models with Memory Augmentation (2022)](https://arxiv.org/abs/2205.12674) — Introduces non‑parametric memory modules for LMs, providing the core technical building block for hierarchical memory in our agent.  
- [A2P-Vis: an Analyzer-to-Presenter Agentic Pipeline for Visual Insights Generation and Reporting (2025)](https://arxiv.org/abs/2512.22101) — Presents an end‑to‑end agentic pipeline that assembles generated visual artifacts into a coherent report, analogous to slide‑deck assembly and highlighting the need for coordinated multi‑step generation.  
- [AutoStudio: Crafting Consistent Subjects in Multi‑turn Interactive Image Generation (2024)](https://arxiv.org/abs/2406.01388) — Studies multi‑turn interactive generation and shows how consistency degrades without explicit memory handling, motivating our focus on revision coherence.  
- [When Memory Becomes a Vulnerability: Towards Multi‑turn Jailbreak Attacks against Text‑to‑Image Generation Systems (2025)](https://arxiv.org/abs/2504.20376) — Analyzes how memory mechanisms can be exploited in multi‑turn settings, underscoring the importance of robust memory design for reliable slide generation.  
- [The distribution of discourse relations within and across turns in spontaneous conversation (2023)](https://arxiv.org/abs/2307.03645) — Provides a discourse‑relations framework useful for measuring coherence across successive slide‑revision turns.  

## Expected results  

We expect that the hierarchical‑memory agent will (a) achieve higher alignment scores between generated slide text and synthetic user‑profile specifications (e.g., ↑ 10 % average semantic similarity) and (b) produce decks with significantly better discourse‑coherence metrics across revision turns (e.g., ↑ 0.12 Δ entity‑grid score). Paired statistical tests (two‑tailed t‑tests, α = 0.05) and effect‑size estimates (Cohen’s d) will confirm whether these improvements are reliable.  

## Methodology sketch  

- **Data acquisition**  
  1. Download a public collection of lecture slide PDFs from the *arXiv* “cs.LG” category (≈ 200 decks) via `wget`.  
  2. Extract slide text using `pdfminer.six` and store as JSON‑lines (`slide_id`, `text`).  
  3. Synthesize 100 user‑profile specifications (topic interests, preferred tone, visual style) via templated prompts to an open‑source LLM (e.g., Llama‑2‑7B).  

- **Model implementation**  
  4. Install the memory‑augmented LM code from the 2022 “Training Language Models with Memory Augmentation” repository (pip install `memlm`).  
  5. Build two agent variants:  
     - **Hierarchical‑Memory Agent**: persistent profile memory + session working memory (as described in the MemSlides proposal).  
     - **Flat‑Memory Baseline**: a single short‑term cache without long‑term profile storage.  

- **Slide generation & multi‑turn revision**  
  6. For each profile, prompt the agent to generate an initial slide deck (≈ 10 slides) from a given topic.  
  7. Simulate a local revision turn by providing feedback (“increase formality”, “add more examples”) and let the agent revise only the affected slides, repeating for three turns.  

- **Evaluation metrics**  
  8. **Personalization**: compute semantic similarity between generated slide sentences and the profile’s preference keywords using SBERT embeddings; average over slides.  
  9. **Coherence**: apply the discourse‑relation classifier from the 2023 conversation paper to successive slide pairs and derive an entity‑grid coherence score across the whole deck.  
  10. Record runtime and memory usage for each turn (to confirm feasibility on a 2‑core, 7 GB runner).  

- **Statistical analysis**  
  11. Perform paired t‑tests comparing hierarchical vs. flat agents on personalization and coherence scores across all profiles and random seeds (3 seeds).  
  12. Report 95 % confidence intervals and Cohen’s d effect sizes.  

- **Reproducibility**  
  13. All scripts, exact dependency versions (`requirements.txt`), random seeds, and the synthetic profile bank are archived in a Zenodo‑linked GitHub release.  

## Duplicate-check  

- Reviewed existing ideas: *(none)*.  
- Closest match: *(none)*.  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-23T11:25:36Z
**Outcome**: success_after_expansion
**Original term**: MemSlides: A Hierarchical Memory Driven Agent Framework for Personalized Slide Generation with Multi-turn Local Revision linguistics
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | MemSlides: A Hierarchical Memory Driven Agent Framework for Personalized Slide Generation with Multi-turn Local Revision linguistics | 0 |
| 1 | hierarchical memory‑augmented language models for slide authoring | 1 |
| 2 | personalized presentation generation using neural agents | 3 |
| 3 | multi‑turn text revision in discourse generation | 5 |
| 4 | adaptive content generation with hierarchical memory networks | 0 |
| 5 | local editing strategies for automated slide creation | 0 |
| 6 | memory‑driven natural language generation for educational materials | 0 |
| 7 | agent‑based slide synthesis with contextual memory | 0 |
| 8 | hierarchical attention mechanisms for presentation text generation | 0 |
| 9 | iterative revision models for personalized lecture slides | 0 |
| 10 | neural memory architectures for discourse structuring | 0 |
| 11 | dynamic slide generation via multi‑turn dialogue systems | 0 |
| 12 | personalized slide deck construction using transformer memory | 0 |
| 13 | context‑aware language generation for visual presentations | 0 |
| 14 | hierarchical encoder‑decoder models for slide content | 0 |
| 15 | local revision modeling in automated document drafting | 0 |
| 16 | memory‑augmented agents for adaptive educational content | 0 |
| 17 | multi‑step text generation for presentation design | 0 |
| 18 | discourse‑aware slide generation frameworks | 0 |
| 19 | incremental revision in neural language generation | 0 |
| 20 | personalized educational slide generation with hierarchical memory | 0 |

### Verified citations

1. **Training Language Models with Memory Augmentation** (2022). Zexuan Zhong, Tao Lei, Danqi Chen. arXiv. [2205.12674](https://arxiv.org/abs/2205.12674). PDF-sampled: No.
2. **A2P-Vis: an Analyzer-to-Presenter Agentic Pipeline for Visual Insights Generation and Reporting** (2025). Shuyu Gan, Renxiang Wang, James Mooney, Dongyeop Kang. arXiv. [2512.22101](https://arxiv.org/abs/2512.22101). PDF-sampled: No.
3. **AutoStudio: Crafting Consistent Subjects in Multi-turn Interactive Image Generation** (2024). Junhao Cheng, Xi Lu, Hanhui Li, Khun Loun Zai, Baiqiao Yin, et al.. arXiv. [2406.01388](https://arxiv.org/abs/2406.01388). PDF-sampled: No.
4. **When Memory Becomes a Vulnerability: Towards Multi-turn Jailbreak Attacks against Text-to-Image Generation Systems** (2025). Shiqian Zhao, Jiayang Liu, Yiming Li, Runyi Hu, Xiaojun Jia, et al.. arXiv. [2504.20376](https://arxiv.org/abs/2504.20376). PDF-sampled: No.
5. **The distribution of discourse relations within and across turns in spontaneous conversation** (2023). S. Magalí López Cortez, Cassandra L. Jacobs. arXiv. [2307.03645](https://arxiv.org/abs/2307.03645). PDF-sampled: No.
