import os
import sys
from pathlib import Path

def create_directories():
    """Create the project directory structure as specified in T006a."""
    base_dirs = [
        "code/data_generation",
        "code/training",
        "code/evaluation",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-predict-stiffness-cnn/contracts",
    ]

    root = Path(".")
    created = []
    for d in base_dirs:
        target = root / d
        target.mkdir(parents=True, exist_ok=True)
        created.append(str(target))
    
    return created

def create_init_files():
    """Create __init__.py files as specified in T006b."""
    init_paths = [
        "code/__init__.py",
        "code/data_generation/__init__.py",
        "code/training/__init__.py",
        "code/evaluation/__init__.py",
        "code/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/contract/__init__.py",
        "tests/integration/__init__.py",
    ]

    root = Path(".")
    created = []
    for p in init_paths:
        target = root / p
        target.touch(exist_ok=True)
        created.append(str(target))
    
    return created

def create_placeholder_files():
    """Create placeholder files as specified in T006c."""
    # We create minimal valid Python stubs for .py files to satisfy "executable code" constraint
    # and empty files for others.
    placeholders = {
        "code/main.py": "import sys\nimport argparse\nfrom pathlib import Path\n\ndef main():\n    pass\n\nif __name__ == \"__main__\":\n    main()\n",
        "code/data_generation/generate_microstructures.py": "import numpy as np\nfrom skimage.draw import disk, ellipse\nfrom pathlib import Path\nimport random\n\ndef generate_microstructure(seed: int, size: int = 128):\n    pass\n\ndef save_microstructure(image, path: Path):\n    pass\n\ndef main():\n    pass\n",
        "code/data_generation/compute_stiffness.py": "import numpy as np\nfrom pathlib import Path\nimport json\nfrom code.utils.fft_homogenization import compute_effective_stiffness\n\ndef load_microstructure(path: Path):\n    pass\n\ndef compute_stiffness_tensor(image):\n    pass\n\ndef main():\n    pass\n",
        "code/training/model.py": "import torch\nimport torch.nn as nn\n\nclass StiffnessPredictorCNN(nn.Module):\n    def __init__(self):\n        super().__init__()\n        pass\n\ndef create_model():\n    return StiffnessPredictorCNN()\n",
        "code/training/train.py": "import torch\nimport torch.nn as nn\nimport torch.optim as optim\nfrom pathlib import Path\nimport json\nfrom code.training.model import create_model\n\ndef load_dataset():\n    pass\n\ndef train_model():\n    pass\n\ndef save_model(model, path):\n    pass\n\ndef main():\n    pass\n",
        "code/evaluation/stats_utils.py": "import numpy as np\nfrom scipy import stats\nfrom typing import List, Dict, Tuple\n\ndef compute_one_way_anova():\n    pass\n\ndef compute_tukey_hsd():\n    pass\n\ndef compute_degradation_rate():\n    pass\n\ndef main():\n    pass\n",
        "code/evaluation/evaluate.py": "import json\nimport numpy as np\nfrom pathlib import Path\nfrom code.evaluation.stats_utils import compute_one_way_anova, compute_degradation_rate\n\ndef load_predictions():\n    pass\n\ndef load_ground_truth():\n    pass\n\ndef compute_errors():\n    pass\n\ndef generate_report():\n    pass\n\ndef main():\n    pass\n",
        "docs/constitution_amendment_proposal.md": "# Constitution Amendment Proposal\n\nThis document proposes the necessary amendments to the project constitution.\n",
        "requirements.txt": "torch==2.0.0+cpu\nscikit-image==0.21.0\nscipy==1.11.0\nnumpy==1.24.0\npandas==2.0.0\npytest==7.3.0\nscikit-learn==1.2.0\npyfftw==0.13.1\n",
        "pyproject.toml": "[tool.black]\nline-length = 88\ntarget-version = ['py39']\n\n[tool.ruff]\nline-length = 88\ntarget-version = 'py39'\n",
    }

    root = Path(".")
    created = []
    for p, content in placeholders.items():
        target = root / p
        # Ensure parent directory exists for nested files
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(str(target))
    
    return created

def verify_structure():
    """Verify that all required directories and files exist."""
    required_dirs = [
        "code/data_generation",
        "code/training",
        "code/evaluation",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-predict-stiffness-cnn/contracts",
    ]
    required_files = [
        "code/__init__.py",
        "code/data_generation/__init__.py",
        "code/training/__init__.py",
        "code/evaluation/__init__.py",
        "code/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/contract/__init__.py",
        "tests/integration/__init__.py",
        "code/main.py",
        "code/data_generation/generate_microstructures.py",
        "code/data_generation/compute_stiffness.py",
        "code/training/model.py",
        "code/training/train.py",
        "code/evaluation/stats_utils.py",
        "code/evaluation/evaluate.py",
        "docs/constitution_amendment_proposal.md",
        "requirements.txt",
        "pyproject.toml",
    ]

    root = Path(".")
    missing_dirs = [d for d in required_dirs if not (root / d).is_dir()]
    missing_files = [f for f in required_files if not (root / f).is_file()]

    if missing_dirs or missing_files:
        errors = []
        if missing_dirs:
            errors.append(f"Missing directories: {missing_dirs}")
        if missing_files:
            errors.append(f"Missing files: {missing_files}")
        raise FileNotFoundError("; ".join(errors))
    
    return True

def main():
    print("Creating project directory structure...")
    dirs = create_directories()
    print(f"Created {len(dirs)} directories.")

    print("Creating __init__.py files...")
    inits = create_init_files()
    print(f"Created {len(inits)} __init__.py files.")

    print("Creating placeholder files...")
    files = create_placeholder_files()
    print(f"Created {len(files)} placeholder files.")

    print("Verifying structure...")
    try:
        verify_structure()
        print("Verification successful. All required artifacts exist.")
    except FileNotFoundError as e:
        print(f"Verification failed: {e}")
        sys.exit(1)

    print("Setup complete.")

if __name__ == "__main__":
    main()
