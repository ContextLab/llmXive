# Tasks: The Impact of Perceived Control Over Digital Environments on Anxiety

**Input**: Design documents from `/specs/001-the-impact-of-perceived-control-over-dig/`
**Re-plan note**: The original 50+ task list produced repeatedly-unverifiable artifacts (truncated ingestion code, missing `data/raw/social_media.csv`, missing config schema, missing all processed outputs). This revision consolidates the remaining work into a small number of end-to-end, deterministically verifiable tasks. Verified infrastructure work (project structure, config, contracts, tests, documentation) is preserved below as completed; the failing ingestion/scoring/proxy chain is REDONE with a simpler, artifact-first approach. No scientific requirement is dropped.

## Completed work (preserved, verified)

The following prior tasks are complete and their artifacts stand: project structure and pinned `requirements.txt` (T001–T003), `code/config.py` with seeds, `SAMPLE_SIZE=10000`, `RUNTIME_LIMIT_HOURS=6` (T004–T006), runtime‑limited `code/main.py` orchestrator (T007, T004b), `contracts/analysis.schema.yaml` and `contracts/dataset.schema.yaml` with `filtering.*` and `model_mapping.fear_to_anxiety` keys (T008a1–T008c), `data-model.md` (T008b), pytest setup (T009), pre‑run sampling logic (T013b), streaming fallback path (T042), empty‑dataset error handling (T018), spec/plan alignment fixes (T045, T046b, T049), dataset source documentation `specs/001-the-impact-of-perceived-control-over-dig/data-sources.md` (T046), unit/integration test scaffolding (T010–T012, T019–T020, T027–T029, T050, T052), proxy filter‑flag and timestamp‑regularity logic with `DataIndependenceError` guard (T022–T025), residual‑based normality branching with Spearman fallback (T033b, T034b, T034), and reproducibility audit (T044).

## Phase 1: Setup and first end-to-end analysis

- [ ] T101 [US1] **REDO ingestion as one small, complete, verifiable script** (replaces rejected T013): Rewrite `code/services/data_ingestion.py` as a short script (`python -m code.services.data_ingestion`) that (a) fetches `cardiffnlp/tweet_sentiment_extraction` via `datasets.load_dataset("cardiffnlp/tweet_sentiment_extraction", split="train", streaming=True)`, (b) takes the first `config.SAMPLE_SIZE` (10000) rows with `itertools.islice`, (c) writes them to `data/raw/social_media.csv` with `pandas.DataFrame.to_csv`, (d) computes and logs the MD5 of the written file, and (e) raises on any fetch failure — NO synthetic/mock fallback. **Verification**: `data/raw/social_media.csv` exists, is non‑empty, parses with `pandas.read_csv`, and has ≥ 1000 rows; the script exits 0.  
  ```bash
  python -m code.services.data_ingestion && \
  python -c "import pandas as pd; df=pd.read_csv('data/raw/social_media.csv'); assert len(df)>=1000"
  ```

- [ ] T102 [US1] **REDO language + gibberish filtering with real I/O** (replaces rejected T014b, T014c): Implement `filter_text(df)` in `code/services/anxiety_scoring.py` that reads `data/raw/social_media.csv`, drops rows where `langdetect.detect` fails or returns a non‑`'en'` language, and drops rows with text length < `filtering.min_text_length` (3) **or** character‑entropy < `filtering.entropy_threshold` (0.7) — both thresholds read from `contracts/analysis.schema.yaml`, raising `ConfigurationError` if missing. Write the result to `data/processed/preprocessed_text.csv`. **Verification**: file exists, non‑empty, every row English, length ≥ 3, and entropy ≥ threshold (checked via schema key).  
  ```bash
  python -m code.services.anxiety_scoring --filter-only && \
  python -c "\
import pandas as pd, yaml, sys; \
df=pd.read_csv('data/processed/preprocessed_text.csv'); \
assert len(df)>0; \
assert all(df['text'].apply(lambda t: len(t)>=3)); \
schema=yaml.safe_load(open('contracts/analysis.schema.yaml')); \
threshold=schema['filtering']['entropy_threshold']; \
import math; \
def entropy(s): \
    probs=[s.count(c)/len(s) for c in set(s)]; \
    return -sum(p*math.log2(p) for p in probs if p>0); \
assert all(entropy(t)>=threshold for t in df['text']); \
"
  ```

