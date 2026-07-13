import os
import sys
import json
import time
import warnings
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
import joblib
from utils.logger import get_logger
from utils.io import load_csv, save_json, ensure_dir
from utils.stats import calculate_correlation_matrix, calculate_feature_variance, filter_low_variance_features
from config import get_config

logger = get_logger(__name__)

# Configuration
CONFIG = get_config()
RANDOM_SEED = CONFIG.get('random_seed', 42)
DATA_DIR = Path('data/processed')
OUTPUT_DIR = Path('data/processed')

# Ensure output directory exists
ensure_dir(OUTPUT_DIR)

def define_decline_label(df, score_col='MMSE', decline_threshold=3):
    """
    Define the decline label based on the drop in cognitive scores.
    Label 1: Decline (drop >= threshold), Label 0: Stable.
    """
    logger.info(f"Defining decline label with threshold: {decline_threshold}")
    
    # Ensure we have both timepoints
    if 'timepoint_1' not in df.columns or 'timepoint_2' not in df.columns:
        # Try to infer from existing columns if names differ
        score_cols = [c for c in df.columns if score_col.lower() in c.lower()]
        if len(score_cols) >= 2:
            t1_col, t2_col = score_cols[0], score_cols[1]
            logger.info(f"Using columns {t1_col} and {t2_col} for decline calculation")
        else:
            raise ValueError(f"Could not find two timepoint columns for {score_col}")
    else:
        t1_col, t2_col = 'timepoint_1', 'timepoint_2'
    
    # Calculate drop
    df['score_drop'] = df[t1_col] - df[t2_col]
    df['decline_label'] = (df['score_drop'] >= decline_threshold).astype(int)
    
    logger.info(f"Decline distribution: {df['decline_label'].value_counts().to_dict()}")
    return df

def collinearity_filter(X, threshold=0.95):
    """
    Remove features with correlation > threshold, keeping the one with higher variance.
    """
    logger.info("Performing collinearity check...")
    corr_matrix = calculate_correlation_matrix(X)
    features = X.columns
    to_drop = set()
    
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            f1, f2 = features[i], features[j]
            if f1 in to_drop or f2 in to_drop:
                continue
            corr_val = abs(corr_matrix.loc[f1, f2])
            if corr_val > threshold:
                # Keep the one with higher variance
                var1 = X[f1].var()
                var2 = X[f2].var()
                if var1 > var2:
                    to_drop.add(f2)
                    logger.debug(f"Dropping {f2} (corr={corr_val:.2f}, var={var2:.2f}) in favor of {f1}")
                else:
                    to_drop.add(f1)
                    logger.debug(f"Dropping {f1} (corr={corr_val:.2f}, var={var1:.2f}) in favor of {f2}")
    
    final_features = [f for f in features if f not in to_drop]
    logger.info(f"Collinearity filter: {len(features)} -> {len(final_features)} features")
    return X[final_features]

def inner_cv_pipeline(X, y, params):
    """
    Inner CV pipeline: Collinearity filter -> Variance Threshold -> RFE -> RF
    """
    # 1. Collinearity filter
    X_filtered = collinearity_filter(X, threshold=0.95)
    
    # 2. Variance Threshold
    vt = VarianceThreshold(threshold=0.01)
    X_vt = vt.fit_transform(X_filtered)
    feature_names = X_filtered.columns[vt.get_support()]
    
    # 3. RFE to select <= 20 features
    rf_base = RandomForestClassifier(
        n_estimators=params['n_estimators'],
        max_depth=params['max_depth'],
        random_state=RANDOM_SEED,
        n_jobs=1
    )
    rfe = RFE(estimator=rf_base, n_features_to_select=min(20, X_vt.shape[1]), step=1)
    X_rfe = rfe.fit_transform(X_vt, y)
    selected_features = feature_names[rfe.support_]
    
    # 4. Final RF fit
    rf_final = RandomForestClassifier(
        n_estimators=params['n_estimators'],
        max_depth=params['max_depth'],
        random_state=RANDOM_SEED,
        n_jobs=1
    )
    rf_final.fit(X_rfe, y)
    
    return rf_final, selected_features

