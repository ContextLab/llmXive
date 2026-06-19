---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/205
---

# SkillsVote: Lifecycle Governance of Agent Skills from Collection, Recommendation to Evolution

**Field**: linguistics  

## Research question

How does applying a structured lifecycle‑governance pipeline (collection → recommendation → evolution) to agent skill libraries affect (i) the safety of deployed LLM agents (measured by an independent unsafe‑skill detection classifier) and (ii) their task performance on benchmark suites, compared with agents that use ungoverned skill collections?

## Motivation

Large‑language‑model (LLM) agents increasingly rely on reusable “skill” artifacts to extend their capabilities, yet these skill libraries are often noisy, unvetted, and evolve without systematic oversight. Without independent governance, agents may adopt unsafe or low‑quality skills, undermining reliability and alignment. Demonstrating that a lightweight, version‑controlled governance workflow can improve safety while preserving or enhancing performance would provide a concrete, reproducible blueprint for responsible agent development.

## Related work
- [SkillsVote: Lifecycle Governance of Agent Skills from Collection, Recommendation to Evolution (2026)](https://arxiv.org/abs/2605.18401) — Introduces the SkillsVote framework and highlights the need for structured skill governance.  
- [Agent Skills for Large Language Models: Architecture, Acquisition, Security, and the Path Forward (2026)](https://arxiv.org/abs/2602.12430) — Surveys modular skill‑equipped agents and discusses security concerns, providing a broad architectural context.  
- [Memento‑Skills: Let Agents Design Agents (2026)](https://arxiv.org/abs/2603.18743) — Presents a continual‑learning agent that autonomously creates and adapts skills, illustrating the challenges of uncontrolled skill evolution.  
- [Toward User Comprehension Supports for LLM Agent Skill Specifications (2026)](https://arxiv.org/abs/2605.19362) — Studies how users interpret SKILL markdown specifications and the need for audit mechanisms, motivating the recommendation component.  
- [Dynamic Skill Lifecycle Management for Agentic Reinforcement Learning (2026)](https://arxiv.org/abs/2605.10923) — Explores modular skill usage in reinforcement‑learning agents and motivates systematic lifecycle management.  
- [Skill‑as‑Pseudocode: Refactoring Skill Libraries to Pseudocode for LLM Agents (2026)](https://arxiv.org/abs/2605.27955) — Shows how unstructured skill representations hinder reliable retrieval, supporting the case for curated recommendation and evolution steps.

## Expected results

We expect that agents using the governed skill pipeline will (a) exhibit a statistically significant reduction in unsafe‑skill activations (≥ 30 % relative drop, p < 0.05, paired bootstrap) and (b) achieve comparable or modestly higher benchmark scores (≥ 1 % absolute gain on avg@5 Accuracy) relative to the ungoverned baseline. The combination of safety improvement and non‑degraded performance would validate the utility of lifecycle governance.

## Methodology sketch
- **Data acquisition**
  - Download the publicly released “million‑scale” skill corpus used in the original SkillsVote paper (URL provided in the paper’s supplemental material).
  - Retrieve benchmark datasets: Terminal‑Bench 2.0 and SWE‑Bench Pro via their open‑access Zenodo releases.
- **Governance pipeline implementation**
  1. **Collection**: Parse each `SKILL.md` file, extract metadata (author, version, declared safety tags) into a JSON‑Schema‑validated registry (schema derived from the SkillsVote specification).
  2. **Recommendation**: Build a BM25 index over skill descriptions; for each benchmark task, retrieve the top‑k candidate skills. Apply a lightweight safety classifier (fine‑tuned on a public unsafe‑skill dataset) to filter out flagged candidates.
  3. **Evolution**: Allow agents to propose edits to selected skills; each edit passes through a sandboxed static‑analysis checker that rejects scripts containing disallowed commands (e.g., `rm -rf`, network calls). Approved edits are version‑controlled via Git.
- **Agent evaluation**
  - Instantiate a frozen LLM (e.g., Llama‑2‑7B‑chat from HuggingFace) as the base agent.
  - Run the agent on each benchmark task twice: (i) with the **governed** skill library, (ii) with the **raw** library (baseline).
  - Record task‑level metrics (avg@5 Accuracy, Resolve Rate) and log every skill invocation.
- **Safety measurement**
  - Apply an independent unsafe‑skill detection model (trained on the “SafeSkill” corpus) to the logged invocations, yielding a binary unsafe‑skill count per run.
- **Statistical analysis**
  - Compute paired differences in performance and unsafe‑skill counts across the two conditions.
  - Perform paired bootstrap resampling (10 000 samples) to obtain confidence intervals and p‑values.
  - Report mean ± standard deviation and effect sizes (Cohen’s d).
- **Reproducibility**
  - All scripts, environment files (`environment.yml`), and a GitHub Actions workflow are version‑controlled; the workflow downloads data, runs the evaluation, and produces a PDF report within the 6‑hour free‑tier limit.

## Duplicate-check
- Reviewed existing ideas: *none*.
- Closest match: *none* (no semantically similar fleshed‑out idea found in the corpus).
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-19T13:49:36Z
**Outcome**: success_after_expansion
**Original term**: SkillsVote: Lifecycle Governance of Agent Skills from Collection, Recommendation to Evolution linguistics
**Verified citation count**: 6

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | SkillsVote: Lifecycle Governance of Agent Skills from Collection, Recommendation to Evolution linguistics | 0 |
| 1 | agent skill lifecycle management | 5 |
| 2 | skill governance frameworks for conversational agents | 0 |
| 3 | skill acquisition and evolution in language models | 0 |
| 4 | automated skill collection and recommendation systems | 0 |
| 5 | competency ontology evolution for NLP agents | 0 |
| 6 | skill taxonomy curation and maintenance | 0 |
| 7 | adaptive skill recommendation for dialogue systems | 0 |
| 8 | skill mining and recommendation in conversational AI | 0 |
| 9 | evolution of agent competencies in linguistics | 0 |
| 10 | skill selection and recommendation mechanisms for chatbots | 0 |
| 11 | dynamic skill management in language agents | 0 |
| 12 | skill evolution modeling for virtual assistants | 0 |
| 13 | governance of agent competencies in NLP | 0 |
| 14 | skill ontology development and lifecycle | 0 |
| 15 | automated skill evaluation and adaptation | 0 |
| 16 | competency recommendation pipelines for conversational agents | 0 |
| 17 | skill evolution and maintenance in AI-driven linguistics tools | 0 |
| 18 | lifecycle governance of dialog system skills | 0 |
| 19 | skill collection, ranking, and evolution in language agents | 0 |
| 20 | agent skill recommendation and continuous improvement. | 0 |

### Verified citations

1. **SkillsVote: Lifecycle Governance of Agent Skills from Collection, Recommendation to Evolution** (2026). Hongyi Liu, Haoyan Yang, Tao Jiang, Bo Tang, Feiyu Xiong, et al.. arXiv. [2605.18401](https://arxiv.org/abs/2605.18401). PDF-sampled: No.
2. **Agent Skills for Large Language Models: Architecture, Acquisition, Security, and the Path Forward** (2026). Renjun Xu, Yang Yan. arXiv. [2602.12430](https://arxiv.org/abs/2602.12430). PDF-sampled: No.
3. **Memento-Skills: Let Agents Design Agents** (2026). Huichi Zhou, Siyuan Guo, Anjie Liu, Zhongwei Yu, Ziqin Gong, et al.. arXiv. [2603.18743](https://arxiv.org/abs/2603.18743). PDF-sampled: No.
4. **Toward User Comprehension Supports for LLM Agent Skill Specifications** (2026). Zikai Alex Wen. arXiv. [2605.19362](https://arxiv.org/abs/2605.19362). PDF-sampled: No.
5. **Dynamic Skill Lifecycle Management for Agentic Reinforcement Learning** (2026). Junhao Shen, Teng Zhang, Xiaoyan Zhao, Hong Cheng. arXiv. [2605.10923](https://arxiv.org/abs/2605.10923). PDF-sampled: No.
6. **Skill-as-Pseudocode: Refactoring Skill Libraries to Pseudocode for LLM Agents** (2026). Xinze Li, Yuhang Zang, Yixin Cao, Aixin Sun. arXiv. [2605.27955](https://arxiv.org/abs/2605.27955). PDF-sampled: No.
