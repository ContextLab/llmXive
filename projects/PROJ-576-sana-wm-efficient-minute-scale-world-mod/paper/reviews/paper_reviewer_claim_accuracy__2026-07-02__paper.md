---
action_items:
- id: 81dec801d0fe
  severity: writing
  text: The claim that the distilled variant generates a 60s 720p clip in 34s on a
    single RTX 5090 (Abstract, Sec 1) relies on hardware (RTX 5090) that is not yet
    publicly released or benchmarked. This specific performance metric is currently
    unverifiable and should be qualified as 'projected' or replaced with data from
    an available GPU (e.g., RTX 4090) to ensure factual accuracy.
- id: c9dd92ab1f2d
  severity: writing
  text: "The claim of '36x higher throughput' compared to baselines (Abstract, Sec\
    \ 1) lacks a clearly defined baseline in the text. While Table 1 shows SANA-WM\
    \ at 24.1 videos/hour, the text does not explicitly state which baseline model\
    \ and configuration (e.g., LingBot-World at 0.6 videos/hour) yields exactly 36x.\
    \ The calculation 24.1/0.6 \u2248 40x suggests the '36x' figure may be rounded\
    \ or derived from a different metric not explicitly shown, requiring clarification\
    \ to support the specific multiplier."
- id: 9119bb48dd07
  severity: writing
  text: The abstract states the model uses '~213K public video clips', but Table 1
    (tables/train-data.tex) lists a total of 212,975 clips. While the difference is
    negligible, the text should either use the exact number or explicitly state the
    rounding convention to maintain precision in factual claims.
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:44:30.262324Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several strong factual claims regarding performance metrics and hardware specifications that require verification or clarification to ensure strict accuracy.

First, the Abstract and Introduction claim that a distilled variant can deploy on a "single RTX 5090" to generate a 60s clip in 34s. As of the current date, the NVIDIA RTX 5090 is not a publicly available or benchmarked product. Citing specific performance metrics on unreleased hardware renders this claim factually unverifiable and potentially misleading. The authors should either provide projected estimates clearly labeled as such, or rephrase the claim to reference available hardware (e.g., RTX 4090) with corresponding data.

Second, the claim of "$36\times$ higher throughput" in the Abstract and Introduction is not immediately supported by the visible data in Table 1. The table lists SANA-WM (refined) at 22.0 videos/hour and LingBot-World at 0.6 videos/hour. The ratio $22.0 / 0.6 \approx 36.6$, which rounds to 37x, or if comparing the non-refined SANA-WM (24.1) to LingBot (0.6), the ratio is $\approx 40x$. The specific "36x" figure appears to be a precise calculation that does not align perfectly with the rounded numbers in the main table, or it refers to a specific baseline configuration not explicitly highlighted in the text. The authors should clarify the exact baseline and calculation used to support this specific multiplier.

Finally, the abstract cites "~213K" clips, while Table 1 (tables/train-data.tex) provides an exact count of 212,975. While this is a minor discrepancy, scientific writing should maintain consistency between rounded claims and exact data tables. Using the exact number or explicitly stating the rounding method would improve precision.

The core scientific claims regarding the architecture (Hybrid Linear Attention, Dual-Branch Camera Control) and the general trend of improved efficiency and accuracy appear supported by the provided tables and ablation studies, but the specific hardware and throughput numbers need the adjustments noted above to be factually rigorous.
