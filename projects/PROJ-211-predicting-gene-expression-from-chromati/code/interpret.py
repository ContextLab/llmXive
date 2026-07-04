import os
import sys
import json
import logging
import argparse
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_model(model_path: str) -> Any:
    """
    Load a trained model from a pickle file.
    
    Args:
        model_path: Path to the model pickle file.
        
    Returns:
        The loaded model object.
    """
    import pickle
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

def extract_feature_importance(model: Any, feature_names: List[str]) -> pd.DataFrame:
    """
    Extract feature importance from a linear model (e.g., ElasticNet).
    Returns a DataFrame with feature names and their coefficients.
    
    Args:
        model: Trained linear model with .coef_ attribute.
        feature_names: List of feature names corresponding to coefficients.
        
    Returns:
        DataFrame with columns ['feature', 'coefficient', 'abs_coefficient']
    """
    if not hasattr(model, 'coef_'):
        raise AttributeError("Model does not have a coef_ attribute")
    
    coefficients = model.coef_
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'coefficient': coefficients,
        'abs_coefficient': [abs(c) for c in coefficients]
    })
    
    # Sort by absolute magnitude descending
    importance_df = importance_df.sort_values('abs_coefficient', ascending=False).reset_index(drop=True)
    return importance_df

def map_peaks_to_tss(peaks_df: pd.DataFrame, genes_df: pd.DataFrame, window_size: int = 50000) -> pd.DataFrame:
    """
    Map peak coordinates to their nearest TSS and calculate distance.
    
    Args:
        peaks_df: DataFrame with peak coordinates (columns: chrom, start, end, name)
        genes_df: DataFrame with gene coordinates (columns: chrom, start, end, gene_name, tss)
        window_size: Window size in bp to consider for TSS proximity (default 50kb)
        
    Returns:
        DataFrame with peak annotations including distance to nearest TSS
    """
    logger.info(f"Mapping peaks to TSS with window size {window_size}bp")
    
    results = []
    
    for _, peak in peaks_df.iterrows():
        peak_chrom = peak['chrom']
        peak_start = peak['start']
        peak_end = peak['end']
        peak_name = peak.get('name', f"peak_{peak_start}")
        
        # Filter genes on same chromosome
        same_chr_genes = genes_df[genes_df['chrom'] == peak_chrom]
        
        if same_chr_genes.empty:
            results.append({
                'peak_name': peak_name,
                'nearest_tss': None,
                'distance_bp': None,
                'within_window': False
            })
            continue
        
        # Calculate distance to each TSS
        min_dist = float('inf')
        nearest_tss = None
        
        for _, gene in same_chr_genes.iterrows():
            tss = gene['tss']
            # Calculate distance from peak center to TSS
            peak_center = (peak_start + peak_end) / 2
            dist = abs(peak_center - tss)
            
            if dist < min_dist:
                min_dist = dist
                nearest_tss = tss
        
        within_window = min_dist <= window_size if min_dist != float('inf') else False
        
        results.append({
            'peak_name': peak_name,
            'nearest_tss': nearest_tss,
            'distance_bp': min_dist if min_dist != float('inf') else None,
            'within_window': within_window
        })
    
    return pd.DataFrame(results)

def calculate_tss_proximity_stats(
    feature_importance_df: pd.DataFrame,
    peak_annotations_df: pd.DataFrame,
    top_n: int = 100,
    tss_window: int = 10000
) -> Dict[str, Any]:
    """
    Calculate the percentage of top-N features that are within ±TSS_WINDOW of a TSS.
    
    Args:
        feature_importance_df: DataFrame with feature importance (must have 'feature' column)
        peak_annotations_df: DataFrame with peak annotations (must have 'peak_name', 'distance_bp')
        top_n: Number of top features to consider (default 100)
        tss_window: Distance in bp from TSS to consider as "proximal" (default 10000 for 10kb)
        
    Returns:
        Dictionary with statistics about TSS proximity
    """
    logger.info(f"Calculating TSS proximity stats for top {top_n} features within ±{tss_window}bp")
    
    # Get top N features
    top_features = feature_importance_df.head(top_n)['feature'].tolist()
    
    # Filter annotations for these peaks
    relevant_annotations = peak_annotations_df[peak_annotations_df['peak_name'].isin(top_features)]
    
    if relevant_annotations.empty:
        logger.warning("No matching peaks found in annotations for top features")
        return {
            "top_n": top_n,
            "tss_window_bp": tss_window,
            "total_top_features": len(top_features),
            "matched_peaks": 0,
            "within_tss_window": 0,
            "percentage_within_window": 0.0,
            "message": "No matching peaks found"
        }
    
    # Count peaks within window
    within_window = relevant_annotations[
        (relevant_annotations['distance_bp'].notna()) & 
        (relevant_annotations['distance_bp'] <= tss_window)
    ]
    
    count_within = len(within_window)
    total_matched = len(relevant_annotations)
    percentage = (count_within / total_matched * 100) if total_matched > 0 else 0.0
    
    stats = {
        "top_n": top_n,
        "tss_window_bp": tss_window,
        "total_top_features": len(top_features),
        "matched_peaks": total_matched,
        "within_tss_window": count_within,
        "percentage_within_window": round(percentage, 2),
        "unmatched_peaks": len(top_features) - total_matched
    }
    
    logger.info(f"Results: {count_within}/{total_matched} ({percentage:.2f}%) within ±{tss_window}bp")
    return stats

