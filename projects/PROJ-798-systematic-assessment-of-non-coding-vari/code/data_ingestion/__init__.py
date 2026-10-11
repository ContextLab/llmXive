"""
Data ingestion module for downloading and processing raw genomic data.
Exposes helper functions at package level for convenient imports.
"""

# Re-export selected utilities from the module implementation so that
# sub‑modules (e.g., fetch_dbsnp.py) can use
# ``from data_ingestion import log_source_lineage, list_ftp_directory, download_ftp_file``.
from .data_ingestion import (
    log_source_lineage,
    list_ftp_directory,
    download_ftp_file,
    download_jaspar_pwms,
    download_file_http,
    download_ftp_file,
    find_common_snps_file,
    download_dbSNP_common_snps,
    download_1000Genomes_snps,
    download_regulatory_regions,
    load_snps_from_vcf,
    load_regulatory_regions,
    intersect_snps_with_regions,
)

__all__ = [
    "log_source_lineage",
    "list_ftp_directory",
    "download_ftp_file",
    "download_jaspar_pwms",
    "download_file_http",
    "find_common_snps_file",
    "download_dbSNP_common_snps",
    "download_1000Genomes_snps",
    "download_regulatory_regions",
    "load_snps_from_vcf",
    "load_regulatory_regions",
    "intersect_snps_with_regions",
]
