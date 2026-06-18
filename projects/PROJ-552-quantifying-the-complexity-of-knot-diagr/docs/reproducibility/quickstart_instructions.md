# Quick‑Start Reproducibility Instructions

**Python version**: The project requires **Python 3.9** or newer.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd <repo-directory>

# (Optional) Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt
```

## Run the quick‑start pipeline

The quick‑start script validates that the core pipeline runs end‑to‑end:

```bash
python -m code.reproducibility.quickstart_validator
```

This command will download the necessary data (if not already present), run the
analysis steps, and report any reproducibility issues. See the other files in
`docs/reproducibility/` for detailed explanations of each stage.

---

*If you encounter problems, ensure that your Python version matches the
requirement above and that all dependencies are successfully installed.*
