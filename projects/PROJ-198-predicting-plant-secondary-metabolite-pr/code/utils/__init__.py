"""
Utilities package for the plant secondary metabolite prediction pipeline.
"""
from .phylogeny import (
    parse_newick_tree,
    get_tip_labels,
    calculate_cophenetic_distance_matrix,
    calculate_pvr_eigenvectors,
    run_pvr_regression,
    main as phylogeny_main
)
from .data_hygiene import (
    ensure_directory_structure,
    calculate_file_checksum,
    update_checksums_file,
    verify_checksums,
    main as hygiene_main
)
from .anti_smash_parser import (
    parse_anti_smash_json,
    extract_bgc_summary,
    bgc_summary_to_dataframe,
    get_bgc_counts_by_type,
    parse_anti_smash_directory,
    main as parser_main
)

__all__ = [
    # Phylogeny
    'parse_newick_tree',
    'get_tip_labels',
    'calculate_cophenetic_distance_matrix',
    'calculate_pvr_eigenvectors',
    'run_pvr_regression',
    'phylogeny_main',
    # Data Hygiene
    'ensure_directory_structure',
    'calculate_file_checksum',
    'update_checksums_file',
    'verify_checksums',
    'hygiene_main',
    # AntiSMASH Parser
    'parse_anti_smash_json',
    'extract_bgc_summary',
    'bgc_summary_to_dataframe',
    'get_bgc_counts_by_type',
    'parse_anti_smash_directory',
    'parser_main'
]
