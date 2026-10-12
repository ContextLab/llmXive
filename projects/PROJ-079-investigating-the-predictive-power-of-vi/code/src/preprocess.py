"""
src.preprocess
----------------
Implements preprocessing utilities for the project, notably the
`map_isg_genes` function which maps a list of human ISG gene symbols to
orthologous Ensembl gene identifiers for a target non‑human species using
the Ensembl Compara REST API (v109).

The module also provides a `normalize_counts` function that performs
TMM normalization using the edgeR R package via rpy2, and a new
`calculate_isg_score` function that computes the first principal component
(PC1) of the ISG gene expression matrix to obtain an interferon‑stimulated
gene (ISG) score per sample.
"""
import logging
from pathlib import Path
from typing import List

import pandas as pd
import requests
from sklearn.decomposition import PCA

from src.config import DATA_PROCESSED_PATH
from src.utils.logging import get_logger

# llmxive toolkit helpers for path handling
from llmxive_toolkit import paths, get_logger as llm_get_logger

# ----------------------------------------------------------------------
# Helper utilities for ISG mapping (unchanged)
# ----------------------------------------------------------------------
_ENSEMBL_REST_BASE = "https://rest.ensembl.org"
_HEADERS = {"Content-Type": "application/json", "User-Agent": "llmXive/1.0"}

def _lookup_human_gene(symbol: str) -> str:
    """
    Retrieve the Ensembl gene ID for a human gene symbol.

    Parameters
    ----------
    symbol : str
        Human gene symbol (e.g., "IFIT1").

    Returns
    -------
    str
        Ensembl gene ID (e.g., "ENSG00000105879").

    Raises
    ------
    RuntimeError
        If the gene cannot be found via the Ensembl REST API.
    """
    url = f"{_ENSEMBL_REST_BASE}/lookup/symbol/homo_sapiens/{symbol}"
    response = requests.get(url, headers=_HEADERS, timeout=10)
    if not response.ok:
        logger.error(
            f"Failed to lookup human gene symbol '{symbol}'. "
            f"Status: {response.status_code}"
        )
        raise RuntimeError(f"Ensembl lookup failed for symbol {symbol}")

    data = response.json()
    if "id" not in data:
        logger.error(
            f"No Ensembl ID returned for human gene symbol '{symbol}'."
        )
        raise RuntimeError(f"No Ensembl ID for symbol {symbol}")

    return data["id"]

def _fetch_ortholog(human_gene_id: str, target_species: str) -> str:
    """
    Retrieve the orthologous Ensembl gene ID for a given human gene ID
    and target species.

    Parameters
    ----------
    human_gene_id : str
        Ensembl gene ID for the human gene (e.g., "ENSG00000105879").
    target_species : str
        Ensembl species name (e.g., "mus_musculus").

    Returns
    -------
    str
        Ensembl gene ID of the ortholog in the target species.

    Raises
    ------
    RuntimeError
        If no ortholog is found.
    """
    species = target_species.lower().replace(" ", "_")
    url = (
        f"{_ENSEMBL_REST_BASE}/homology/id/{human_gene_id}"
        f"?target_species={species}&type=ortholog_one2one"
    )
    response = requests.get(url, headers=_HEADERS, timeout=10)
    if not response.ok:
        logger.error(
            f"Failed to fetch orthology for gene ID '{human_gene_id}' "
            f"to species '{species}'. Status: {response.status_code}"
        )
        raise RuntimeError(
            f"Ensembl homology request failed for {human_gene_id}"
        )

    data = response.json()
    homologies = data.get("data", [{}])[0].get("homologies", [])
    if not homologies:
        logger.warning(
            f"No orthologs found for human gene ID '{human_gene_id}' "
            f"in species '{species}'."
        )
        raise RuntimeError(
            f"No ortholog found for {human_gene_id} in {species}"
        )

    for entry in homologies:
        if entry.get("type") == "ortholog_one2one":
            target = entry.get("target")
            if target and target.get("id"):
                return target["id"]

    # Fallback to first entry if strict one‑to‑one not found
    first = homologies[0].get("target", {})
    orth_id = first.get("id")
    if orth_id:
        return orth_id

    raise RuntimeError(f"Unable to extract ortholog ID for {human_gene_id}")