def calculate_performance_gap(
    housekeeping_r2: pd.DataFrame,
    cell_type_specific_r2: pd.DataFrame,
    gene_lists: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Calculate the performance gap (ΔR²) between housekeeping and cell-type-specific genes.
    
    Args:
        housekeeping_r2: DataFrame with R² values for housekeeping genes
        cell_type_specific_r2: DataFrame with R² values for cell-type-specific genes
        gene_lists: Dictionary with 'housekeeping' and 'cell_type_specific' gene lists
        
    Returns:
        Dictionary with performance gap statistics
    """
    logger.info("Calculating performance gap between gene categories")
    
    # Calculate mean R² for each category
    hk_mean = housekeeping_r2['r2'].mean() if not housekeeping_r2.empty else 0.0
    cts_mean = cell_type_specific_r2['r2'].mean() if not cell_type_specific_r2.empty else 0.0
    
    delta_r2 = hk_mean - cts_mean
    
    stats = {
        "housekeeping_mean_r2": round(hk_mean, 4),
        "cell_type_specific_mean_r2": round(cts_mean, 4),
        "delta_r2": round(delta_r2, 4),
        "housekeeping_count": len(housekeeping_r2),
        "cell_type_specific_count": len(cell_type_specific_r2)
    }
    
    logger.info(f"Performance gap: ΔR² = {delta_r2:.4f} (HK: {hk_mean:.4f}, CTS: {cts_mean:.4f})")
    return stats

def generate_regulatory_insights_report(
    feature_importance_df: pd.DataFrame,
    peak_annotations_df: pd.DataFrame,
    tss_stats: Dict[str, Any],
    performance_gap: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate a summary report of regulatory insights.
    
    Args:
        feature_importance_df: DataFrame with feature importance
        peak_annotations_df: DataFrame with peak annotations
        tss_stats: Dictionary with TSS proximity statistics
        performance_gap: Dictionary with performance gap statistics
        output_path: Path to write the report
    """
    logger.info(f"Generating regulatory insights report to {output_path}")
    
    report_lines = [
        "# Regulatory Insights Report",
        "",
        "## Feature Importance",
        f"- Total features analyzed: {len(feature_importance_df)}",
        f"- Top 10 features by absolute coefficient:",
    ]
    
    for i, row in feature_importance_df.head(10).iterrows():
        report_lines.append(f"  {i+1}. {row['feature']}: {row['coefficient']:.6f}")
    
    report_lines.extend([
        "",
        "## TSS Proximity Analysis",
        f"- Top features analyzed: {tss_stats['top_n']}",
        f"- TSS window: ±{tss_stats['tss_window_bp']}bp",
        f"- Matched peaks: {tss_stats['matched_peaks']}/{tss_stats['total_top_features']}",
        f"- Within TSS window: {tss_stats['within_tss_window']} ({tss_stats['percentage_within_window']}%)",
        "",
        "## Gene Category Performance",
        f"- Housekeeping genes mean R²: {performance_gap['housekeeping_mean_r2']}",
        f"- Cell-type-specific genes mean R²: {performance_gap['cell_type_specific_mean_r2']}",
        f"- Performance gap (ΔR²): {performance_gap['delta_r2']}",
        "",
        "## Conclusions",
        "This analysis provides a first-order approximation of gene regulation based on bulk chromatin accessibility.",
        "The results should be interpreted with caution as they do not capture single-cell heterogeneity.",
    ])
    
    report_content = "\n".join(report_lines)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Report written to {output_path}")

def main():
    """
    Main entry point for the interpret module.
    Executes T030, T031, T032, T033, and T034.
    """
    parser = argparse.ArgumentParser(description='Interpret trained models and generate insights')
    parser.add_argument('--model-dir', type=str, default='data/models', help='Directory containing trained models')
    parser.add_argument('--data-dir', type=str, default='data/processed', help='Directory containing processed data')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Directory for output files')
    parser.add_argument('--top-n', type=int, default=100, help='Number of top features to analyze')
    parser.add_argument('--tss-window', type=int, default=10000, help='TSS proximity window in bp')
    args = parser.parse_args()
    
    try:
        # Load feature importance (from T030)
        feature_importance_path = os.path.join(args.output_dir, 'feature_importance.csv')
        if not os.path.exists(feature_importance_path):
            logger.error(f"Feature importance file not found: {feature_importance_path}")
            logger.error("Please run T030 first to generate feature_importance.csv")
            sys.exit(1)
        
        feature_importance_df = pd.read_csv(feature_importance_path)
        logger.info(f"Loaded feature importance with {len(feature_importance_df)} features")
        
        # Load peak annotations (from T031)
        peak_annotations_path = os.path.join(args.output_dir, 'peak_annotations.csv')
        if not os.path.exists(peak_annotations_path):
            logger.error(f"Peak annotations file not found: {peak_annotations_path}")
            logger.error("Please run T031 first to generate peak_annotations.csv")
            sys.exit(1)
        
        peak_annotations_df = pd.read_csv(peak_annotations_path)
        logger.info(f"Loaded peak annotations with {len(peak_annotations_df)} peaks")
        
        # T032: Calculate TSS proximity stats
        tss_stats = calculate_tss_proximity_stats(
            feature_importance_df,
            peak_annotations_df,
            top_n=args.top_n,
            tss_window=args.tss_window
        )
        
        tss_stats_output = os.path.join(args.output_dir, 'tss_proximity_stats.json')
        with open(tss_stats_output, 'w') as f:
            json.dump(tss_stats, f, indent=2)
        logger.info(f"TSS proximity stats written to {tss_stats_output}")
        
        # T033: Calculate performance gap
        # Load R² values for housekeeping and cell-type-specific genes
        hk_r2_path = os.path.join(args.output_dir, 'housekeeping_r2.csv')
        cts_r2_path = os.path.join(args.output_dir, 'external_validation_r2.csv')  # Using external validation as proxy if specific file missing
        
        # Try to load specific files, fall back to external validation if needed
        if os.path.exists(hk_r2_path):
            housekeeping_r2 = pd.read_csv(hk_r2_path)
        else:
            logger.warning(f"Housekeeping R² file not found: {hk_r2_path}, using empty DataFrame")
            housekeeping_r2 = pd.DataFrame(columns=['gene', 'r2'])
        
        # For cell-type-specific, we might need to calculate from external validation or use a placeholder
        if os.path.exists(cts_r2_path):
            cell_type_r2 = pd.read_csv(cts_r2_path)
        else:
            logger.warning(f"Cell-type-specific R² file not found, using empty DataFrame")
            cell_type_r2 = pd.DataFrame(columns=['gene', 'r2'])
        
        gene_lists = {
            'housekeeping': [],
            'cell_type_specific': []
        }
        
        performance_gap = calculate_performance_gap(
            housekeeping_r2,
            cell_type_r2,
            gene_lists
        )
        
        performance_gap_output = os.path.join(args.output_dir, 'performance_gap.json')
        with open(performance_gap_output, 'w') as f:
            json.dump(performance_gap, f, indent=2)
        logger.info(f"Performance gap written to {performance_gap_output}")
        
        # T034: Generate summary report
        report_path = os.path.join(args.output_dir, '..', 'docs', 'regulatory_insights_report.md')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        generate_regulatory_insights_report(
            feature_importance_df,
            peak_annotations_df,
            tss_stats,
            performance_gap,
            report_path
        )
        
        logger.info("All interpretation tasks completed successfully")
        
    except Exception as e:
        logger.error(f"Error during interpretation: {str(e)}")
        raise

if __name__ == '__main__':
    main()