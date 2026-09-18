"""
Data module for handling downloads, preprocessing, and alignment.
"""
from .download import DownloadError, download_genomes, download_metabolites, main
from .preprocess import (
    AntiSMASHError,
    MIBiGMappingError,
    map_bgc_to_metabolite,
    map_bgc_to_metabolite_dataframe,
    run_antiasmh_wrapper,
    harmonize_metabolites,
    main as preprocess_main,
)
from .align import align_data, save_aligned_matrix, calculate_alignment_success_rate, main as align_main
