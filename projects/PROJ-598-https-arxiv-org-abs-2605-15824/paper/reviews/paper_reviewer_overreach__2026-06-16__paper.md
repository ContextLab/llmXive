---
action_items:
- id: 7dc99bd95052
  severity: science
  text: "Provide explicit baseline inference\u2011time or FPS numbers for each competing\
    \ method to substantiate the claim of \u201C30\u2013180\xD7 faster than baselines\u201D\
    \ (Abstract, line\u202F1). Without these numbers the speed\u2011up statement is\
    \ not verifiable."
- id: 9e65e3fce69a
  severity: writing
  text: "Re\u2011phrase the \u201Ctraining\u2011free KV Cache Rescheduling\u201D description\
    \ (Section\u202F4.3) to clarify that only the cache\u2011rescheduling component\
    \ is training\u2011free, while the overall pipeline still requires teacher pre\u2011\
    training and streaming distillation."
- id: 97a96d629428
  severity: science
  text: "In Table\u202F1 (Main Results) include the FPS values of the baseline methods,\
    \ or at least a footnote specifying their speeds, so readers can confirm the reported\
    \ 23.8\u202FFPS advantage and the claimed 30\u2013180\xD7 speedup."
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T03:06:28.585364Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript makes several quantitative claims that extend beyond the evidence presented.  

1. **Speed‑up claim** – In the abstract the authors state that FashionChameleon is “30–180× faster than baselines.” The only speed figure reported for the proposed method is 23.8 FPS (Abstract line 1, Table 1). No baseline FPS or inference‑time numbers are shown anywhere in the paper, nor is there a discussion of hardware parity (e.g., whether baselines were also run on an H200 GPU). Without these data the multiplicative speed‑up claim cannot be verified and appears over‑stated.

2. **Overall superiority claim** – The same abstract sentence claims “outperforming baselines on ID consistency, motion quality, and garment consistency.” Table 1 highlights the best values for many metrics, but it does not display the corresponding baseline scores for all listed metrics (e.g., Cur., GME, Amp., Smoo., VQ, HGC, LGC, NTP). Consequently, readers cannot assess whether the proposed method truly dominates across the board. The paper should either present the full baseline numbers or temper the claim to reflect the metrics where it is demonstrably superior.

3. **Training‑free terminology** – Section 4.3 introduces “Training‑Free KV Cache Rescheduling” and the conclusion repeatedly emphasizes a “training‑free” approach. However, the methodology clearly involves a teacher model trained on reference–garment pairs (Section 4.1) and a streaming distillation stage (Section 4.2). Only the cache‑rescheduling component is training‑free. The current wording may mislead readers to think the entire pipeline requires no training, which is not the case.

4. **Generality of “real‑time interactive”** – The paper reports 23.8 FPS at 720p on a single H200 GPU, which satisfies a real‑time threshold for many applications. Nonetheless, the claim of “interactive” usage would be stronger if the authors reported latency of garment‑switch operations (e.g., time between a new garment input and visible change in the output) and demonstrated this in a user study. The existing user‑study (Section User Study) only reports preference scores, not interaction latency.

Overall, the manuscript’s core contributions are promising, but the quantitative claims about speedup, universal superiority, and training‑free nature need tighter grounding in the presented data. Addressing the points above will eliminate over‑reach and improve the paper’s scientific credibility.
