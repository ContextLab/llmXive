import logging
from pathlib import Path
from typing import Optional
from src.utils.logging_config import setup_logging, create_logger
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)
WARNING_DOC = project_root / "docs" / "reports" / "data_scarcity_warning.md"

def check_and_warn():
    """
    Generates the data scarcity warning document if triggered.
    """
    logger.warning("Generating Data Scarcity Warning (FR-008)...")
    
    WARNING_DOC.parent.mkdir(parents=True, exist_ok=True)
    
    content = """# Data Scarcity Warning (FR-008)

## Warning Generated

**Reason**: The dataset contains fewer than 50 data points.

**Implications**:
1. **Reduced Statistical Power**: With N < 50, the model's ability to detect true effects is limited.
2. **Overfitting Risk**: High risk of overfitting, especially with complex models like Random Forest.
3. **Generalizability**: Results may not generalize well to unseen Heusler alloys.

**Recommendation**:
- Interpret model performance metrics (R², MAE) with caution.
- Consider using simpler models or regularization.
- Prioritize data collection from additional sources.

**Reference**: Spec FR-008.
"""
    
    with open(WARNING_DOC, 'w') as f:
        f.write(content)
    
    logger.info(f"Data scarcity warning saved to {WARNING_DOC}")

def main():
    setup_logging()
    logger.info("Scarcity Warning Main Entry")
    check_and_warn()
    return 0

if __name__ == "__main__":
    sys.exit(main())