"""
Validation package initialization.
Exposes the public API of the validation sub‑modules.
"""
from .compute_reliability import compute_split_half_reliability, main as reliability_main
from .compute_convergent import compute_convergent_correlation, main as convergent_main
from .select_subset import (
    find_external_scale_file,
    load_data,
    stratified_sample,
    write_subset,
    main as select_subset_main,
)
from .generate_report import (
    ValidationResult,
    load_validation_subset,
    generate_yaml_summary,
    generate_pdf_report,
    main as generate_report_main,
)
