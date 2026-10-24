# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/power_analysis.py: self-declared fabricated metric — “…les, 3))      # Construct the simulated scores matrix:     #   mean + sqrt(…”
- code/statistical_analysis.py: self-declared fabricated metric — “…rics CSV is empty – producing placeholder results.")     # Metrics we care abo…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/commit_pairs.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/power_analysis.py: self-declared fabricated metric — “…les, 3))      # Construct the simulated scores matrix:     #   mean + sqrt(…”; code/statistical_analysis.py: self-declared fabricated metric — “…rics CSV is empty – producing placeholder results.")     # Metrics we care abo…”; every produced artifact is gitignored (data/raw/commit_pairs.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 command(s) failed: python -m pytest tests/contract/ (rc=1); python -m pytest tests/unit/ (rc=1); 1 declared deliverable(s) absent: data/generated/generation_success_rates.csv

## Failing / missing run-book commands

- python -m pytest tests/contract/ -> rc=1
sts/contract/test_intent_schema.py F                                   [ 28%]
tests/contract/test_schemas.py ....                                      [ 85%]
tests/contract/test_statistical_analysis_schema.py .                     [100%]

=================================== FAILURES ===================================
___________________________ test_intent_json_schema ____________________________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-4/test_intent_json_schema0')

    def test_intent_json_schema(tmp_path):
        # Locate a sample intent JSON file (generated by the pipeline).
        intent_dir = paths.data("intermediate", "intent_entities")
        json_files = list(intent_dir.glob("*.json"))
>       assert json_files, "No intent JSON files found – run the extraction first."
E       AssertionError: No intent JSON files found – run the extraction first.
E       assert []

tests/contract/test_intent_schema.py:27: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_intent_schema.py::test_intent_json_schema - Assert...
========================= 1 failed, 6 passed in 0.18s ==========================


- python -m pytest tests/unit/ -> rc=1
 Request: HEAD https://huggingface.co/facebook/bart-large-mnli/resolve/d7645e127eaf1aefc7862fd59a17a5aa8558b8ce/special_tokens_map.json "HTTP/1.1 404 Not Found"
INFO     httpx2:_client.py:1084 HTTP Request: HEAD https://huggingface.co/facebook/bart-large-mnli/resolve/d7645e127eaf1aefc7862fd59a17a5aa8558b8ce/chat_template.jinja "HTTP/1.1 404 Not Found"
INFO     httpx2:_client.py:1084 HTTP Request: HEAD https://huggingface.co/facebook/bart-large-mnli/resolve/d7645e127eaf1aefc7862fd59a17a5aa8558b8ce/processor_config.json "HTTP/1.1 404 Not Found"
INFO     httpx2:_client.py:1084 HTTP Request: HEAD https://huggingface.co/facebook/bart-large-mnli/resolve/d7645e127eaf1aefc7862fd59a17a5aa8558b8ce/video_preprocessor_config.json "HTTP/1.1 404 Not Found"
INFO     httpx2:_client.py:1084 HTTP Request: HEAD https://huggingface.co/facebook/bart-large-mnli/resolve/d7645e127eaf1aefc7862fd59a17a5aa8558b8ce/preprocessor_config.json "HTTP/1.1 404 Not Found"
=========================== short test summary info ============================
ERROR tests/unit/test_entity_extraction_intent.py::test_precision_recall_against_gold
============================== 1 error in 15.84s ===============================



## Declared deliverables still missing

- data/generated/generation_success_rates.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/generated/generation_success_rates.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/generated/generation_success_rates.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
