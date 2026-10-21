# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/download.py: self-declared fabricated metric — “…ported data – no synthetic or placeholder values are generated.  The script i…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/ri_dataset.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/data/download.py: self-declared fabricated metric — “…ported data – no synthetic or placeholder values are generated.  The script i…”; every produced artifact is gitignored (data/raw/ri_dataset.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 run-book script(s) missing (plan/impl path mismatch): python data/split.py --folds 5 --repeats 5 --ratios 0.8 0.1 0.1; python training/train.py --fold $i --repeat $j --epochs 200 --batch-size 32 --seed $((2000 + i*10 + j)); python training/evaluate.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt; 1 command(s) failed: python code/data/preprocess.py --filter-mw 500 (rc=1); 1 declared deliverable(s) absent: data/processed/filtered.csv

## Failing / missing run-book commands

- python code/data/preprocess.py --filter-mw 500 -> rc=1
n fetch_double
    self.fetch_flow_scalar(style='"')
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/yaml/scanner.py", line 666, in fetch_flow_scalar
    self.tokens.append(self.scan_flow_scalar(style))
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/yaml/scanner.py", line 1151, in scan_flow_scalar
    chunks.extend(self.scan_flow_scalar_spaces(double, start_mark))
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/yaml/scanner.py", line 1238, in scan_flow_scalar_spaces
    raise ScannerError("while scanning a quoted scalar", start_mark,
yaml.scanner.ScannerError: while scanning a quoted scalar
  in "/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/specs/001-predicting-molecular-refractive-indices/contracts/dataset.schema.yaml", line 41, column 18
found unexpected end of stream
  in "/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/specs/001-predicting-molecular-refractive-indices/contracts/dataset.schema.yaml", line 41, column 22402

- python data/split.py --folds 5 --repeats 5 --ratios 0.8 0.1 0.1 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/data/split.py': [Errno 2] No such file or directory

- python training/train.py --fold $i --repeat $j --epochs 200 --batch-size 32 --seed $((2000 + i*10 + j)) -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/training/train.py': [Errno 2] No such file or directory

- python training/evaluate.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/training/evaluate.py': [Errno 2] No such file or directory

- python models/attribution.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt --output results/attributions_${i}_${j}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/models/attribution.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/filtered.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
