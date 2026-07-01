import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Dict, Any
import json
import numpy as np

# Ensure seaborn style is consistent
sns.set(style="whitegrid", font_scale=1.1)

def generate_importance_plot(
    importance_df: pd.DataFrame,
    output_path: Path,
    title: str = "Feature Importance (Random Forest)"
) -> None:
    """
    Generate a horizontal bar chart of feature importances.
    
    Args:
        importance_df: DataFrame with columns ['feature', 'importance'].
        output_path: Path to save the figure.
        title: Plot title.
    """
    plt.figure(figsize=(10, 6))
    # Sort by importance
    importance_df = importance_df.sort_values(by='importance', ascending=True)
    
    sns.barplot(
        data=importance_df,
        x='importance',
        y='feature',
        palette="viridis"
    )
    plt.title(title)
    plt.xlabel("Importance Score")
    plt.ylabel("Feature")
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()

def generate_scatter_plots(
    data: pd.DataFrame,
    feature_cols: list,
    target_col: str,
    output_dir: Path
) -> None:
    """
    Generate scatter plots of each motion feature vs. agency scores.
    
    Args:
        data: DataFrame containing features and target.
        feature_cols: List of feature column names.
        target_col: Name of the target column (agency_score).
        output_dir: Directory to save plots.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for feature in feature_cols:
        if feature not in data.columns or target_col not in data.columns:
            continue
        
        plt.figure(figsize=(8, 6))
        sns.scatterplot(
            data=data,
            x=feature,
            y=target_col,
            alpha=0.6,
            edgecolor=None
        )
        plt.title(f"{feature} vs. {target_col}")
        plt.xlabel(feature)
        plt.ylabel(target_col)
        
        # Save
        safe_name = feature.replace(" ", "_").replace("-", "_")
        save_path = output_dir / f"scatter_{safe_name}.png"
        plt.savefig(save_path, dpi=300)
        plt.close()

def generate_partial_dependence(
    model: Any,
    data: pd.DataFrame,
    feature_col: str,
    output_path: Path,
    title: str = "Partial Dependence Plot"
) -> None:
    """
    Generate a partial dependence plot for a single feature using the provided model.
    This function computes the partial dependence manually using sklearn's 
    PartialDependenceDisplay logic or a simplified grid sweep if sklearn's 
    built-in is not directly available or if we need specific styling.
    
    For this implementation, we use sklearn's PartialDependenceDisplay for robustness,
    falling back to a manual grid calculation if necessary (though sklearn is standard).
    
    Args:
        model: Trained model (e.g., RandomForestRegressor).
        data: DataFrame with features used for training.
        feature_col: The name of the feature to plot.
        output_path: Path to save the figure.
        title: Plot title.
    """
    try:
        from sklearn.inspection import PartialDependenceDisplay
        
        # Ensure the feature exists
        if feature_col not in data.columns:
            raise ValueError(f"Feature '{feature_col}' not found in data.")
        
        # Prepare X for the display (ensure it matches model expectations)
        # We assume the model was trained on a subset of columns or the full dataframe
        # If the model expects a specific feature matrix, we pass that.
        # For simplicity, we pass the dataframe assuming the model can handle it 
        # or we extract the relevant columns if the model was trained on a subset.
        # To be safe, we assume `model` was trained on `data[feature_cols]` where feature_cols 
        # includes `feature_col`.
        
        # We need to know the feature names the model was trained on to index correctly.
        # If the model doesn't have feature_names_in_, we might need to infer or pass X.
        # Standard approach:
        X = data
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Create the display
        disp = PartialDependenceDisplay.from_estimator(
            model,
            X,
            features=[feature_col],
            ax=ax,
            kind='average'
        )
        
        plt.title(f"Partial Dependence: {feature_col} -> Predicted Agency")
        plt.xlabel(feature_col)
        plt.ylabel("Partial Dependence (Predicted Agency)")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300)
        plt.close()
        
    except ImportError:
        # Fallback if sklearn.inspection is not available (unlikely but safe)
        # Or if the model doesn't support it directly (e.g., some custom wrappers)
        # We perform a manual grid sweep:
        # 1. Create a grid of values for the feature of interest.
        # 2. For each value, set that feature to the grid value for all samples.
        # 3. Predict and average.
        
        if feature_col not in data.columns:
            raise ValueError(f"Feature '{feature_col}' not found in data.")
        
        # Determine range
        x_vals = np.linspace(data[feature_col].min(), data[feature_col].max(), 100)
        y_preds = []
        
        # Assume model.predict expects a DataFrame or array with same columns as training
        # We will create a copy of the data for each point to be safe, though it's slow.
        # Optimization: Only vary the target column.
        
        # Check if model has feature_names_in_ to match columns
        if hasattr(model, 'feature_names_in_'):
            feature_names = model.feature_names_in_
        else:
            # Fallback: assume columns match data.columns
            feature_names = data.columns.tolist()
        
        for x_val in x_vals:
            X_temp = data.copy()
            X_temp[feature_col] = x_val
            
            # Predict
            preds = model.predict(X_temp)
            y_preds.append(np.mean(preds))
        
        plt.figure(figsize=(8, 6))
        plt.plot(x_vals, y_preds, color='blue', linewidth=2)
        plt.fill_between(x_vals, y_preds, alpha=0.2, color='blue')
        plt.title(f"Partial Dependence: {feature_col} -> Predicted Agency")
        plt.xlabel(feature_col)
        plt.ylabel("Partial Dependence (Predicted Agency)")
        plt.grid(True, alpha=0.3)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300)
        plt.close()