# ----------------------------------------------------------------------
# Public API for ISG mapping (unchanged)
# ----------------------------------------------------------------------
def map_isg_genes(species: str, gene_list: list) -> list:
    """
    Maps human ISG gene symbols to orthologous Ensembl gene identifiers for
    a given target species using the Ensembl Compara REST API (v109).

    The function writes a CSV file ``data/processed/ortholog_map.csv`` with
    columns ``human_gene``, ``ortholog_gene`` and ``species``.  The CSV is
    comma‑delimited and uses UTF‑8 encoding.

    Parameters
    ----------
    species : str
        Target species name. Accepts either the Ensembl species identifier
        (e.g., ``mus_musculus``) or a common name (e.g., ``mouse``).  The
        function normalises the string to the Ensembl format.
    gene_list : list
        List of human ISG gene symbols (e.g., ``["IFIT1", "OAS1"]``).

    Returns
    -------
    list
        List of ortholog Ensembl gene IDs corresponding to the input
        symbols.  Genes for which an ortholog could not be resolved are
        omitted from the returned list.
    """
    if not gene_list:
        logger.warning("Empty gene list supplied to map_isg_genes.")
        return []

    species_norm = species.lower().replace(" ", "_")
    if species_norm in {"human", "homo sapiens", "homo_sapiens"}:
        species_norm = "homo_sapiens"
    elif species_norm in {"mouse", "mus musculus", "mus_musculus"}:
        species_norm = "mus_musculus"

    mappings = []  # List of tuples (human_gene, ortholog_gene, species)

    for symbol in gene_list:
        try:
            human_ensembl_id = _lookup_human_gene(symbol)
            logger.debug(
                f"Human gene {symbol} -> Ensembl ID {human_ensembl_id}"
            )

            if species_norm == "homo_sapiens":
                ortholog_id = human_ensembl_id
            else:
                ortholog_id = _fetch_ortholog(human_ensembl_id, species_norm)

            mappings.append((symbol, ortholog_id, species_norm))
            logger.info(
                f"Mapped {symbol} (human) -> {ortholog_id} ({species_norm})"
            )
        except Exception as exc:
            logger.error(
                f"Failed to map ISG gene '{symbol}' for species "
                f"'{species_norm}': {exc}"
            )

    if mappings:
        df = pd.DataFrame(
            mappings,
            columns=["human_gene", "ortholog_gene", "species"],
        )
        output_path = Path(DATA_PROCESSED_PATH) / "ortholog_map.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8")
        logger.info(f"Ortholog mapping saved to {output_path}")
    else:
        logger.warning(
            "No ortholog mappings were generated; CSV will not be created."
        )

    return [orth for _, orth, _ in mappings]

def validate_isg_mapping(mappings: list, raw_counts: pd.DataFrame) -> bool:
    """
    Validate that the ortholog identifiers produced by ``map_isg_genes``
    are present in the raw counts matrix.

    The function checks the proportion of mapped ortholog IDs that appear
    as row identifiers (index) in ``raw_counts``.  If at least 80 % of the
    mappings are found, validation passes and the function returns ``True``.
    Otherwise the function logs a warning, indicating that the sample (or
    dataset) should be excluded according to FR‑015, and returns ``False``.

    Parameters
    ----------
    mappings : list
        List of ortholog Ensembl gene IDs (as strings) returned by
        ``map_isg_genes``.
    raw_counts : pd.DataFrame
        Raw count matrix where rows correspond to gene identifiers
        (Ensembl IDs) and columns correspond to sample IDs.

    Returns
    -------
    bool
        ``True`` if ≥ 80 % of the mapped orthologs are present in the
        raw counts index; ``False`` otherwise.
    """
    if not mappings:
        logger.warning(
            "No ISG mappings provided for validation; treating as failed validation."
        )
        return False

    raw_gene_set = set(str(g) for g in raw_counts.index)

    present = sum(1 for ortho_id in mappings if str(ortho_id) in raw_gene_set)
    overlap_ratio = present / len(mappings)

    if overlap_ratio >= 0.80:
        logger.info(
            f"ISG mapping validation passed: {present}/{len(mappings)} "
            f"({overlap_ratio:.2%}) orthologs found in raw counts."
        )
        return True
    else:
        logger.warning(
            f"ISG mapping validation failed: only {present}/{len(mappings)} "
            f"({overlap_ratio:.2%}) orthologs found in raw counts. "
            "Sample will be marked as excluded per FR-015."
        )
        return False

