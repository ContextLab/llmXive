---
action_items:
- id: c4eb1743f46a
  severity: writing
  text: "The abstract (Section\u202F1) claims \u201C30\u2013180\xD7 faster than baselines\u201D\
    \ but the manuscript never provides baseline FPS numbers to substantiate this\
    \ range. Add a table or explicit numbers for each baseline\u2019s inference speed\
    \ to support the speed\u2011up claim."
- id: 22ec6abd63f2
  severity: science
  text: "The statement in the introduction (Section\u202F2) that diffusion\u2011based\
    \ text\u2011to\u2011video models \u201Clack fine\u2011grained, low\u2011latency\
    \ garment control\u201D is not directly supported by the cited works\u202F\\cite{ho2020denoising,lipman2022flow,yang2024cogvideox,wan2025wan}.\
    \ Those papers discuss general video diffusion and do not evaluate garment\u2011\
    level control. Either replace the citation with works that explicitly study garment\
    \ control or qualify the claim."
- id: 649e7bcd1a0f
  severity: science
  text: "In the related\u2011works paragraph on Subject\u2011to\u2011Video customization,\
    \ the paper asserts that existing methods \u201Csuffer high latency\u201D and\
    \ that FashionChameleon \u201Cachieves real\u2011time interactivity\u201D. No\
    \ latency figures are provided for the cited baselines\u202F\\cite{wang2026customvideo,chen2024disenstudio,he2024id,yuan2025identity,liu2025phantom,vace,xue2025stand}.\
    \ Provide latency measurements (FPS or ms/frame) for these baselines to substantiate\
    \ the claim."
- id: 5c4b1dcfd73f
  severity: science
  text: "The claim that the proposed Gradient\u2011Reweighted DMD \u201Cimproves long\u2011\
    video (165\u2011frame) metrics\u201D relies on Table\u202F5, which compares only\
    \ two variants (Naive DMD vs. GR\u2011DMD). However, statistical significance\
    \ is not reported. Include variance/error bars or statistical tests to confirm\
    \ that the improvements are not due to random variation."
- id: d0ab59acbb3d
  severity: writing
  text: "The conclusion states that the method \u201Coutperforms baselines on ID consistency,\
    \ motion quality, and garment consistency\u201D. While Table\u202F1 shows the\
    \ best values for many metrics, the baselines\u2019 numbers are omitted (shown\
    \ as \u201C\u2026 rows omitted\u2026\u201D). Provide the full baseline results\
    \ so readers can verify the superiority claim."
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T02:53:48.980998Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript makes several quantitative claims that are insufficiently supported by the presented evidence or by the cited literature.

1. **Speed‑up claim (Abstract, line 1)** – The paper reports “23.8 FPS on a single GPU (30–180× faster than baselines)”. Table 1 lists only the FPS of FashionChameleon; the FPS of competing methods is absent, making the multiplicative speed‑up factor unverified. Without baseline runtimes, readers cannot assess whether the claimed 30–180× improvement holds.

2. **Lack of garment control in prior diffusion models (Introduction, lines 10‑12)** – The citations `\cite{ho2020denoising,lipman2022flow,yang2024cogvideox,wan2025wan}` describe diffusion‑based video generation but do not explicitly evaluate garment‑level manipulation. The claim therefore overstates the relevance of those works. A more appropriate citation would be a paper that directly examines fine‑grained clothing editing, or the claim should be softened.

3. **High latency of Subject‑to‑Video baselines (Related Works, lines 30‑33)** – The statement that earlier S2V methods “suffer high latency” lacks quantitative backing. The cited papers (`\cite{wang2026customvideo,chen2024disenstudio,he2024id,yuan2025identity,liu2025phantom,vace,xue2025stand}`) report runtime metrics, but these numbers are not reproduced in the manuscript. Including their FPS or per‑frame inference time would allow a fair comparison.

4. **Ablation significance (Ablation Studies, Table 5)** – The improvement of Gradient‑Reweighted DMD over naive DMD is shown as a modest increase in several metrics (e.g., Cur 0.4232 → 0.4265). No confidence intervals or statistical tests are reported, leaving it unclear whether the differences are statistically meaningful. Adding variance estimates or performing paired significance testing would strengthen the claim.

5. **Overall superiority claim (Conclusion, line 5)** – The conclusion claims superiority across ID consistency, motion quality, and garment consistency, yet Table 1 omits the baseline rows (“... 8 rows omitted ...”). Readers cannot verify that FashionChameleon truly dominates all baselines on these dimensions. Providing the complete set of baseline numbers (or a separate supplemental table) is necessary for transparency.

Overall, the paper’s experimental results are promising, but several central quantitative assertions are currently under‑supported. Addressing the points above will make the claims verifiable and improve the manuscript’s scientific rigor.