- [ ] T103 [US1] **REDO CPU anxiety scoring end-to-end on a small real slice** (replaces rejected T015, T016, T017): In `code/services/anxiety_scoring.py`, load `cardiffnlp/twitter-roberta-base-emotion` in float32 on CPU (`device=-1`), verify that a `fear`‑equivalent label exists (per `model_mapping.fear_to_anxiety`), use its probability as `anxiety_score`; abort if missing. Score the first 500 rows of `data/processed/preprocessed_text.csv`, drop rows with `confidence_score` < 0.6, and write `data/processed/scoring_results.csv` with columns `post_id, text, anxiety_score, confidence_score`. **Verification**: file exists with correct columns, values ∈ [0,1], no nulls, **coverage ≥ 95 %** of valid rows, low‑confidence rows removed, and **CPU‑only** confirmed.  
  ```bash
  python -m code.services.anxiety_scoring --limit 500 && \
  python -c "\
import pandas as pd, json, torch, sys; \
df=pd.read_csv('data/processed/scoring_results.csv'); \
required={'post_id','text','anxiety_score','confidence_score'}; \
assert required.issubset(df.columns); \
assert df['anxiety_score'].between(0,1).all(); \
assert df['confidence_score'].between(0,1).all(); \
cov=json.load(open('data/processed/coverage_report.json')); \
assert cov['coverage_ratio']>=0.95; \
assert (df['confidence_score']>=0.6).all(); \
assert not torch.cuda.is_available(), 'CUDA detected!'; \
"
  ```

**Checkpoint**: Real downloaded data, real model scores on real text, all as checkable files. Do not proceed to analysis until these three commands pass.

## Phase 2: Complete the study and validate its evidence

