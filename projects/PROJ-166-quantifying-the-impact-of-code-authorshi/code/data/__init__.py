# code.data package
from .extract_github import (
    check_memory_usage,
    shallow_clone,
    parse_git_log_and_count_authors,
    run_cloc_on_clone,
    process_repo,
    main
)
from .generate_target_list import (
    fetch_repo_metadata,
    generate_target_list,
    main as generate_target_list_main
)
from .download_nvd import (
    calculate_sha256,
    fetch_nvd_feed,
    download_all_nvd_feeds,
    deduplicate_cves,
    save_and_compress,
    generate_checksum,
    main as download_nvd_main
)
from .merge_datasets import (
    load_target_list,
    load_github_metrics,
    load_nvd_cves,
    count_cves_per_repo,
    merge_datasets,
    validate_merged_data,
    main as merge_datasets_main
)
from .utils import (
    run_command,
    parse_git_log,
    run_cloc
)
from .schemas import (
    get_schema,
    validate_dataframe
)

__all__ = [
    'check_memory_usage',
    'shallow_clone',
    'parse_git_log_and_count_authors',
    'run_cloc_on_clone',
    'process_repo',
    'main',
    'fetch_repo_metadata',
    'generate_target_list',
    'generate_target_list_main',
    'calculate_sha256',
    'fetch_nvd_feed',
    'download_all_nvd_feeds',
    'deduplicate_cves',
    'save_and_compress',
    'generate_checksum',
    'download_nvd_main',
    'load_target_list',
    'load_github_metrics',
    'load_nvd_cves',
    'count_cves_per_repo',
    'merge_datasets',
    'validate_merged_data',
    'merge_datasets_main',
    'run_command',
    'parse_git_log',
    'run_cloc',
    'get_schema',
    'validate_dataframe'
]