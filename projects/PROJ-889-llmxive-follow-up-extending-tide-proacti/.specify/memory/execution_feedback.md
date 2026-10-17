# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/synthetic_meta.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/synthetic_meta.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 13 command(s) failed: python -m src.data.acquire_real   # downloads, verifies SHA‑256, maps to binary ground_truth_label (rc=1); python -m src.data.generate_synthetic   # creates .py files under data/synthetic/ (rc=1); python -m src.features.extract   # reads all .py files, estimates depth/scope, writes data/features.csv (includes sha256) (rc=1)

## Failing / missing run-book commands

- python -m src.data.acquire_real   # downloads, verifies SHA‑256, maps to binary ground_truth_label -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-tide-proacti/src/data/acquire_real.py", line 15, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.data.generate_synthetic   # creates .py files under data/synthetic/ -> rc=1
c_88_depth4.py\\na6fc0d7920e5b91e8b50667d229d1e5036d938bd208a634bd6e34091a8cd88ac  synthetic_89_depth5.py\\n5a49249a256e3a2207ea4945a154414416cfed29f8f919dfd63d3bfb5ce6b7b7  synthetic_8_depth4.py\\n0ae524d59d1d9216eb933022e0b45ab6e53ff2951f4a7cd8d980c820d4814a0b  synthetic_90_depth1.py\\n9ce52ee40f7aa4681eda6072db88f45c28ecf4ba8adfec2b20e462f0237ccb6e  synthetic_91_depth2.py\\nb8af253ea0127cd4d50553cb64ac528bcf6def51d0f018f3a092d9f016e86a8e  synthetic_92_depth3.py\\nfca54825494e76cdce5db76d5be0bf7f60850eec78fdddd1994141036e2db166  synthetic_93_depth4.py\\n6e753e501ab6c5da118f1df7b4f5b01fba99437c5e0e9b1ba5f97e319977f00e  synthetic_94_depth5.py\\n908098abeb51f0181eac68474797ec667dd47a3863b0b3f6fa85a52dcfbded3f  synthetic_95_depth1.py\\n5ca4420e64aaa78b023eeec7252f3bd5a52bce5942dd783b843c4b52b2d92c16  synthetic_96_depth2.py\\n6e84d48bca497f5fc61d463fb3d0144bfd95829e258b86160dbdb99823de7b97  synthetic_97_depth3.py\\n0493a3eb84de5107cdce15277c3f40cdfa0e09c38dbf3f4a66fbd45c2a8a352a  synthetic_98_depth4.py\\nd392b4b77f28994625aa691c9498099be21668b45cafa8f7b362a5332460a548  synthetic_99_depth5.py\\nd6f447c7bc5b80a065bf7d49eea358590f7997240fc3f2724911fdcbe5bafd0c  synthetic_9_depth5.py\\n'

- python -m src.features.extract   # reads all .py files, estimates depth/scope, writes data/features.csv (includes sha256) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.features.extract' (ModuleNotFoundError: No module named 'src.features')

- python -m src.pipelines.tide_lite   # outputs data/tide_lite_enriched.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.tide_lite' (ModuleNotFoundError: No module named 'src.pipelines')

- python -m src.pipelines.tide_original   # outputs data/tide_original_enriched.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.tide_original' (ModuleNotFoundError: No module named 'src.pipelines')

- python -m src.pipelines.consolidate   # creates data/merged_results.csv (SSoT) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.consolidate' (ModuleNotFoundError: No module named 'src.pipelines')

- python -m src.data.split_data          # writes train/validation index files (seed=42) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: No module named src.data.split_data

- python -m src.analysis.logistic        # logistic regression, EPV check, PDP threshold + bootstrap CI -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.logistic' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.mcnemar         # stratified McNemar tests + Holm‑Bonferroni -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.mcnemar' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.sensitivity     # probability‑cutoff sweep & variance reporting -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.sensitivity' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.efficiency      # total runtime & CPU utilisation check -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.efficiency' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.visualize   # writes PNGs under outputs/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.visualize' (ModuleNotFoundError: No module named 'src.analysis')

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


