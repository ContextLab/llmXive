import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
import sys
import os

# Ensure code directory is in path if run directly
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code import logger

def load_cluster_data(cluster_path: Path) -> Dict[str, Any]:
    """Load cluster data from JSON file."""
    if not cluster_path.exists():
        logger.warning(f"Cluster data file not found: {cluster_path}")
        return {}
    with open(cluster_path, 'r') as f:
        return json.load(f)

def load_feature_importance(importance_path: Path) -> pd.DataFrame:
    """Load feature importance data from CSV or JSON."""
    if importance_path.suffix == '.csv':
        return pd.read_csv(importance_path)
    elif importance_path.suffix == '.json':
        with open(importance_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return pd.DataFrame(data)
            return pd.DataFrame([data])
    else:
        raise ValueError(f"Unsupported file format: {importance_path.suffix}")

def report_cluster_importance(cluster_data: Dict[str, Any], importance_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Calculate and report aggregate importance scores for correlated feature clusters."""
    if not cluster_data or importance_df.empty:
        return []

    results = []
    clusters = cluster_data.get('clusters', [])

    for cluster in clusters:
        cluster_name = cluster.get('name', 'Unknown')
        cluster_features = cluster.get('features', [])

        # Filter importance dataframe for cluster features
        cluster_importance = importance_df[importance_df['feature'].isin(cluster_features)]

        if not cluster_importance.empty:
            avg_importance = cluster_importance['importance'].mean()
            results.append({
                'cluster_name': cluster_name,
                'features': cluster_features,
                'aggregate_importance': float(avg_importance),
                'count': len(cluster_features)
            })

    # Sort by aggregate importance descending
    results.sort(key=lambda x: x['aggregate_importance'], reverse=True)
    return results

def calculate_cv_stability(df: pd.DataFrame, feature_columns: List[str]) -> Dict[str, Any]:
    """Calculate Coefficient of Variation for top features across folds."""
    result = {
        'status': 'incomplete',
        'reason': 'No fold-level data found',
        'top_features': []
    }

    # Check for fold-specific columns in the dataframe
    fold_cols = [col for col in df.columns if col.startswith('shap_fold_')]
    if not fold_cols:
        # Try to load from file if available
        json_path = Path("data/results/shap_fold_importances.json")
        if json_path.exists():
            with open(json_path, 'r') as f:
                fold_data = json.load(f)
            # Convert to DataFrame for calculation
            df_fold = pd.DataFrame(fold_data).T
            # Calculate stats
            top_features = []
            for feature in feature_columns:
                if feature in df_fold.columns:
                    values = df_fold[feature].dropna()
                    if len(values) > 0:
                        mean_val = values.mean()
                        std_val = values.std()
                        cv = (std_val / mean_val) if mean_val != 0 else 0
                        top_features.append({
                            'feature': feature,
                            'mean_importance': float(mean_val),
                            'std_importance': float(std_val),
                            'coefficient_of_variation': float(cv)
                        })
            if top_features:
                result['status'] = 'completed'
                result['reason'] = 'Data loaded from file'
                result['top_features'] = sorted(top_features, key=lambda x: x['mean_importance'], reverse=True)
            return result
        return result

    # Process fold columns from dataframe
    top_features = []
    for feature in feature_columns:
        fold_col = f'shap_fold_{feature}'
        if fold_col in df.columns:
            values = df[fold_col].dropna()
            if len(values) > 0:
                mean_val = values.mean()
                std_val = values.std()
                cv = (std_val / mean_val) if mean_val != 0 else 0
                top_features.append({
                    'feature': feature,
                    'mean_importance': float(mean_val),
                    'std_importance': float(std_val),
                    'coefficient_of_variation': float(cv)
                })

    if top_features:
        result['status'] = 'completed'
        result['reason'] = 'Data processed from dataframe'
        result['top_features'] = sorted(top_features, key=lambda x: x['mean_importance'], reverse=True)

    return result

def generate_interpretation(
    feature_importance: pd.DataFrame,
    correlation_matrix: pd.DataFrame,
    cluster_data: Dict[str, Any],
    physics_mappings: Dict[str, str]
) -> Dict[str, Any]:
    """
    Generate interpretation report with feature ranking, physical mechanisms,
    and correlation analysis.
    """
    interpretation = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'feature_ranking': [],
        'physical_mechanisms': {},
        'correlations': {},
        'warnings': []
    }

    # Get cluster information for suppression logic
    clusters = cluster_data.get('clusters', []) if cluster_data else []
    clustered_features = set()
    for cluster in clusters:
        clustered_features.update(cluster.get('features', []))

    # Rank features
    if 'importance' in feature_importance.columns:
        ranked = feature_importance.sort_values('importance', ascending=False)
    else:
        ranked = feature_importance

    for _, row in ranked.iterrows():
        feature = row.get('feature', row.index if hasattr(row, 'index') else 'unknown')
        importance = float(row.get('importance', 0))

        # Check if feature is in a correlated cluster
        is_clustered = feature in clustered_features
        mechanism = physics_mappings.get(feature, "Unknown mechanism")

        entry = {
            'feature': feature,
            'importance': importance,
            'mechanism': mechanism,
            'is_clustered': is_clustered
        }

        # Suppress individual causal claims for clustered features
        if is_clustered:
            entry['causal_claim_suppressed'] = True
            interpretation['warnings'].append(
                f"Feature '{feature}' is part of a correlated cluster. "
                "Individual causal claims suppressed per SC-003."
            )

        interpretation['feature_ranking'].append(entry)
        interpretation['physical_mechanisms'][feature] = mechanism

    # Add correlation data for top features
    if not ranked.empty:
        top_features = ranked.head(5)['feature'].tolist()
        for feat in top_features:
            if feat in correlation_matrix.columns and 'weibull_modulus' in correlation_matrix.columns:
                corr_val = correlation_matrix.loc[feat, 'weibull_modulus']
                interpretation['correlations'][feat] = float(corr_val)

    return interpretation

def sanitize_conclusion(text: str) -> str:
    """
    Remove 'cause' (case-insensitive, whole word) from text and append
    the required disclaimer as per FR-008.
    
    Args:
        text: The original text to sanitize.
        
    Returns:
        Sanitized text with 'cause' removed and disclaimer appended.
    """
    if not text:
        return "These results represent statistical associations only and do not imply causal relationships."
    
    # Remove 'cause' as a whole word, case-insensitive
    # \b ensures we match whole words only
    sanitized = re.sub(r'\bcause\b', '', text, flags=re.IGNORECASE)
    
    # Clean up any double spaces resulting from removal
    sanitized = re.sub(r'\s{2,}', ' ', sanitized).strip()
    
    # Append the mandatory disclaimer
    disclaimer = " These results represent statistical associations only and do not imply causal relationships."
    
    return sanitized + disclaimer

def generate_final_report(
    metrics: Dict[str, Any],
    interpretation: Dict[str, Any],
    stability_metrics: Dict[str, Any],
    output_path: Path
) -> Path:
    """
    Generate the final comprehensive report combining metrics, SHAP analysis,
    stability scores, and disclaimers.
    
    Args:
        metrics: Model performance metrics.
        interpretation: Feature interpretation data.
        stability_metrics: CV stability scores.
        output_path: Path where the report will be saved.
        
    Returns:
        Path to the generated report.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sanitize all text-based conclusions in the interpretation
    sanitized_interpretation = {}
    for key, value in interpretation.items():
        if isinstance(value, str):
            sanitized_interpretation[key] = sanitize_conclusion(value)
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized_nested = {}
            for k, v in value.items():
                if isinstance(v, str):
                    sanitized_nested[k] = sanitize_conclusion(v)
                else:
                    sanitized_nested[k] = v
            sanitized_interpretation[key] = sanitized_nested
        else:
            sanitized_interpretation[key] = value

    # Build final report structure
    final_report = {
        'report_version': '1.0',
        'generated_at': pd.Timestamp.now().isoformat(),
        'model_metrics': metrics,
        'interpretation': sanitized_interpretation,
        'stability_analysis': stability_metrics,
        'compliance': {
            'fr_008_disclaimer_applied': True,
            'disclaimer_text': "These results represent statistical associations only and do not imply causal relationships."
        }
    }
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Final report generated at {output_path}")
    return output_path

def main():
    """Main entry point for report generation (example usage)."""
    logging.basicConfig(level=logging.INFO)
    
    # Example: Load sample data and generate report
    # In practice, this would be called by the pipeline
    logger.info("Report module initialized.")
    logger.info("Use generate_final_report() to create the final compliance report.")

if __name__ == "__main__":
    main()
