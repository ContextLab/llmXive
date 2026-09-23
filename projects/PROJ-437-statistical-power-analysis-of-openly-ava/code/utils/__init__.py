"""Utilities package."""
from .seed_manager import set_global_seed, get_seed
from .memory_monitor import (
    get_current_memory_usage_gb,
    check_memory_threshold,
    trigger_gc,
    downsample_data,
    monitor_and_ensure_memory,
    main as memory_monitor_main,
)
from .timer import (
    start_run,
    end_run,
    log_split,
    save_timing_report,
    save_timing_breakdown,
    run_pipeline_with_timing,
    main as timer_main,
)
from .bootstrap_aggregator import (
    aggregate_power_results,
    compute_confidence_intervals,
    save_aggregated_results,
    main as bootstrap_aggregator_main,
)
