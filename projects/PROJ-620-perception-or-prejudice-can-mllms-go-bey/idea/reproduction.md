# Reproduce & validate: Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Personality?

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/external/MM-OCEAN/   (clone of https://github.com/kkkcx/MM-OCEAN)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Personality?

**Abstract:** Multimodal Large Language Models (MLLMs) are increasingly deployed in human-facing roles where personality perception is critical, yet existing benchmarks evaluate this capability solely on numerical Big Five score prediction, leaving open whether models truly perceive personality through behavioral understanding or merely prejudge through superficial pattern matching. We address this gap with three contributions. (i) A new task: we formalize Grounded Personality Reasoning (GPR), which requires MLLMs to anchor each Big Five rating in observable evidence through a chain of rating, reasoning, and grounding. (ii) A new dataset: we release MM-OCEAN (1,104 videos, 5,320 MCQs), produced by a multi-agent pipeline with human verification, with timestamped behavioral observations, evidence-grounded trait analyses, and seven categories of cue-grounding MCQs. (iii) Benchmark and analysis: we design a three-tier evaluation (rating, reasoning, grounding) plus four sample-level failure-mode metrics: Prejudice Rate (PR), Confabulation Rate (CR), Integration-failure Rate (IR), and Holistic-grounding Rate (HR), and benchmark 27 MLLMs (13 closed, 14 open). The analysis uncovers a striking Prejudice Gap: across the field, 51% of correct ratings are not grounded in retrieved cues, and the Holistic-Grounding Rate spans only 0-33.5%. These findings expose a disconnect between getting the right score and reasoning for the right reason, charting a roadmap for grounded social cognition in MLLMs.

## Shipped code — file tree (`projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/external/MM-OCEAN/`)

```
LICENSE
README.md
croissant.json
data/test/--Ymqszjv54.000.mp4.json
data/test/-10-QQDO_ME.001.mp4.json
data/test/-4J4xkfN5cI.002.mp4.json
data/test/-6otZ7M-Mro.002.mp4.json
data/test/-6otZ7M-Mro.004.mp4.json
data/test/-8asrRvfJWA.002.mp4.json
data/test/-DOqN0d8KHw.004.mp4.json
data/test/-DOqN0d8KHw.005.mp4.json
data/test/-Gl98Jn45Fs.004.mp4.json
data/test/-N6QKrbnaDs.000.mp4.json
data/test/-N6QKrbnaDs.001.mp4.json
data/test/-N6QKrbnaDs.003.mp4.json
data/test/-NwfYYf5xLo.002.mp4.json
data/test/-PWjgx2czwY.001.mp4.json
data/test/-R2SZu3SYgM.001.mp4.json
data/test/-Wqk9eex6bQ.000.mp4.json
data/test/-ZP25UpJeJ4.000.mp4.json
data/test/-aU2FN5pkWA.000.mp4.json
data/test/-agCXYgb7pI.002.mp4.json
data/test/-awAu11kBZ0.001.mp4.json
data/test/-fqiCqZtgYs.005.mp4.json
data/test/-lSBwF052u0.005.mp4.json
data/test/-m5QCnnp-vI.000.mp4.json
data/test/-mt-IKgGhuY.002.mp4.json
data/test/-rxiLMvlZqM.002.mp4.json
data/test/04oq2yrBwMg.002.mp4.json
data/test/05l5bteT_qA.003.mp4.json
data/test/0G2o3fik36I.000.mp4.json
data/test/0G2o3fik36I.001.mp4.json
data/test/0MB91ku0eEw.000.mp4.json
data/test/0MB91ku0eEw.002.mp4.json
data/test/0MB91ku0eEw.004.mp4.json
data/test/0SS47KwVOQ4.001.mp4.json
data/test/0_xOGmydDN0.005.mp4.json
data/test/0iQIfGnKflc.003.mp4.json
data/test/0kg6pmbSN6A.003.mp4.json
data/test/0kg6pmbSN6A.004.mp4.json
data/test/0u56Q_QmxIM.000.mp4.json
data/test/0uCqd5hZcyI.003.mp4.json
data/test/1-GgVRmAEoo.001.mp4.json
data/test/12Ezy1y1cWY.000.mp4.json
data/test/13KtmgntgQw.004.mp4.json
data/test/13kjwEtSyXc.003.mp4.json
data/test/19cplBTXyoY.001.mp4.json
data/test/19pTUX8KfYM.001.mp4.json
data/test/19pTUX8KfYM.003.mp4.json
data/test/1Lv72Si4GnY.000.mp4.json
data/test/1Wh2mIFrGvk.000.mp4.json
data/test/1hpZ2ecWqtI.004.mp4.json
data/test/1mHjMNZZvFo.001.mp4.json
data/test/1mReUxIEuw0.004.mp4.json
data/test/1mdMhaq5p4w.003.mp4.json
data/test/1q-N_zbsAg0.002.mp4.json
data/test/1q-N_zbsAg0.005.mp4.json
data/test/1tPH6PNeOSk.005.mp4.json
data/test/1yIGI42lzak.000.mp4.json
data/test/2-LDYe7OXZU.002.mp4.json
data/test/26CMYJn3u6Y.000.mp4.json
data/test/26CMYJn3u6Y.001.mp4.json
data/test/29UCGJldICw.000.mp4.json
data/test/2AV8m02PjdU.001.mp4.json
data/test/2AV8m02PjdU.004.mp4.json
data/test/2AYq7CdNXNo.005.mp4.json
data/test/2Fgn78rYjPM.004.mp4.json
data/test/2GHz8LYflE0.001.mp4.json
data/test/2GHz8LYflE0.003.mp4.json
data/test/2HE6cw3HFPk.000.mp4.json
data/test/2NNYN1ZCJhw.001.mp4.json
data/test/2SzC9dm4Yy4.004.mp4.json
data/test/2SzC9dm4Yy4.005.mp4.json
data/test/2TXrDZgbDHE.000.mp4.json
data/test/2TXrDZgbDHE.004.mp4.json
data/test/2TbU3Eg2i4A.002.mp4.json
data/test/2UxhlaDEPmI.001.mp4.json
data/test/2Z8Xi_DTlpI.000.mp4.json
data/test/2Z8Xi_DTlpI.005.mp4.json
data/test/2bAsXLQjlt8.000.mp4.json
data/test/2bAsXLQjlt8.003.mp4.json
data/test/2d6btbaNdfo.000.mp4.json
data/test/2f7rLXwzP3s.005.mp4.json
data/test/2fzLibPAtvI.003.mp4.json
data/test/2hhqEWiv4eI.005.mp4.json
data/test/2mfmw63l88g.000.mp4.json
data/test/2oEUp9sGRGk.002.mp4.json
data/test/2q8orkMs2Jg.004.mp4.json
data/test/300gK3CnzW0.001.mp4.json
data/test/300gK3CnzW0.003.mp4.json
data/test/36sZ__mv_KY.000.mp4.json
data/test/383HhOtOBwg.005.mp4.json
data/test/3CyIOM2izmI.000.mp4.json
data/test/3DURnr95fMg.001.mp4.json
data/test/3DURnr95fMg.003.mp4.json
data/test/3DURnr95fMg.005.mp4.json
data/test/3LAaFUSGvsU.005.mp4.json
data/test/3P_D_bd-_NM.004.mp4.json
data/test/3S72dDIm1fM.002.mp4.json
data/test/3S72dDIm1fM.004.mp4.json
data/test/3S72dDIm1fM.005.mp4.json
data/test/3VyriB3isO8.005.mp4.json
data/test/3WmWJ1lNy-U.002.mp4.json
data/test/3WoXkI06zGk.000.mp4.json
data/test/3b9fhd-EDaY.002.mp4.json
data/test/3df_Uk9EmwU.002.mp4.json
data/test/3g6Ab-BIbR4.004.mp4.json
data/test/3gmc2kLV4Bo.003.mp4.json
data/test/3hKgh9AB3tk.003.mp4.json
data/test/3wRj39GKLJ0.002.mp4.json
data/test/3wRj39GKLJ0.003.mp4.json
data/test/3wgZrRMosvY.001.mp4.json
data/test/3wgZrRMosvY.004.mp4.json
data/test/3zAyM2edy1g.002.mp4.json
data/test/3zAyM2edy1g.005.mp4.json
data/test/40rn4A64Bdk.004.mp4.json
data/test/41NNb7cucVo.004.mp4.json
data/test/48S9_KZvzVw.002.mp4.json
data/test/4CSV8L7aVik.003.mp4.json
data/test/4CSV8L7aVik.004.mp4.json
data/test/4FS7wEOOBNk.004.mp4.json
data/test/4JjpfL4y3XM.004.mp4.json
data/test/4OKYywIqnqg.000.mp4.json
data/test/4Qr1BjZhnpg.001.mp4.json
data/test/4RKQGZzPClk.000.mp4.json
data/test/4a6-tNo-NDM.001.mp4.json
data/test/4fN-DKUzgWQ.004.mp4.json
data/test/4kIHxR6s1L4.003.mp4.json
data/test/4kYaYIcuLpM.000.mp4.json
data/test/4lIbWq27O84.003.mp4.json
data/test/4vJ69g7gAH4.002.mp4.json
data/test/4vdJGgZpj4k.000.mp4.json
data/test/4vdJGgZpj4k.003.mp4.json
data/test/4yogPbHFQ9o.001.mp4.json
data/test/50gokPvvMs8.004.mp4.json
data/test/50gokPvvMs8.005.mp4.json
data/test/51KRxB3g7A8.002.mp4.json
data/test/51z2rCqPqPE.004.mp4.json
data/test/53QFyec0uN0.000.mp4.json
data/test/53QFyec0uN0.001.mp4.json
data/test/53gtUkC7IZM.000.mp4.json
data/test/53gtUkC7IZM.002.mp4.json
data/test/54JawR1x0II.000.mp4.json
data/test/54JawR1x0II.004.mp4.json
data/test/5BPGRteF64Y.004.mp4.json
data/test/5CRqN54uejE.001.mp4.json
data/test/5Eez38v8TuU.004.mp4.json
data/test/5IqtX-uq28E.004.mp4.json
data/test/5Ku4_r_Yxsk.003.mp4.json
data/test/5T2PhH-OMds.002.mp4.json
data/test/5VG1EgzvprE.004.mp4.json
data/test/5Wmlo8Z5yVA.000.mp4.json
data/test/5bYq8LXMRaw.004.mp4.json
data/test/5bi_PM3XMEQ.001.mp4.json
data/test/5ghk5950BhU.003.mp4.json
data/test/5kwoq4EZixQ.000.mp4.json
data/test/5xA5iKk4v6w.000.mp4.json
data/test/5xA8-Y5qgT0.002.mp4.json
data/test/5xA8-Y5qgT0.005.mp4.json
data/test/6-_1-vBNl_0.000.mp4.json
data/test/69BopbFc34U.002.mp4.json
data/test/69EsTnCVCp0.002.mp4.json
data/test/69EsTnCVCp0.004.mp4.json
data/test/69EsTnCVCp0.005.mp4.json
data/test/6EMgu2djYrU.000.mp4.json
data/test/6M8OQNo64Tc.001.mp4.json
data/test/6N02tjYPLh8.003.mp4.json
data/test/6N02tjYPLh8.004.mp4.json
data/test/6NjuNY4LfQc.000.mp4.json
data/test/6NjuNY4LfQc.003.mp4.json
data/test/6NjuNY4LfQc.005.mp4.json
data/test/6RwVJK3husE.002.mp4.json
data/test/6SoFnys6mf0.000.mp4.json
data/test/6V807Mf_gHM.003.mp4.json
data/test/6V807Mf_gHM.004.mp4.json
data/test/6WSr4IW6cNI.002.mp4.json
data/test/6WSr4IW6cNI.004.mp4.json
data/test/6l0RBbxg4fk.000.mp4.json
data/test/6oL9yyc9iJc.004.mp4.json
data/test/6wIEiqmuHOM.002.mp4.json
data/test/6waL_gUxtAM.005.mp4.json
data/test/6zm71IHOCZA.003.mp4.json
data/test/6zm71IHOCZA.005.mp4.json
data/test/7-7qX0heWkg.002.mp4.json
data/test/78zauTEQ-k8.002.mp4.json
data/test/7BgScfRre5M.000.mp4.json
data/test/7FXs86Z98E0.003.mp4.json
data/test/7GRC7XjGzX8.002.mp4.json
data/test/7Kn5VT9bB4I.000.mp4.json
data/test/7PYAn9njCHI.005.mp4.json
data/test/7QpoDA8t6yQ.004.mp4.json
data/test/7WixH0aSfqI.003.mp4.json
data/test/7Y3S4nfQHeo.000.mp4.json
data/test/7Y4cUPFEt-4.003.mp4.json
data/test/7ZnijRlK5-E.000.mp4.json
data/test/7ZnijRlK5-E.004.mp4.json
data/test/7ZnijRlK5-E.005.mp4.json
data/test/7b9DirXrkHo.005.mp4.json
data/test/7knYNR1tAig.001.mp4.json
data/test/7knYNR1tAig.003.mp4.json
… (truncated)
```

## Detected entry points

- `projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/external/MM-OCEAN/evaluate.py`
- `projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/external/MM-OCEAN/prompts/aligner.py`
- `projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/external/MM-OCEAN/prompts/examiner.py`
- `projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/external/MM-OCEAN/prompts/judge.py`
- `projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/external/MM-OCEAN/prompts/observer.py`
- `projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/external/MM-OCEAN/prompts/psychologist.py`
- `projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/external/MM-OCEAN/prompts/unified.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `MM-OCEAN` — not re-implementing it.
