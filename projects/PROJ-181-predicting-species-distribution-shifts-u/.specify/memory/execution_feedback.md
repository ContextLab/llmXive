# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 run-book script(s) missing (plan/impl path mismatch): python code/main.py download; python code/main.py preprocess; python code/main.py train; 2 declared deliverable(s) absent: data/raw/occurrence_1970_2000.csv; data/raw/occurrence_2005_2020.csv

## Failing / missing run-book commands

- python code/main.py download -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-181-predicting-species-distribution-shifts-u/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py preprocess -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-181-predicting-species-distribution-shifts-u/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py train -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-181-predicting-species-distribution-shifts-u/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py evaluate -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-181-predicting-species-distribution-shifts-u/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py report -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-181-predicting-species-distribution-shifts-u/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/raw/occurrence_1970_2000.csv
- data/raw/occurrence_2005_2020.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `pygbif` to the project's `requirements.txt` and `pip install pygbif`.
- **Verified**: this loads **300** real records with fields: key, datasetKey, publishingOrgKey, datasetCategory, installationKey, hostingOrganizationKey, publishingCountry, protocol, lastCrawled, lastParsed, crawlId, extensions, basisOfRecord, occurrenceStatus, classifications, taxonKey, kingdomKey, phylumKey, classKey, orderKey, familyKey, genusKey, speciesKey, acceptedTaxonKey, scientificName, acceptedScientificName, kingdom, phylum, order, family, genus, species, genericName, specificEpithet, infraspecificEpithet, taxonRank, taxonomicStatus, decimalLatitude, decimalLongitude, continent, gadm, year, month, day, eventDate, startDayOfYear, endDayOfYear, issues, lastInterpreted, license, isSequenced, identifiers, media, facts, relations, isInCluster, recordedBy, dnaSequenceID, nucleotideSequence, geodeticDatum, class, countryCode, recordedByIDs, identifiedByIDs, gbifRegion, country, publishedByGbifRegion, http://unknown.org/download, datasetTitle, catalogNumber, http://unknown.org/crawl_attempt, http://unknown.org/orphanEndpoint, institutionCode, locality, http://unknown.org/status, http://unknown.org/griddedDataset, collectionCode, gbifID.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from pygbif import occurrences as occ

res = occ.search()
records = res.get('results', [])
if not records:
    raise ValueError('No occurrence records returned')
print(f"RECORDS={len(records)}")
print('FIELDS=' + ','.join(records[0].keys()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/occurrence_1970_2000.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download.py` — NOT invoked by the run-book
    - `code/manifest_manager.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/occurrence_1970_2000.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/occurrence_2005_2020.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download.py` — NOT invoked by the run-book
    - `code/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/occurrence_2005_2020.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
