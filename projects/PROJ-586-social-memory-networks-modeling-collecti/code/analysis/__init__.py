"""Analysis package initialization."""
from .anova import ANOVAOutput, load_experiment_results, prepare_data_for_anova, compute_two_way_anova, compute_manual_anova, apply_bonferroni_correction, run_anova_analysis, main
from .power import PowerAnalysisResult, compute_effect_size, compute_power, compute_detectable_effect_size, run_power_analysis, generate_power_report, main
from .scaling import PowerLawFitResult, ScalingAnalysisResult, power_law_function, fit_power_law, load_scaling_data, aggregate_metrics_by_agent_count, run_scaling_analysis, generate_scaling_plot, main
from .sensitivity import run_game_simulation, run_sensitivity_analysis, generate_sensitivity_plot, main

__all__ = [
    'ANOVAOutput', 'load_experiment_results', 'prepare_data_for_anova',
    'compute_two_way_anova', 'compute_manual_anova', 'apply_bonferroni_correction',
    'run_anova_analysis', 'PowerAnalysisResult', 'compute_effect_size',
    'compute_power', 'compute_detectable_effect_size', 'run_power_analysis',
    'generate_power_report', 'PowerLawFitResult', 'ScalingAnalysisResult',
    'power_law_function', 'fit_power_law', 'load_scaling_data',
    'aggregate_metrics_by_agent_count', 'run_scaling_analysis', 'generate_scaling_plot',
    'run_game_simulation', 'run_sensitivity_analysis', 'generate_sensitivity_plot'
]
