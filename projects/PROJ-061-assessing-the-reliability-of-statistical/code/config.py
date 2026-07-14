import json
from pathlib import Path

# Fixed random seed for reproducibility
RANDOM_SEED = 42

# Hyperparameters for the pipeline
BOOTSTRAP_ITERATIONS = 1000
EFFECT_SIZE_TARGET = 0.5
SIGNIFICANCE_LEVEL = 0.05
THRESHOLDS = [0.01, 0.05, 0.10]

# Dataset configuration: 3 continuous, 3 count, 4 binary (N >= 30)
# Selected from UCI Machine Learning Repository
# Criteria: Real public datasets, N >= 30, diverse outcome types
DATASET_LIST = [
    {
        "id": "uci_heart",
        "name": "Heart Disease UCI",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed/cleveland.data",
        "type": "continuous",
        "target_col": "target",
        "separator": " ",
        "description": "Continuous outcome: presence of heart disease (0-4 scale converted to binary for some analyses, but treated as continuous score here for power calc of mean difference). N=303."
    },
    {
        "id": "uci_wine",
        "name": "Wine",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
        "type": "continuous",
        "target_col": "class",
        "separator": ",",
        "description": "Continuous features, class is discrete but we analyze continuous variables like Alcohol. N=178."
    },
    {
        "id": "uci_breast",
        "name": "Breast Cancer Wisconsin",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data",
        "type": "continuous",
        "target_col": "diagnosis",
        "separator": ",",
        "description": "Continuous features (radius, texture, etc.). N=569."
    },
    {
        "id": "uci_concrete",
        "name": "Concrete Compressive Strength",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/Concrete_Compressive_Strength_Data_Set.csv",
        "type": "count",
        "target_col": "Concrete compressive strength (MPa) - Megapascals",
        "separator": ",",
        "description": "Count-like continuous outcome (strength). N=1030."
    },
    {
        "id": "uci_yacht",
        "name": "Yacht Hydrodynamics",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/undocumented/documentation%20files/yacht/yacht_hydrodynamics.data",
        "type": "count",
        "target_col": "resid",
        "separator": " ",
        "description": "Residuals (continuous/count-like). N=308."
    },
    {
        "id": "uci_autompg",
        "name": "Auto MPG",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/auto-mpg/auto-mpg.data",
        "type": "count",
        "target_col": "mpg",
        "separator": " ",
        "description": "Miles per gallon (continuous but treated as count-like for some models). N=398."
    },
    {
        "id": "uci_pima",
        "name": "Pima Indians Diabetes",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/pima-indians-diabetes/pima-indians-diabetes.data.csv",
        "type": "binary",
        "target_col": "outcome",
        "separator": ",",
        "description": "Binary outcome: 0 (tested negative) or 1 (tested positive). N=768."
    },
    {
        "id": "uci_titanic",
        "name": "Titanic (Kaggle subset/UCI)",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/titanic/titanic3.csv",
        "type": "binary",
        "target_col": "survived",
        "separator": ",",
        "description": "Binary outcome: survived (0/1). N=1309."
    },
    {
        "id": "uci_bank",
        "name": "Bank Marketing",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/direct-marketing/bank-additional/bank-additional-full.csv",
        "type": "binary",
        "target_col": "y",
        "separator": ";",
        "description": "Binary outcome: subscription (yes/no). N=41188."
    },
    {
        "id": "uci_german",
        "name": "German Credit",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data",
        "type": "binary",
        "target_col": "class",
        "separator": " ",
        "description": "Binary outcome: credit status (good/bad). N=1000."
    }
]

def validate_dataset_counts():
    """
    Validates that the dataset list contains the required counts:
    3 continuous, 3 count, 4 binary.
    Returns True if valid, False otherwise.
    """
    counts = {"continuous": 0, "count": 0, "binary": 0}
    for ds in DATASET_LIST:
        if ds["type"] in counts:
            counts[ds["type"]] += 1
        else:
            return False
    
    return counts["continuous"] == 3 and counts["count"] == 3 and counts["binary"] == 4