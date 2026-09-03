import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats

def load_interim_dataset(filepath):
    """Loads a dataset from an interim file."""
    try:
        df = pd.read_csv(filepath)
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        raise

def filter_low_variance_metabolites(df, variance_threshold=0.001):
    """Filters metabolites with variance below a threshold."""
    variance = df.var()
    metabolites_to_keep = variance[variance > variance_threshold].index
    df_filtered = df[metabolites_to_keep]
    return df_filtered

def apply_knn_imputation(df, k=5):
    """Applies k-Nearest Neighbors imputation for missing values."""
    from sklearn.impute import KNNImputer
    imputer = KNNImputer(n_neighbors=k)
    df_imputed = df.copy()
    df_imputed = pd.DataFrame(imputer.fit_transform(df_imputed), columns=df_imputed.columns)
    df_imputed['imputation_flag'] = 0  # Flag for imputed values
    return df_imputed

def apply_pca_if_needed(df, n_components=None):
    """Applies PCA if the number of features exceeds the number of samples."""
    if df.shape[1] > df.shape[0]:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=n_components)
        pca_result = pca.fit_transform(df)
        pca_df = pd.DataFrame(pca_result)
        return pca_df
    else:
        return df

def genotype_stratified_split(df, train_size=0.8):
    """Splits the data into training and testing sets, stratified by genotype."""
    # Assuming 'genotype_id' is the column for genotype
    from sklearn.model_selection import train_test_split
    train_df, test_df = train_test_split(df, train_size=train_size, random_state=42, stratify=df['genotype_id'])
    return train_df, test_df

def save_split_indices(train_indices, test_indices, filepath):
    """Saves the train and test indices to a file."""
    data = {'train': train_indices.tolist(), 'test': test_indices.tolist()}
    with open(filepath, 'w') as f:
        json.dump(data, f)

def save_pca_reduced_data(df, filepath):
    """Saves the PCA-reduced data to a file."""
    df.to_csv(filepath, index=False)
    
def main():
    # Example usage (for testing)
    # Load the interim dataset
    try:
        df = load_interim_dataset('data/interim/harmonized.csv')
    except FileNotFoundError:
        print("Error: harmonized.csv not found.  Ensure T015 has run.")
        return

    # Filter low variance metabolites
    df_filtered = filter_low_variance_metabolites(df)

    # Apply KNN imputation
    df_imputed = apply_knn_imputation(df_filtered)

    # Apply PCA if needed
    df_pca = apply_pca_if_needed(df_imputed)

    # Save PCA reduced data
    save_pca_reduced_data(df_pca, 'data/processed/pca_reduced.csv')

    print("Preprocessing completed and PCA reduced data saved to data/processed/pca_reduced.csv")