def train_and_evaluate_nested_cv(X, y):
    """
    Perform Nested Cross-Validation:
    Outer: 5-fold StratifiedKFold
    Inner: GridSearchCV with Collinearity/Variance/RFE pipeline
    """
    logger.info("Starting Nested Cross-Validation...")
    
    # Define the grid
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, None]
    }
    
    # Ensure FR-003 compliance: n_estimators=100, max_depth=None must be in grid
    assert {'n_estimators': 100, 'max_depth': None} in [
        {**p} for p in [dict(zip(param_grid.keys(), v)) for v in 
                        zip(param_grid['n_estimators'], param_grid['max_depth'])]
    ] or any(p['n_estimators']==100 and p['max_depth']==None for p in 
             [{'n_estimators': ne, 'max_depth': md} for ne in param_grid['n_estimators'] for md in param_grid['max_depth']])
    
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    
    cv_results = []
    all_selected_features = []
    
    start_time = time.time()
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        logger.info(f"Processing Outer Fold {fold_idx + 1}/5")
        
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Inner CV: Grid Search with the pipeline logic
        # We use a custom scoring function that runs the full pipeline
        def custom_scorer(estimator, X_inner, y_inner):
            # estimator is the RF, but we need to re-run the pipeline inside
            # Since GridSearchCV expects a pipeline, we simulate the pipeline logic here
            # by creating a wrapper or using a custom CV splitter that applies the steps.
            # However, for strict control, we will manually run the inner loop.
            pass 
        
        # Manual Inner Grid Search to ensure the specific pipeline (Collinearity -> VT -> RFE -> RF) is applied
        best_score = -1
        best_params = None
        
        for n_est in param_grid['n_estimators']:
            for max_d in param_grid['max_depth']:
                params = {'n_estimators': n_est, 'max_depth': max_d}
                # Use cross_val_score on the pipeline logic
                # We need a scorer that runs the pipeline
                scores = []
                for inner_train, inner_val in StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED).split(X_train, y_train):
                    X_it, X_iv = X_train.iloc[inner_train], X_train.iloc[inner_val]
                    y_it, y_iv = y_train.iloc[inner_train], y_train.iloc[inner_val]
                    
                    model, _ = inner_cv_pipeline(X_it, y_it, params)
                    # Predict on validation
                    # Note: RFE transforms features, so we must apply the same transformation to X_iv
                    # This is tricky because RFE is fitted on X_it. We need to re-run the pipeline logic
                    # to get the transformed X_iv.
                    # Re-run pipeline to get transformation
                    X_it_filt = collinearity_filter(X_it, threshold=0.95)
                    vt = VarianceThreshold(threshold=0.01)
                    X_it_vt = vt.fit_transform(X_it_filt)
                    feat_names = X_it_filt.columns[vt.get_support()]
                    
                    rf_base = RandomForestClassifier(n_estimators=n_est, max_depth=max_d, random_state=RANDOM_SEED, n_jobs=1)
                    rfe = RFE(estimator=rf_base, n_features_to_select=min(20, X_it_vt.shape[1]), step=1)
                    X_it_rfe = rfe.fit_transform(X_it_vt, y_it)
                    
                    # Transform X_iv
                    X_iv_filt = collinearity_filter(X_iv, threshold=0.95)
                    X_iv_vt = vt.transform(X_iv_filt)
                    X_iv_rfe = rfe.transform(X_iv_vt)
                    
                    model.fit(X_it_rfe, y_it)
                    preds = model.predict(X_iv_rfe)
                    # Use AUC for scoring
                    try:
                        auc = roc_auc_score(y_iv, model.predict_proba(X_iv_rfe)[:, 1])
                        scores.append(auc)
                    except:
                        scores.append(0.5)
                
                mean_score = np.mean(scores)
                if mean_score > best_score:
                    best_score = mean_score
                    best_params = params
        
        logger.info(f"Best Inner Params for Fold {fold_idx + 1}: {best_params} (Score: {best_score:.3f})")
        
        # Train final model on full train set with best params
        final_model, selected_feats = inner_cv_pipeline(X_train, y_train, best_params)
        all_selected_features.append(selected_feats)
        
        # Evaluate on test set
        # Need to transform X_test using the same pipeline
        X_test_filt = collinearity_filter(X_test, threshold=0.95)
        # Re-fit VT and RFE on X_train features to apply to X_test? 
        # No, the pipeline fitted on X_train. We need to re-run the full pipeline on X_train to get the transformers
        # to apply to X_test.
        X_train_filt = collinearity_filter(X_train, threshold=0.95)
        vt = VarianceThreshold(threshold=0.01)
        X_train_vt = vt.fit_transform(X_train_filt)
        feat_names = X_train_filt.columns[vt.get_support()]
        
        rf_base = RandomForestClassifier(n_estimators=best_params['n_estimators'], max_depth=best_params['max_depth'], random_state=RANDOM_SEED, n_jobs=1)
        rfe = RFE(estimator=rf_base, n_features_to_select=min(20, X_train_vt.shape[1]), step=1)
        X_train_rfe = rfe.fit_transform(X_train_vt, y_train)
        
        X_test_vt = vt.transform(X_test_filt)
        X_test_rfe = rfe.transform(X_test_vt)
        
        final_model.fit(X_train_rfe, y_train)
        y_pred = final_model.predict(X_test_rfe)
        y_proba = final_model.predict_proba(X_test_rfe)[:, 1]
        
        fold_auc = roc_auc_score(y_test, y_proba)
        fold_acc = accuracy_score(y_test, y_pred)
        fold_f1 = f1_score(y_test, y_pred)
        
        logger.info(f"Fold {fold_idx + 1} Results: AUC={fold_auc:.3f}, Acc={fold_acc:.3f}, F1={fold_f1:.3f}")
        
        cv_results.append({
            'fold': fold_idx + 1,
            'auc': fold_auc,
            'accuracy': fold_acc,
            'f1': fold_f1,
            'best_params': best_params,
            'selected_features': selected_feats.tolist()
        })
    
    elapsed = time.time() - start_time
    logger.info(f"Nested CV completed in {elapsed:.1f}s")
    
    # Aggregate results
    mean_auc = np.mean([r['auc'] for r in cv_results])
    std_auc = np.std([r['auc'] for r in cv_results])
    
    result_summary = {
        'mean_auc': mean_auc,
        'std_auc': std_auc,
        'cv_results': cv_results,
        'final_params': cv_results[0]['best_params'], # Use first fold's best as representative or aggregate
        'runtime_seconds': elapsed
    }
    
    return result_summary, final_model

