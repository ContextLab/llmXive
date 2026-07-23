"""Visualization and reporting package."""
from .plots import (
    load_processed_data,
    load_model_results,
    create_scatter_plot,
    generate_scatter_plot_report,
    create_coefficient_plot,
    create_distribution_plot,
    main as plots_main
)
from .refactor_plots import (
    setup_figure,
    save_figure,
    add_timestamp_to_path,
    create_color_map,
    format_axis_labels,
    add_grid_to_axes,
    create_subplots_grid,
    log_plot_metadata
)

__all__ = [
    'load_processed_data', 'load_model_results', 'create_scatter_plot',
    'generate_scatter_plot_report', 'create_coefficient_plot',
    'create_distribution_plot', 'plots_main',
    'setup_figure', 'save_figure', 'add_timestamp_to_path',
    'create_color_map', 'format_axis_labels', 'add_grid_to_axes',
    'create_subplots_grid', 'log_plot_metadata'
]
