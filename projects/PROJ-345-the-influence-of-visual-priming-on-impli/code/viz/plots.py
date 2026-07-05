import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from statsmodels.iolib.table import SimpleTable
import io
import base64

from config import get_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_interaction_plot(
    df: pd.DataFrame,
    x_col: str = "prime_valence",
    y_col: str = "mean_response_time",
    hue_col: str = "stimulus_ambiguity",
    title: str = "Interaction Plot: Prime Valence x Ambiguity",
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate an interaction plot showing response time differences across prime valence
    and stimulus ambiguity.

    Args:
        df: DataFrame containing the aggregated data.
        x_col: Column name for the x-axis (prime condition).
        y_col: Column name for the y-axis (response time).
        hue_col: Column name for the grouping variable (ambiguity).
        title: Plot title.
        output_path: Path to save the plot. If None, saves to data/processed/figures/.

    Returns:
        Path to the saved plot file.
    """
    if output_path is None:
        output_dir = get_path("data/processed/figures")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "interaction_plot.png"
    else:
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 6))
    
    # Ensure categorical columns are treated correctly
    df[x_col] = pd.Categorical(df[x_col])
    if hue_col in df.columns:
        df[hue_col] = pd.Categorical(df[hue_col])

    # Use seaborn for easier interaction plotting if available, otherwise manual
    try:
        import seaborn as sns
        sns.set(style="whitegrid")
        sns.pointplot(
            data=df,
            x=x_col,
            y=y_col,
            hue=hue_col,
            ci=95,
            capsize=0.1,
            dodge=True,
            palette="muted"
        )
        plt.title(title)
        plt.ylabel("Mean Response Time (ms)")
        plt.xlabel("Prime Valence")
        plt.legend(title="Stimulus Ambiguity")
    except ImportError:
        logger.warning("Seaborn not found. Falling back to matplotlib pointplot logic.")
        # Fallback to basic matplotlib
        for val in df[hue_col].unique():
            subset = df[df[hue_col] == val]
            plt.errorbar(
                subset[x_col],
                subset[y_col],
                yerr=subset['std_dev'] if 'std_dev' in subset else 0,
                fmt='-o',
                label=str(val)
            )
        plt.title(title)
        plt.ylabel("Mean Response Time (ms)")
        plt.xlabel("Prime Valence")
        plt.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Interaction plot saved to {output_path}")
    return output_path

def generate_coefficient_table_from_df(
    df: pd.DataFrame,
    columns_map: Dict[str, str],
    precision: int = 4
) -> pd.DataFrame:
    """
    Transform a raw model results DataFrame into a formatted coefficient table
    with p-values and confidence intervals.

    Args:
        df: DataFrame containing model results (e.g., from statsmodels summary).
        columns_map: Mapping of expected column names in df to output names.
                    Expected keys: 'coef', 'std err', 't', 'P>|t|', '0.025', '0.975'
        precision: Number of decimal places for formatting.

    Returns:
        Formatted DataFrame ready for table generation or export.
    """
    required_cols = ['coef', 'std err', 't', 'P>|t|', '0.025', '0.975']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Model results DataFrame missing columns: {missing}")

    table_df = pd.DataFrame()
    
    # Map coefficients
    table_df['Term'] = df.index
    table_df['Estimate'] = df[columns_map.get('coef', 'coef')].round(precision)
    table_df['Std Error'] = df[columns_map.get('std err', 'std err')].round(precision)
    table_df['t-stat'] = df[columns_map.get('t', 't')].round(precision)
    table_df['p-value'] = df[columns_map.get('P>|t|', 'P>|t|')].round(precision)
    table_df['Lower 95% CI'] = df[columns_map.get('0.025', '0.025')].round(precision)
    table_df['Upper 95% CI'] = df[columns_map.get('0.975', '0.975')].round(precision)

    # Add significance stars
    def add_stars(p):
        if p < 0.001: return '***'
        if p < 0.01: return '**'
        if p < 0.05: return '*'
        if p < 0.1: return '.'
        return ''

    table_df['Significance'] = table_df['p-value'].apply(add_stars)
    
    return table_df

def generate_coefficient_table(
    model_results: Any,
    output_path: Optional[Path] = None,
    format_type: str = "csv"
) -> Path:
    """
    Generate a coefficient table with p-values and confidence intervals from a fitted model.
    Supports statsmodels MixedLM or similar objects.
    
    This function extracts the fixed effects parameters, standard errors, t-values,
    p-values, and confidence intervals, then formats them into a table.

    Args:
        model_results: The fitted model object (e.g., from statsmodels).
        output_path: Path to save the table. If None, saves to data/processed/tables/.
        format_type: Output format ('csv', 'png', 'pdf').

    Returns:
        Path to the generated artifact.
    """
    if output_path is None:
        output_dir = get_path("data/processed/tables")
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = "coefficient_table"
        if format_type == "png":
            output_path = output_dir / f"{base_name}.png"
        elif format_type == "pdf":
            output_path = output_dir / f"{base_name}.pdf"
        else:
            output_path = output_dir / f"{base_name}.csv"
    else:
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

    # Extract fixed effects summary
    # Assuming statsmodels MixedLM or similar structure
    if hasattr(model_results, 'summary2'):
        # statsmodels object
        summary = model_results.summary2()
        # summary.tables[0] usually contains the coefficient table
        if len(summary.tables) > 0:
            table_data = summary.tables[0]
            # Convert to DataFrame if possible, or parse manually
            # statsmodels summary2 tables have a 'data' attribute
            if hasattr(table_data, 'data'):
                df = pd.DataFrame(table_data.data[1:], columns=table_data.data[0])
                # Clean up column names if they contain extra spaces
                df.columns = df.columns.str.strip()
            else:
                # Fallback: try to extract from summary as string or dict
                # This is less robust but handles edge cases
                logger.warning("Could not directly extract table data from summary2. Attempting fallback.")
                # Re-run summary to get the dict representation if available
                # For now, we assume the standard statsmodels output structure
                # We will reconstruct from the model results directly if summary2 is tricky
                df = model_results.summary().tables[1].data[1:] # Skip header row
                # This is a hacky fallback for specific statsmodels versions
                # A more robust way is to use the params, bse, tvalues, pvalues
                pass
    
    # Robust extraction using model attributes directly
    if hasattr(model_results, 'params'):
        params = model_results.params
        bse = model_results.bse
        tvalues = model_results.tvalues
        pvalues = model_results.pvalues
        conf_int = model_results.conf_int()

        table_df = pd.DataFrame({
            'Term': params.index,
            'Estimate': params.values,
            'Std Error': bse.values,
            't-stat': tvalues.values,
            'p-value': pvalues.values,
            'Lower 95% CI': conf_int.iloc[:, 0].values,
            'Upper 95% CI': conf_int.iloc[:, 1].values
        })

        # Add significance stars
        def add_stars(p):
            if p < 0.001: return '***'
            if p < 0.01: return '**'
            if p < 0.05: return '*'
            if p < 0.1: return '.'
            return ''

        table_df['Significance'] = table_df['p-value'].apply(add_stars)
        
        # Round for display
        for col in ['Estimate', 'Std Error', 't-stat', 'p-value', 'Lower 95% CI', 'Upper 95% CI']:
            table_df[col] = table_df[col].round(4)

        if format_type == "csv":
            table_df.to_csv(output_path, index=False)
            logger.info(f"Coefficient table saved to CSV: {output_path}")
        
        elif format_type in ["png", "pdf"]:
            # Create a figure for the table
            fig, ax = plt.subplots(figsize=(10, 0.5 * len(table_df) + 1))
            ax.axis('off')
            ax.axis('tight')
            
            # Use matplotlib table
            table = ax.table(
                cellText=table_df.values,
                colLabels=table_df.columns,
                cellLoc='center',
                loc='center'
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.5)
            
            plt.title("Model Coefficients", pad=20)
            plt.tight_layout()
            
            if format_type == "png":
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                logger.info(f"Coefficient table saved to PNG: {output_path}")
            else:
                plt.savefig(output_path, bbox_inches='tight')
                logger.info(f"Coefficient table saved to PDF: {output_path}")
            
            plt.close()
        
        return output_path
    
    else:
        raise ValueError("Model results object does not have expected attributes (params, bse, etc.)")

def main():
    """
    Main entry point for T034: Generate coefficient tables from pre-computed model results.
    This script expects the LMM model results to be available in a serialized format
    or to be re-fitted if the data pipeline has been run.
    
    For the purpose of this task, we assume the model results are passed or loaded.
    Since the task is to 'implement the generation', we create a script that
    loads the processed data, fits the model (if not already done), and generates the table.
    
    In a real pipeline, this would load the fitted model from state/ or data/.
    Here we simulate the flow: Load Data -> Fit Model -> Generate Table.
    """
    logger.info("Starting T034: Coefficient Table Generation")
    
    # 1. Load data (Simulating the output of US2)
    # We expect 'data/processed/linked_trials.csv' or similar aggregated data
    data_path = get_path("data/processed/linked_trials.csv")
    if not data_path.exists():
        # Fallback to a more specific path if T017 output was different
        data_path = get_path("data/processed/stimulus_level_data.csv")
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}. Cannot generate table.")
        return

    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded data from {data_path}, shape: {df.shape}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return

    # 2. Fit the LMM model (Simulating US2 T025)
    # Formula: mean_response_time ~ prime_valence * stimulus_ambiguity + (1 | participant_id)
    # We need to ensure columns exist
    required_cols = ['mean_response_time', 'prime_valence', 'stimulus_ambiguity', 'participant_id']
    if not all(col in df.columns for col in required_cols):
        # Try to map common names if exact names differ
        if 'response_time' in df.columns:
            df['mean_response_time'] = df['response_time']
        if 'prime_condition' in df.columns:
            df['prime_valence'] = df['prime_condition']
        if 'ambiguity' in df.columns:
            df['stimulus_ambiguity'] = df['ambiguity']
        
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Missing required columns for modeling. Found: {df.columns.tolist()}")
            return

    from statsmodels.regression.mixed_linear_model import MixedLM
    
    # Prepare data
    # Ensure categorical variables are treated as such
    df['prime_valence'] = pd.Categorical(df['prime_valence'])
    df['stimulus_ambiguity'] = pd.Categorical(df['stimulus_ambiguity'])
    df['participant_id'] = df['participant_id'].astype(str)

    formula = "mean_response_time ~ C(prime_valence) * C(stimulus_ambiguity)"
    re_formula = "1"
    
    try:
        model = MixedLM.from_formula(formula, re_formula=re_formula, groups=df['participant_id'], data=df)
        result = model.fit()
        logger.info("Model fitted successfully.")
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return

    # 3. Generate the Coefficient Table
    output_path = get_path("data/processed/tables/coefficient_table.csv")
    table_path = generate_coefficient_table(result, output_path=output_path, format_type="csv")
    logger.info(f"Coefficient table generated at {table_path}")

    # Also generate a visual representation (PNG) for the report
    png_path = get_path("data/processed/tables/coefficient_table.png")
    generate_coefficient_table(result, output_path=png_path, format_type="png")
    logger.info(f"Coefficient table image generated at {png_path}")

    logger.info("T034 completed successfully.")

if __name__ == "__main__":
    main()