def main():
    logger.info("Starting T023: Train Model with Nested CV")
    
    # Load data
    metrics_path = DATA_DIR / 'graph_metrics.csv'
    labels_path = DATA_DIR / 'eligible_subjects.csv'
    
    if not metrics_path.exists():
        logger.error(f"Metrics file not found: {metrics_path}")
        sys.exit(1)
    if not labels_path.exists():
        logger.error(f"Labels file not found: {labels_path}")
        sys.exit(1)
    
    df_metrics = load_csv(metrics_path)
    df_labels = load_csv(labels_path)
    
    # Merge
    df = pd.merge(df_metrics, df_labels, on='subject_id', how='inner')
    logger.info(f"Merged dataset shape: {df.shape}")
    
    # Define decline label
    df = define_decline_label(df)
    
    # Prepare X and y
    feature_cols = [c for c in df.columns if c not in ['subject_id', 'decline_label', 'score_drop', 'timepoint_1', 'timepoint_2']]
    X = df[feature_cols]
    y = df['decline_label']
    
    if y.sum() == 0 or y.sum() == len(y):
        logger.error("Imbalanced labels: Cannot train classifier.")
        sys.exit(1)
    
    # Train
    results, model = train_and_evaluate_nested_cv(X, y)
    
    # Save results
    output_path = OUTPUT_DIR / 'cv_results.json'
    save_json(results, output_path)
    logger.info(f"Saved CV results to {output_path}")
    
    # Save model
    model_path = OUTPUT_DIR / 'model.pkl'
    joblib.dump(model, model_path)
    logger.info(f"Saved model to {model_path}")
    
    # Log FR-003 compliance
    final_params = results['final_params']
    logger.info(f"Final Selected Parameters: {final_params}")
    if final_params['n_estimators'] == 100 and final_params['max_depth'] is None:
        logger.info("FR-003 Compliance: VERIFIED (n_estimators=100, max_depth=None)")
    else:
        logger.warning(f"FR-003 Compliance: NOT MET (Got {final_params})")
        
    logger.info("T023 Completed Successfully")

if __name__ == '__main__':
    main()