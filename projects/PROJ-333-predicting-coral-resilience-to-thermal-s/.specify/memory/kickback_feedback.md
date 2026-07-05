# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T019 'Stream FASTQ files... to generate count matrix' is not self-contained. It assumes the implementer knows the exact Salmon command-line flags, the reference index path (defined in T018 but not linked here), and the output format. It must explicitly state: 'Run salmon quant -i <index_path> -l A -r <fastq_path> -o <output_dir> --validateMappings' and define the expected output file 'data/processed/quant.sf'.