# ----------------------------------------------------------------------
# New functionality: TMM normalization via edgeR
# ----------------------------------------------------------------------
def normalize_counts(counts_matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Perform TMM (Trimmed Mean of M-values) normalization on a raw counts
    matrix using the edgeR R package via rpy2.

    The input DataFrame must have genes as the index and sample IDs as
    columns.  The function returns a new DataFrame with the same shape,
    containing normalized counts.  The normalized matrix is written to
    ``data/processed/normalized_counts.csv`` as a tab‑separated file.

    Parameters
    ----------
    counts_matrix : pd.DataFrame
        Raw integer count matrix (genes × samples).

    Returns
    -------
    pd.DataFrame
        TMM‑normalized counts matrix.

    Raises
    ------
    RuntimeError
        If the edgeR R package cannot be loaded or the normalization fails.
    """
    logger = get_logger(__name__)

    # Import rpy2 and edgeR lazily to avoid import overhead when not used
    try:
        from rpy2.robjects import pandas2ri, r
        from rpy2.robjects.packages import importr
    except Exception as exc:
        logger.error(
            "Failed to import rpy2. Ensure the 'rpy2' Python package is installed."
        )
        raise RuntimeError("rpy2 import error") from exc

    # Activate automatic conversion between pandas and R data frames
    pandas2ri.activate()

    try:
        edgeR = importr("edgeR")
    except Exception as exc:
        logger.error(
            "The R package 'edgeR' is not available in the current R environment."
        )
        raise RuntimeError("edgeR R package not available") from exc

    # Convert pandas DataFrame to R matrix (edgeR expects a matrix or data.frame)
    r_counts = pandas2ri.py2rpy(counts_matrix)

    # Create DGEList object
    dge = edgeR.DGEList(counts=r_counts)

    # Calculate normalization factors (TMM)
    dge = edgeR.calcNormFactors(dge)

    # Obtain normalized counts using CPM with normalized library sizes
    # This yields counts per million that are already normalized.
    norm_counts_r = edgeR.cpm(dge, normalized_lib_sizes=True, log=False)

    # Convert back to pandas DataFrame
    norm_counts = pandas2ri.rpy2py(norm_counts_r)

    # Ensure the DataFrame retains original index/column labels
    norm_counts = pd.DataFrame(
        norm_counts,
        index=counts_matrix.index,
        columns=counts_matrix.columns,
    )

    # Write to the prescribed output location
    out_path = paths.data("processed", "normalized_counts.csv")
    norm_counts.to_csv(out_path, sep="\t")
    logger.info(f"Normalized counts written to {out_path}")

    return norm_counts

# ----------------------------------------------------------------------
# New functionality: ISG score calculation (PC1 of ISG genes)
# ----------------------------------------------------------------------
def calculate_isg_score(normalized_counts: pd.DataFrame, isg_genes: list) -> pd.Series:
    """
    Compute the first principal component (PC1) of the ISG gene expression
    matrix and use it as the interferon‑stimulated gene (ISG) score for
    each sample.

    The function expects ``normalized_counts`` to have genes as the
    index and sample identifiers as columns (as produced by
    ``normalize_counts``).  ``isg_genes`` should be a list of gene
    identifiers (Ensembl IDs) that correspond to rows in the
    ``normalized_counts`` DataFrame.

    Safety net:
    - Abort with a fatal RuntimeError if ``isg_genes`` is empty.
    - Abort with a fatal RuntimeError if none of the provided ISG genes are
      present in ``normalized_counts``.
    - Abort with a fatal RuntimeError if PCA fails for any reason.

    The resulting scores are saved to ``data/processed/isg_scores.csv`` with
    a single column ``isg_score`` and the sample identifier as the index.

    Parameters
    ----------
    normalized_counts : pd.DataFrame
        TMM‑normalized expression matrix (genes × samples).
    isg_genes : list
        List of ISG gene identifiers (must match the index of
        ``normalized_counts``).

    Returns
    -------
    pd.Series
        Series indexed by sample IDs containing the ISG PC1 score.
    """
    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # Validate input gene list
    # ------------------------------------------------------------------
    if not isg_genes:
        logger.error("Fatal: ISG gene set is empty.")
        raise RuntimeError("Fatal: ISG gene set is empty.")

    # Determine which ISG genes are actually present
    present_genes = [gene for gene in isg_genes if gene in normalized_counts.index]
    if not present_genes:
        logger.error(
            "Fatal: None of the provided ISG genes are present in the normalized counts matrix."
        )
        raise RuntimeError(
            "Fatal: No overlap between ISG gene set and normalized counts."
        )

    # Subset the matrix to ISG rows and transpose so samples are rows
    isg_matrix = normalized_counts.loc[present_genes].transpose()

    # ------------------------------------------------------------------
    # Perform PCA
    # ------------------------------------------------------------------
    try:
        pca = PCA(n_components=1)
        pc1_array = pca.fit_transform(isg_matrix.values)
        # Flatten to 1‑D array
        pc1_scores = pc1_array.ravel()
    except Exception as exc:
        logger.error(f"Fatal: PCA failed during ISG score calculation: {exc}")
        raise RuntimeError("Fatal: PCA failed during ISG score calculation") from exc

    # Build a Series with sample IDs as the index
    isg_score_series = pd.Series(
        pc1_scores,
        index=isg_matrix.index,
        name="isg_score",
    )
    isg_score_series.index.name = "sample_id"

    # ------------------------------------------------------------------
    # Persist results
    # ------------------------------------------------------------------
    out_path = paths.data("processed", "isg_scores.csv")
    # Ensure parent directory exists (paths.data does this)
    df_out = isg_score_series.to_frame()
    df_out.to_csv(out_path)
    logger.info(f"ISG scores written to {out_path}")

    return isg_score_series

# ----------------------------------------------------------------------
# New functionality: Filter rows with missing strain links
# ----------------------------------------------------------------------
def filter_samples(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows that lack a valid ``strain_accession`` identifier.

    This function is used after merging viral features with host ISG
    scores but before any downstream aggregation or count‑based checks.
    It simply drops any row where the ``strain_accession`` column is
    missing, empty, or consists solely of whitespace.

    Parameters
    ----------
    merged_df : pd.DataFrame
        DataFrame resulting from ``merge_datasets``; must contain a
        ``strain_accession`` column.

    Returns
    -------
    pd.DataFrame
        A filtered DataFrame containing only rows with a non‑null,
        non‑empty ``strain_accession`` value.

    Raises
    ------
    ValueError
        If the ``strain_accession`` column is absent from ``merged_df``.
    """
    logger = get_logger(__name__)

    if "strain_accession" not in merged_df.columns:
        logger.error("Column 'strain_accession' not found in merged DataFrame.")
        raise ValueError("merged_df must contain a 'strain_accession' column")

    initial_count = len(merged_df)

    # Keep rows where strain_accession is not NA and not just whitespace
    valid_mask = merged_df["strain_accession"].notna() & (
        merged_df["strain_accession"]
        .astype(str)
        .str.strip()
        .astype(bool)
    )
    filtered_df = merged_df[valid_mask].copy()

    removed = initial_count - len(filtered_df)
    logger.info(f"filter_samples: removed {removed} rows with missing strain links.")

    return filtered_df