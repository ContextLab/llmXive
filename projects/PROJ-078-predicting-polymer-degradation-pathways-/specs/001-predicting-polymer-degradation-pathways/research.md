# Research: Predicting Polymer Degradation Pathways

**Feature**: Predicting Polymer Degradation Pathways

## Dataset Strategy

The project will utilize the following verified datasets:

| Dataset                               | URL                                                                    | Purpose                                                                   |
| ------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| NIST Cybersecurity Training Embeddings | https://huggingface.co/datasets/ethanolivertroy/nist-cybersecurity-training/resolve/main/embeddings/train_embeddings.parquet | Placeholder; will not be used for polymer data. |
| NIST Publications Raw                 | https://huggingface.co/datasets/ethanolivertroy/nist-publications-raw/resolve/main/metadata.json | Placeholder; will not be used for polymer data. |
| SMILES Transformers                   | https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet | Polymer SMILES strings                                                     |
| WebBooks-1                             | https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt | Polymer records (potential source of degradation information)                |
| new_vt_apis                            | https://huggingface.co/datasets/hmao/new_vt_apis/resolve/main/data/train-00000-of-00001-283ff2ab4f83ebe1.parquet | Placeholder; will not be used for polymer data. |
| cvecpe_apis                            | https://huggingface.co/datasets/hmao/cvecpe_apis/resolve/main/data/train-00000-of-00001-dfa2f47bf9593a3f.parquet | Placeholder; will not be used for polymer data. |
| all_apis_for_multiapi                  | https://huggingface.co/datasets/hmao/all_apis_for_multiapi/resolve/main/data/train-00000-of-00001-bd8d5e4d08813d65.parquet | Placeholder; will not be used for polymer data. |

The primary data source will be a combination of SMILES strings from the SMILES Transformers dataset and degradation information from WebBooks-1.  Data will be filtered to include only polyester compounds. If degradation labels are missing, the synthetic label distribution proposed in the specification will be applied.

## Decision/Rationale

*   **CPU-First**: The GNN training and feature attribution will be performed on the CPU due to the free-tier CI runner constraints.  A lightweight GNN architecture will be used to ensure efficient training within the resource limits.
*   **Data Streaming**: The project will leverage data streaming techniques (e.g., `datasets.load_dataset(streaming=True)`) to handle potentially large datasets without exceeding memory limits.
*   **No GPU Usage**: No GPU acceleration will be used in this project.
*   **Synthetic Labels**: Due to the potential lack of labeled degradation pathways in publicly available datasets, synthetic labels will be generated to provide training signals.

## Related Work

[Placeholder for related work citations]

## Experimental Design

The project will follow a three-phase approach:

1.  **Data Preparation:** Download, filter, and convert data from the selected sources into a graph-based dataset.
2.  **Model Training:** Train a lightweight GNN on the prepared dataset using 5-fold cross-validation.
3.  **Feature Attribution & Validation:** Compute feature importance scores using Integrated Gradients and validate the results using statistical tests.

## Risk Assessment

*   **Data Availability**: The availability of labeled degradation pathways may be limited. Synthetic labels will be used as a mitigation strategy.
*   **Computational Resources**: The free-tier CI runner has limited resources. A lightweight GNN architecture and data streaming techniques will be used to address this constraint.
*   **Data Quality**: Data from external sources may contain errors or inconsistencies. Data cleaning and validation procedures will be implemented.
