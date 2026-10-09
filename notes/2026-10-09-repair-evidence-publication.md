# Repair evidence publication contract

The runner retains raw observations in `evidence.json` and adds source-derived
dispatch hints only to the model input. Its result must hash the retained raw
input: hashing the augmented prompt context made every validated candidate fail
the publisher's unchanged evidence-integrity check.

A runner-to-publisher regression reproduces that failure before this fix and
verifies both successful application of unmodified artifacts and rejection of
tampered evidence before any source mutation. Model replies and isolated test
exits are fixture inputs in this contract test; it does not demonstrate a live
autonomous repair. The live trial at run 37937595531 uses the preceding deployed
head and remains separate evidence. Candidate regression, preservation and
independent-review requirements are unchanged.
