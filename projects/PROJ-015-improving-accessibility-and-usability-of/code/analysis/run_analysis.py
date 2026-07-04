from pathlib import Path
from config.settings import get_settings
from analysis.data_cleaner import DataCleaner
from analysis.stat_utils import StatUtils
from analysis.visualizer import Visualizer
import sys
import logging
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """
    Orchestrates the full analysis pipeline:
    1. Clean data
    2. Run statistical tests
    3. Generate descriptive stats
    4. Visualize results
    """
    settings = get_settings()
    raw_data_dir = settings.get('raw_data_dir', 'data/raw')
    processed_data_dir = settings.get('processed_data_dir', 'data/processed')
    
    # Ensure directories exist
    Path(processed_data_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting analysis pipeline...")
    
    # 1. Data Cleaning
    cleaner = DataCleaner()
    clean_df = cleaner.clean(raw_data_dir)
    
    if clean_df is None or clean_df.empty:
        logger.error("No valid data found after cleaning. Exiting.")
        return 1
    
    logger.info(f"Data cleaning complete. {len(clean_df)} valid sessions.")
    
    # 2. Generate Descriptive Stats (T023b)
    desc_output = Path(processed_data_dir) / "descriptive_stats.csv"
    if not StatUtils.generate_descriptive_stats_report(raw_data_dir, str(desc_output)):
        logger.warning("Failed to generate descriptive stats report.")
    
    # 3. Statistical Analysis (T022, T023, T024)
    # Run Shapiro-Wilk on difference scores for key metrics
    metrics_to_test = ['completion_time', 'error_count', 'sus_score']
    
    for metric in metrics_to_test:
        if metric in clean_df.columns:
            # Calculate difference (Explainable - Traditional) per participant
            # Requires pivoting
            try:
                wide = clean_df.pivot_table(index='participant_id', columns='interface_type', values=metric)
                if len(wide.columns) == 2:
                    diff = wide[wide.columns[1]] - wide[wide.columns[0]]
                    sw_result = StatUtils.run_shapiro_wilk(diff)
                    logger.info(f"Shapiro-Wilk for {metric} diff: stat={sw_result['statistic']:.4f}, p={sw_result['pvalue']:.4f}")
            except Exception as e:
                logger.warning(f"Could not compute Shapiro-Wilk for {metric}: {e}")
    
    # Run RM-ANOVA for key metrics
    for metric in ['completion_time', 'error_count', 'sus_score']:
        if metric in clean_df.columns:
            anova_result = StatUtils.run_repeated_measures_anova(
                clean_df, 
                within_subject_col='interface_type', 
                dependent_col=metric
            )
            logger.info(f"RM-ANOVA for {metric}: F={anova_result.get('F_statistic', 'N/A')}, p={anova_result.get('p_value', 'N/A')}")
    
    # 4. Visualization (T027)
    viz = Visualizer()
    viz.generate_box_plots(clean_df, metrics_to_test, processed_data_dir)
    
    logger.info("Analysis pipeline complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())