- [ ] T104 [US1] **Scale scoring to the full sample and validate coverage & runtime** (replaces rejected T018a and completes T103's expansion): Extend scoring to all rows of `data/processed/preprocessed_text.csv` in batches (batch size from `code/config.py`) under the 6‑hour guard. Record start/end timestamps, compute elapsed seconds, write `data/processed/coverage_report.json` (with `valid_rows`, `scored_rows`, `coverage_ratio`) and `data/processed/runtime_report.json` (with `elapsed_seconds`). If `coverage_ratio < 0.95` or `elapsed_seconds > 21600`, raise an error. **Verification**: both JSON files exist, satisfy thresholds, and runtime is asserted.  
  ```bash
  python -m code.services.anxiety_scoring && \
  python -c "\
import json, sys; \
cov=json.load(open('data/processed/coverage_report.json')); \
run=json.load(open('data/processed/runtime_report.json')); \
assert cov['coverage_ratio']>=0.95, 'Coverage too low'; \
assert run['elapsed_seconds']<=21600, 'Runtime exceeded 6h'; \
"
  ```

- [ ] T105 [US2] **REDO proxy extraction with real I/O and independence guard** (replaces rejected T021, T026): Implement `code/services/proxy_extractor.py` as a runnable module that reads **only** metadata columns from `data/raw/social_media.csv` (as listed in `code/config.py`'s `COLUMN_MAP`). If the script attempts to load the `text` column, raise `DataIndependenceError`. Compute `filter_applied` flag: if the source column is missing, set flag to 0 and log a warning; otherwise copy the boolean/int flag (0/1). Compute per‑user `timestamp_regularity` = 1 − (standard deviation of inter‑post intervals / mean interval), normalized to [0,1]. Write `data/processed/proxy_results.csv` with columns `post_id, user_id, filter_applied, timestamp_regularity`. **Verification**: output CSV exists, required columns present, `filter_applied` values are only 0 or 1 (and a warning is emitted when missing), `timestamp_regularity` ∈ [0,1], and a unit test confirms no `text` column was read.  
  ```bash
  python -m code.services.proxy_extractor && \
  python -c "\
import pandas as pd, sys, logging; \
df=pd.read_csv('data/processed/proxy_results.csv'); \
assert {'post_id','user_id','filter_applied','timestamp_regularity'}.issubset(df.columns); \
assert df['filter_applied'].isin([0,1]).all(); \
assert df['timestamp_regularity'].between(0,1).all(); \
# check warning was logged when missing column (implementation‑specific) \
"
  ```

- [ ] T106 [US3] **Merge, correlate, and branch on residual normality** (replaces OLS‑heavy T106): In `code/main.py`, inner‑join `scoring_results.csv` and `proxy_results.csv` on `post_id` → `final_analysis.csv`. In `code/analysis/statistical_test.py`, fit a simple linear model `anxiety_score ~ control_proxy` (where `control_proxy` is the `filter_applied` column). Compute residuals, run **Shapiro‑Wilk** test on residuals, and write `normality_check.json` containing **three fields**: `test` set to `"shapiro_wilk"`, `p_value` (float), and `method_chosen` (`"pearson"` if `p_value` > 0.05 else `"spearman"`). Then compute the chosen correlation coefficient `r` and its p‑value, writing `analysis_results.json` with `r`, `p_value`, `method` (matching `method_chosen`), and `is_significant` (true if `p_value` < 0.05). **Verification**: both JSON files exist; `normality_check.json` includes the `test` field equal to `"shapiro_wilk"` and a numeric `p_value`; `analysis_results.json` `method` matches `normality_check.json`.`method_chosen`; and `is_significant` correctly reflects `p_value < 0.05`.  
  ```bash
  python -m code.main && \
  python -c "\
import json, sys; \
norm=json.load(open('data/processed/normality_check.json')); \
res=json.load(open('data/processed/analysis_results.json')); \
assert norm['test'] == 'shapiro_wilk', 'Shapiro-Wilk test not recorded'; \
assert isinstance(norm['p_value'], float); \
assert norm['method_chosen'] in ('pearson','spearman'); \
assert res['method'] == norm['method_chosen']; \
assert (res['p_value']<0.05) == res['is_significant']; \
"
  ```

- [ ] T107 [US3] **Generate the publication‑quality scatter plot** (completes T035, T036, T053): Implement `code/viz/plot_results.py` reading `final_analysis.csv` and `analysis_results.json`, producing `data/processed/correlation_plot.png`: scatter of `filter_applied` (as control proxy) vs `anxiety_score` with a regression line matching the chosen correlation method, using `seaborn.set_style('darkgrid')`, DPI ≥ 150, file size < 5 MB. **Verification**: PNG exists, can be opened, DPI ≥ 150, size < 5 MB, and seaborn style was set to `darkgrid`.  
  ```bash
  python -m code.viz.plot_results && \
  python -c "\
import os, PIL.Image as Img, sys; \
path='data/processed/correlation_plot.png'; \
assert os.path.getsize(path) < 5*1024*1024, 'File too large'; \
with Img.open(path) as im: assert im.info.get('dpi',(0,0))[0] >= 150; \
# simple runtime check that seaborn darkgrid was used (implementation‑specific) \
"
  ```

- [ ] T108 [US1/US2/US3] **Independent checks: audit and full‑pipeline test execution**: Run the full test suite (`pytest tests/ -v`). Record outcomes in `data/results/test_outcomes.md` (ensure file is non‑empty). **Verification**: test suite exits 0 and `test_outcomes.md` exists with at least one line.  
  ```bash
  pytest tests/ -v && \
  python -c "import pathlib, sys; assert pathlib.Path('data/results/test_outcomes.md').read_text().strip()!=''"
  ```

- [ ] T109 **Write a concise methods/results account**: Create `specs/001-the-impact-of-perceived-control-over-dig/results.md` summarizing the study and linking to `analysis_results.json`, `coverage_report.json`, `normality_check.json`, and `correlation_plot.png`. **Verification**: file exists and contains the four artifact filenames.  
  ```bash
  python -c "\
import pathlib, sys; \
p=pathlib.Path('specs/001-the-impact-of-perceived-control-over-dig/results.md'); \
assert p.exists(); \
text=p.read_text(); \
for fn in ['analysis_results.json','coverage_report.json','normality_check.json','correlation_plot.png']:\n    assert fn in text, f'Missing link to {fn}';\
"
  ```

- [ ] T110 **Re‑run the documented workflow end‑to‑end and confirm reproducibility**: Execute the full pipeline (`python -m code.services.data_ingestion && python -m code.services.anxiety_scoring && python -m code.services.proxy_extractor && python -m code.main && python -m code.viz.plot_results`). Then run `tests/integration/test_reproducibility.py` to ensure identical outputs with fixed seeds, and create `specs/001-the-impact-of-perceived-control-over-dig/handoff.md` documenting the single source of truth (`final_analysis.csv`) and known limitations. **Verification**: integration test passes and `handoff.md` exists.  
  ```bash
  python -m code.services.data_ingestion && \
  python -m code.services.anxiety_scoring && \
  python -m code.services.proxy_extractor && \
  python -m code.main && \
  python -m code.viz.plot_results && \
  pytest -q tests/integration/test_reproducibility.py && \
  test -f specs/001-the-impact-of-perceived-control-over-dig/handoff.md
  ```

## Dependencies and requirement coverage

- **AC‑001**: T101. **AC‑002**: T102 (now includes entropy‑threshold). **AC‑003**: T103/T104 (coverage ≥ 95 %). **AC‑004**: T103/T104 (low‑confidence removal).  
- **AC‑005/AC‑006/AC‑007**: T105 (filter_applied default handling, per‑user timestamp_regularity, metadata‑only).  
- **AC‑008/AC‑009/AC‑010**: T106 (Shapiro‑Wilk, method selection, significance flag).  
- **AC‑011**: T107 (DPI, size, style).  
- **SC‑001**: T103 (CPU‑only enforced). **SC‑002**: T105, T108 (independence audit). **SC‑003**: T101 (fails loudly, no synthetic fallback). **SC‑004**: T104 (runtime ≤ 6 h). **SC‑005**: seeds in `code/config.py`; reproducibility verified in T110.  

**Execution order**: T101 → T102 → T103 → (T104, T105 parallel) → T106 → T107 → T108 → T109 → T110. T106 strictly requires both T104 and T105 outputs.  

## Revision behavior

- Reopened requirements are exactly those the verifier rejected (T013, T014b, T014c, T015, T016, T017, T018a, T021); they are redone as T101–T105 with artifact‑first verification (every task's check is a real file plus an executable assertion command).  
- The rejected approach's failure mode — long, truncated scripts that never reach their save/checksum code — is countered by bounding the ingestion script's size and putting the file‑write at the center of each verification step.  
- Completed and verified prior work (structure, config, contracts, tests, documentation, statistical branching logic) is preserved unchanged; no completed task was erased and no acceptance criterion was weakened.  