# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): The verification test run failed (exit 1): all three tests failed — MS MARCO and Spider fetches raise `DataFetchError` because `datasets` cannot import (pyarrow requires NumPy 2.0+, environment has 1.26.4), and the DBpedia TTL download returns 404 for `https://raw.githubusercontent.com/RDFWebTools/rdf-samples/master/dbpedia-sample.ttl`, so no real row was fetched from any source. The task explicitly requires a real fetch to succeed and a unit test fetching ≥1 real row per source; the implementer must fix the environment/dependency issue (e.g. pin compatible numpy/pyarrow or handle the import)

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

