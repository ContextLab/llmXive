import logging
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import Binomial
from utils.logging import get_logger

logger = get_logger(__name__)

def prepare_model_features(
    expression_df: pd.DataFrame,
    phenotype_df: pd.DataFrame,
    label_df: pd.DataFrame,
    gene_list: List[str],
    covariates: List[str] = ['Age', 'Sex', 'Tissue']
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Prepare features for the logistic regression model.
    Encodes categorical variables and scales numeric features.
    Returns X (features), y (target), and feature names.
    """
    # Merge data sources
    df = label_df.merge(phenotype_df, left_on='sample_id', right_index=True)
    df = df.merge(expression_df, left_on='sample_id', right_index=True)

    # Filter to core genes and covariates
    feature_cols = [g for g in gene_list if g in df.columns]
    if not feature_cols:
        raise ValueError("No gene expression columns found in the merged dataframe.")

    # Prepare target
    y = df['MetS_Status'].astype(int)  # Assuming 1 for MetS, 0 for Control

    # Prepare X
    X = df[feature_cols + covariates].copy()

    # Identify categorical and numeric columns
    categorical_cols = [col for col in covariates if X[col].dtype == 'object']
    numeric_cols = [col for col in covariates if X[col].dtype in ['int64', 'float64']] + feature_cols

    # Handle missing values in covariates (drop rows if necessary, or impute if strategy defined)
    # For strict ATP-III and power analysis, we usually drop rows with missing covariates
    initial_count = len(X)
    X = X.dropna(subset=categorical_cols + numeric_cols)
    y = y.loc[X.index]
    dropped = initial_count - len(X)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} samples due to missing covariate data.")

    # Preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_cols),
            ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), categorical_cols)
        ]
    )

    X_processed = preprocessor.fit_transform(X)

    # Get feature names after transformation
    feature_names = list(numeric_cols)
    if categorical_cols:
        ohe = preprocessor.named_transformers_['cat']
        cat_feature_names = []
        for i, col in enumerate(categorical_cols):
            categories = ohe.categories_[i]
            # Drop first category as per drop='first'
            for cat in categories[1:]:
                cat_feature_names.append(f"{col}_{cat}")
        feature_names.extend(cat_feature_names)

    return pd.DataFrame(X_processed, columns=feature_names), y, feature_names

def train_logistic_regression(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42
) -> Any:
    """
    Train a logistic regression model using statsmodels for interpretability.
    Returns the fitted model and the design matrix (with intercept).
    """
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Add constant for intercept
    X_train_const = sm.add_constant(X_train)

    # Fit GLM with Binomial family
    model = GLM(y_train, X_train_const, family=Binomial())
    result = model.fit()

    logger.info(f"Model trained. AIC: {result.aic:.4f}, BIC: {result.bic:.4f}")

    return result, X_train_const

def run_cross_validation(
    X: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, float]:
    """
    Perform k-fold cross-validation and calculate mean AUC with 95% CI.
    """
    from sklearn.model_selection import StratifiedKFold
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from scipy.stats import sem

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    auc_scores = []

    for train_idx, test_idx in skf.split(X, y):
        X_tr, X_te = X.iloc[train_idx], X.iloc[test_idx]
        y_tr, y_te = y.iloc[train_idx], y.iloc[test_idx]

        # Simple Logistic Regression for CV speed
        clf = LogisticRegression(max_iter=1000)
        clf.fit(X_tr, y_tr)
        
        y_pred_prob = clf.predict_proba(X_te)[:, 1]
        auc = roc_auc_score(y_te, y_pred_prob)
        auc_scores.append(auc)

    mean_auc = np.mean(auc_scores)
    std_auc = np.std(auc_scores)
    # 95% CI approximation
    ci_95 = 1.96 * (std_auc / np.sqrt(n_splits))

    logger.info(f"CV AUC: {mean_auc:.4f} (95% CI: {mean_auc - ci_95:.4f} - {mean_auc + ci_95:.4f})")

    return {
        "mean_auc": mean_auc,
        "std_auc": std_auc,
        "ci_95_lower": mean_auc - ci_95,
        "ci_95_upper": mean_auc + ci_95
    }

def extract_odds_ratios(
    model_result: Any,
    feature_names: List[str],
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Compute Odds Ratios (OR), Standard Errors (SE), and p-values for predictors.
    Uses the statsmodels GLM result object.
    
    Args:
        model_result: Fitted GLM result from statsmodels.
        feature_names: List of feature names (including 'const' if intercept is present).
        alpha: Significance level.
    
    Returns:
        DataFrame with columns: ['Feature', 'Odds_Ratio', 'SE', 'P_value', 'CI_lower', 'CI_upper']
    """
    import statsmodels.api as sm
    
    # Ensure we have the params, bse, and pvalues from the model
    # model_result.params: coefficients (log-odds)
    # model_result.bse: standard errors of coefficients
    # model_result.pvalues: p-values
    
    params = model_result.params
    bse = model_result.bse
    pvalues = model_result.pvalues
    
    # Calculate Odds Ratios
    odds_ratios = np.exp(params)
    
    # Calculate Confidence Intervals for OR
    # CI for log-odds: beta +/- z * SE
    # z for 95% CI is approx 1.96
    z_score = stats.norm.ppf(1 - alpha/2)
    lower_log = params - z_score * bse
    upper_log = params + z_score * bse
    
    ci_lower = np.exp(lower_log)
    ci_upper = np.exp(upper_log)
    
    # Create DataFrame
    results_df = pd.DataFrame({
        'Feature': feature_names,
        'Odds_Ratio': odds_ratios,
        'SE': bse,
        'P_value': pvalues,
        'CI_lower': ci_lower,
        'CI_upper': ci_upper
    })
    
    # Sort by p-value
    results_df = results_df.sort_values(by='P_value')
    
    # Log significant findings
    significant = results_df[results_df['P_value'] < alpha]
    if not significant.empty:
        logger.info(f"Found {len(significant)} significant predictors (p < {alpha}):")
        for _, row in significant.iterrows():
            logger.info(f"  {row['Feature']}: OR={row['Odds_Ratio']:.3f} (95% CI: {row['CI_lower']:.3f}-{row['CI_upper']:.3f}, p={row['P_value']:.4f})")
    else:
        logger.warning(f"No significant predictors found at alpha={alpha}.")
    
    return results_df

def check_collinearity(
    X: pd.DataFrame,
    threshold: float = 5.0
) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    Flags features with VIF > threshold.
    
    Args:
        X: Feature DataFrame (numeric, no target).
        threshold: VIF threshold for flagging collinearity.
    
    Returns:
        DataFrame with columns: ['Feature', 'VIF', 'Flag']
    """
    # Add constant for intercept calculation (VIF usually calculated on predictors only, but statsmodels needs design matrix)
    # VIF is typically calculated on the predictors matrix X (with constant if intercept included, but constant VIF is undefined/infinite)
    # We calculate VIF on the predictors without the intercept column for the matrix, but the function signature implies X is the feature matrix.
    
    # Ensure X has no NaNs
    if X.isnull().any().any():
        logger.warning("NaNs detected in feature matrix for VIF calculation. Dropping rows.")
        X = X.dropna()
    
    # Add constant to calculate VIF correctly for the model context
    X_with_const = sm.add_constant(X)
    
    vif_data = []
    for i, col in enumerate(X_with_const.columns):
        if col == 'const':
            continue # Skip intercept
        try:
            vif = variance_inflation_factor(X_with_const.values, i)
            flag = "High Collinearity" if vif > threshold else "OK"
            vif_data.append({'Feature': col, 'VIF': vif, 'Flag': flag})
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
    
    vif_df = pd.DataFrame(vif_data)
    
    high_vif = vif_df[vif_df['VIF'] > threshold]
    if not high_vif.empty:
        logger.warning(f"Detected {len(high_vif)} features with VIF > {threshold}:")
        logger.warning(high_vif.to_string(index=False))
    
    return vif_df

def plot_roc_curve(
    y_true: pd.Series,
    y_pred_prob: np.ndarray,
    output_path: str
) -> None:
    """
    Generate and save an ROC curve plot.
    """
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve, auc
    
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_prob)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc="lower right")
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"ROC curve saved to {output_path}")

def generate_heatmap(
    expression_df: pd.DataFrame,
    labels: pd.Series,
    gene_list: List[str],
    output_path: str
) -> None:
    """
    Generate a heatmap of gene expression patterns across MetS/Control groups.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Filter genes
    X = expression_df[gene_list]
    
    # Add group labels as a column for annotation
    X['Group'] = labels.map({0: 'Control', 1: 'MetS'})
    
    # Pivot for heatmap (Samples x Genes) or (Genes x Samples)
    # Usually Genes x Samples is better for clustering genes
    # But for simple group comparison, we might want mean expression per group
    # Let's do a heatmap of mean expression per group per gene
    
    mean_expr = X.groupby('Group')[gene_list].mean().T
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(mean_expr, annot=True, fmt=".2f", cmap='YlGnBu', cbar_kws={'label': 'TPM'})
    plt.title('Mean Gene Expression by MetS Status')
    plt.xlabel('Group')
    plt.ylabel('Gene')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Heatmap saved to {output_path}")

# Re-import sm inside functions to avoid global import issues if not used, 
# but statsmodels is required for GLM and VIF.
import statsmodels.api as sm