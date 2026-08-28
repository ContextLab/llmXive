"""
LMM Runner: Linear Mixed-Effects Model analysis.
"""
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def run_lmm_analysis(data: pd.DataFrame, formula: str = "coherence ~ param + (1|time_step)") -> Dict[str, Any]:
    """
    Run LMM analysis on the provided data.
    """
    try:
        model = smf.mixedlm(formula, data, groups=data["time_step"])
        result = model.fit()
        return {
            "summary": str(result.summary()),
            "params": result.params.to_dict(),
            "converged": result.converged
        }
    except Exception as e:
        logger.error(f"LMM analysis failed: {e}")
        return {"error": str(e), "converged": False}
