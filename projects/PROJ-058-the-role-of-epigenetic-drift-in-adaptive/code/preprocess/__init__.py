"""
Preprocessing module for data normalization and filtering.
"""

from rna_seq import (
    load_rna_seq_data,
    median_of_ratios_normalization,
    calculate_gene_variance,
    get_sample_metadata,
    logo_jackknife_variance,
    filter_low_variance_genes,
    process_rna_seq,
    main
)

from methyl import (
    load_methyl_data,
    cpg_density_normalization,
    calculate_gene_variance,
    get_sample_metadata,
    logo_jackknife_variance,
    filter_low_variance_genes,
    process_methyl_data,
    main
)

from filters import (
    normalize_organism_name,
    is_model_organism,
    filter_by_organism,
    filter_by_global_methylation_level,
    apply_global_filters,
    main
)

from filter_genes import (
    load_variance_matrix,
    filter_genes_by_variance_and_missing,
    save_filtered_data,
    main
)

__all__ = [
    # RNA-seq
    "load_rna_seq_data",
    "median_of_ratios_normalization",
    "calculate_gene_variance",
    "get_sample_metadata",
    "logo_jackknife_variance",
    "filter_low_variance_genes",
    "process_rna_seq",
    # Methylation
    "load_methyl_data",
    "cpg_density_normalization",
    "get_sample_metadata",
    "logo_jackknife_variance",
    "filter_low_variance_genes",
    "process_methyl_data",
    # Filters
    "normalize_organism_name",
    "is_model_organism",
    "filter_by_organism",
    "filter_by_global_methylation_level",
    "apply_global_filters",
    # Gene filtering
    "load_variance_matrix",
    "filter_genes_by_variance_and_missing",
    "save_filtered_data"
]
