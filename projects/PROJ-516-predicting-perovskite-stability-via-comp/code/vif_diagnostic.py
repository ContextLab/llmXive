import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNetCV
from sklearn.preprocessing import StandardScaler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

VIF_THRESHOLD = 5.0

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame containing features.
        feature_cols: List of column names to calculate VIF for.
        
    Returns:
        DataFrame with 'feature', 'vif' columns.
    """
    if len(feature_cols) == 0:
        logger.warning("No features provided for VIF calculation.")
        return pd.DataFrame(columns=['feature', 'vif'])

    X = df[feature_cols].copy()
    
    # Handle constant columns (infinite VIF)
    # Replace zero variance with a large VIF value
    vif_data = []
    
    for i, col in enumerate(feature_cols):
        if X[col].var() == 0:
            vif_val = float('inf')
        else:
            # VIF = 1 / (1 - R^2) where R^2 is from regressing col on all other features
            other_cols = [c for c in feature_cols if c != col]
            if len(other_cols) == 0:
                vif_val = 1.0
            else:
                try:
                    y = X[col]
                    X_other = X[other_cols]
                    
                    # Fit linear regression
                    model = ElasticNetCV(cv=3, random_state=42, l1_ratio=0.5)
                    model.fit(X_other, y)
                    r2 = model.score(X_other, y)
                    
                    if r2 >= 1.0:
                        vif_val = float('inf')
                    else:
                        vif_val = 1.0 / (1.0 - r2)
                except Exception as e:
                    logger.warning(f"Could not calculate VIF for {col}: {e}")
                    vif_val = float('inf')
        
        vif_data.append({'feature': col, 'vif': vif_val})
    
    return pd.DataFrame(vif_data)

def select_features_with_elastic_net(X: pd.DataFrame, y: pd.Series, 
                                     max_features: int = 20) -> List[str]:
    """
    Select features using Elastic Net regularization.
    
    Args:
        X: Feature DataFrame.
        y: Target Series.
        max_features: Maximum number of features to select.
        
    Returns:
        List of selected feature names.
    """
    if X.shape[1] == 0:
        return []
        
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Use ElasticNetCV to find non-zero coefficients
    # L1 ratio 1.0 is Lasso, 0.0 is Ridge. We use a mix but lean towards Lasso for selection.
    model = ElasticNetCV(l1_ratio=0.8, cv=5, random_state=42, n_alphas=100)
    model.fit(X_scaled, y)
    
    # Get indices of non-zero coefficients
    non_zero_mask = model.coef_ != 0
    selected_indices = np.where(non_zero_mask)[0]
    
    # If too many, we need to select top ones based on absolute coefficient magnitude
    if len(selected_indices) > max_features:
        abs_coefs = np.abs(model.coef_[selected_indices])
        top_k_indices = selected_indices[np.argsort(abs_coefs)[-max_features:]]
        selected_indices = np.sort(top_k_indices)
    
    return [X.columns[i] for i in selected_indices]

def run_vif_diagnostic(input_path: Path, output_path: Path, 
                       target_col: str = 'T_d', 
                       feature_cols: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Run VIF diagnostic on the dataset, flag high-VIF features, and optionally
    suggest feature removal or Elastic Net fallback.
    
    Args:
        input_path: Path to input descriptors CSV.
        output_path: Path to write VIF report CSV.
        target_col: Name of the target column.
        feature_cols: Optional list of feature columns. If None, all numeric cols
                      except target are used.
                      
    Returns:
        Tuple of (success, list of removed/high-VIF features).
    """
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return False, []
        
    df = pd.read_csv(input_path)
    
    if feature_cols is None:
        # Select all numeric columns except target
        feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                       if col != target_col]
    
    logger.info(f"Calculating VIF for {len(feature_cols)} features: {feature_cols}")
    
    vif_df = calculate_vif(df, feature_cols)
    
    # Sort by VIF descending
    vif_df = vif_df.sort_values(by='vif', ascending=False)
    
    # Identify high VIF features
    high_vif_features = vif_df[vif_df['vif'] > VIF_THRESHOLD]['feature'].tolist()
    
    logger.warning(f"Found {len(high_vif_features)} features with VIF > {VIF_THRESHOLD}: {high_vif_features}")
    
    # Prepare report
    report_data = []
    for _, row in vif_df.iterrows():
        feature = row['feature']
        vif_val = row['vif']
        status = "HIGH" if vif_val > VIF_THRESHOLD else "OK"
        
        # Determine action
        action = "Keep"
        if vif_val == float('inf'):
            action = "Remove (Constant)"
        elif vif_val > VIF_THRESHOLD:
            action = "Remove or Elastic Net Fallback"
            
        report_data.append({
            'feature': feature,
            'vif': vif_val if vif_val != float('inf') else np.nan,
            'status': status,
            'action': action
        })
    
    report_df = pd.DataFrame(report_data)
    
    # Save report
    logger.info(f"Writing VIF report to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(output_path, index=False)
    
    # If high VIF features exist, suggest Elastic Net selection
    if len(high_vif_features) > 0:
        logger.info("High VIF detected. Suggesting Elastic Net feature selection as fallback.")
        # We don't modify the data here, just report the recommendation
        # The actual selection would happen in model_training or a preprocessing step
        
    return True, high_vif_features

def main():
    """Main entry point for VIF diagnostic script."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "processed" / "descriptors.csv"
    output_path = project_root / "data" / "processed" / "vif_report.csv"
    
    success, high_vif_features = run_vif_diagnostic(input_path, output_path)
    
    if success:
        logger.info(f"VIF diagnostic completed. Report saved to {output_path}")
        if high_vif_features:
            logger.warning(f"Features with VIF > {VIF_THRESHOLD}: {high_vif_features}")
            logger.info("Recommendation: Use Elastic Net regularization or remove these features.")
        else:
            logger.info("No features with VIF > 5.0 detected.")
    else:
        logger.error("VIF diagnostic failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
