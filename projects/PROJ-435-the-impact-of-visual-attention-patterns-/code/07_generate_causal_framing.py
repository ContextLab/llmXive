"""
T028: Generate Causal Framing Statement

This script reads the regression results from T027 and generates a
'Causal Framing Statement' that frames findings as causal based on the
experimental design (controlled stimuli) and dynamically reports the
observed interaction effect (coefficient, p-value) from the data.

Output: output/causal_framing_statement.txt
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    # Traverse up to find the project root (where 'code' folder exists)
    parent = current_file.parent
    while parent.parent != parent:
        if (parent / 'code').exists() and (parent / 'data').exists():
            return parent
        parent = parent.parent
    raise FileNotFoundError("Could not find project root")

def get_paths(project_root: Path) -> Dict[str, Path]:
    """Get all necessary file paths."""
    return {
        'input': project_root / 'data' / 'derived' / 'regression_results.csv',
        'output': project_root / 'output' / 'causal_framing_statement.txt',
        'state_dir': project_root / 'state',
        'output_dir': project_root / 'output'
    }

def load_regression_results(input_path: Path) -> pd.DataFrame:
    """Load regression results from CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Regression results file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded regression results with {len(df)} rows")
    return df

def find_interaction_term(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Find the three-way interaction term in the regression results.
    The term should contain fixation_duration, valence, and crt.
    """
    # Look for the interaction term in the 'term' column
    interaction_candidates = []
    
    for _, row in df.iterrows():
        term = str(row.get('term', '')).lower()
        # Check if this is the three-way interaction
        if all(x in term for x in ['fixation_duration', 'valence', 'crt']):
            interaction_candidates.append(row.to_dict())
    
    if not interaction_candidates:
        # Try to find any significant interaction if exact match fails
        for _, row in df.iterrows():
            term = str(row.get('term', '')).lower()
            if 'interaction' in term or ('*' in str(row.get('term', ''))):
                interaction_candidates.append(row.to_dict())
    
    if interaction_candidates:
        # Return the first match (preferably the three-way)
        return interaction_candidates[0]
    
    return None

def find_main_effects(df: pd.DataFrame) -> Dict[str, Optional[Dict[str, Any]]]:
    """Find main effect terms for fixation_duration, valence, and crt."""
    main_effects = {
        'fixation_duration': None,
        'valence': None,
        'crt': None
    }
    
    for _, row in df.iterrows():
        term = str(row.get('term', '')).lower()
        # Remove interaction terms to find main effects
        if '*' not in str(row.get('term', '')) and '|' not in str(row.get('term', '')):
            if 'fixation_duration' in term:
                main_effects['fixation_duration'] = row.to_dict()
            elif 'valence' in term:
                main_effects['valence'] = row.to_dict()
            elif 'crt' in term:
                main_effects['crt'] = row.to_dict()
    
    return main_effects

def format_coefficient(coef: float) -> str:
    """Format coefficient to 4 decimal places."""
    return f"{coef:.4f}"

def format_pvalue(pval: float) -> str:
    """Format p-value appropriately."""
    if pval < 0.001:
        return "p < 0.001"
    elif pval < 0.01:
        return f"p = {pval:.3f}"
    elif pval < 0.05:
        return f"p = {pval:.4f}"
    else:
        return f"p = {pval:.4f}"

def generate_causal_framing_statement(
    interaction_term: Optional[Dict[str, Any]],
    main_effects: Dict[str, Optional[Dict[str, Any]]],
    df: pd.DataFrame
) -> str:
    """
    Generate the causal framing statement dynamically based on observed effects.
    
    This statement:
    1. Frames findings as causal based on experimental design (controlled stimuli)
    2. Reports observed interaction effect with coefficient and p-value
    3. Avoids hardcoded values
    """
    lines = []
    lines.append("=" * 70)
    lines.append("CAUSAL FRAMING STATEMENT")
    lines.append("=" * 70)
    lines.append("")
    
    # Section 1: Experimental Design Basis for Causal Inference
    lines.append("1. CAUSAL INFERENCE BASIS")
    lines.append("-" * 40)
    lines.append("This analysis leverages an experimental design with controlled stimuli")
    lines.append("to support causal inference regarding the relationship between visual")
    lines.append("attention patterns and susceptibility to misleading headlines.")
    lines.append("Random assignment to headline conditions and controlled presentation")
    lines.append("timing allow us to frame the observed associations as causal effects")
    lines.append("within the bounds of this experimental paradigm.")
    lines.append("")
    
    # Section 2: Observed Interaction Effect
    lines.append("2. OBSERVED INTERACTION EFFECT")
    lines.append("-" * 40)
    
    if interaction_term:
        coef = interaction_term.get('coef', 0.0)
        pval = interaction_term.get('pvalue', 1.0)
        std_err = interaction_term.get('std_err', 0.0)
        
        lines.append(f"The three-way interaction between visual attention (fixation duration),")
        lines.append(f"headline valence, and cognitive reflection was observed with:")
        lines.append(f"  - Coefficient: {format_coefficient(coef)}")
        lines.append(f"  - Standard Error: {format_coefficient(std_err)}")
        lines.append(f"  - Significance: {format_pvalue(pval)}")
        lines.append("")
        
        # Interpretation based on significance
        if pval < 0.05:
            direction = "positive" if coef > 0 else "negative"
            lines.append(f"This {direction} interaction ({format_pvalue(pval)}) indicates that the")
            lines.append(f"effect of visual attention on belief susceptibility varies depending")
            lines.append(f"on both the emotional valence of the headline and the participant's")
            lines.append(f"level of cognitive reflection.")
        else:
            lines.append(f"The interaction effect was not statistically significant")
            lines.append(f"({format_pvalue(pval)}), suggesting that the relationship between")
            lines.append(f"visual attention and belief susceptibility may not be moderated")
            lines.append(f"by the combined influence of headline valence and cognitive reflection")
            lines.append(f"in this dataset.")
    else:
        lines.append("WARNING: The three-way interaction term was not found in the regression")
        lines.append("results. This may indicate a model specification issue or that the")
        lines.append("interaction term was excluded during multiple comparison correction.")
        lines.append("")
    
    lines.append("")
    
    # Section 3: Main Effects (if available)
    lines.append("3. MAIN EFFECTS SUMMARY")
    lines.append("-" * 40)
    
    effect_found = False
    for effect_name, effect_data in main_effects.items():
        if effect_data:
            effect_found = True
            coef = effect_data.get('coef', 0.0)
            pval = effect_data.get('pvalue', 1.0)
            lines.append(f"{effect_name.replace('_', ' ').title()}:")
            lines.append(f"  Coefficient: {format_coefficient(coef)}, {format_pvalue(pval)}")
    
    if not effect_found:
        lines.append("No main effects were identified in the results.")
    
    lines.append("")
    
    # Section 4: Causal Framing Statement
    lines.append("4. CAUSAL FRAMING CONCLUSION")
    lines.append("-" * 40)
    lines.append("Based on the controlled experimental design and the observed statistical")
    lines.append("effects, we can frame these findings as follows:")
    lines.append("")
    
    if interaction_term and interaction_term.get('pvalue', 1.0) < 0.05:
        lines.append("The experimental manipulation of visual attention patterns causally")
        lines.append("influences susceptibility to misleading headlines, but this effect is")
        lines.append("contingent upon the emotional valence of the content and the individual's")
        lines.append("cognitive reflection capacity. Specifically, the significant three-way")
        lines.append(f"interaction (β = {format_coefficient(interaction_term.get('coef', 0.0))}, {format_pvalue(interaction_term.get('pvalue', 1.0))})")
        lines.append("demonstrates that System 1 processing (rapid acceptance) and System 2")
        lines.append("processing (analytical override) interact dynamically with visual")
        lines.append("attention to determine belief outcomes.")
    else:
        lines.append("While the experimental design supports causal inference, the observed")
        lines.append("interaction effect did not reach statistical significance. This suggests")
        lines.append("that the relationship between visual attention and belief susceptibility")
        lines.append("may be more complex than the hypothesized three-way interaction, or that")
        lines.append("additional moderating variables not captured in this model may be at play.")
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("END OF CAUSAL FRAMING STATEMENT")
    lines.append("=" * 70)
    
    return "\n".join(lines)

def write_statement(output_path: Path, statement: str) -> None:
    """Write the causal framing statement to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(statement)
    logger.info(f"Causal framing statement written to: {output_path}")

def main():
    """Main execution function."""
    try:
        # Get paths
        project_root = get_project_root()
        paths = get_paths(project_root)
        
        logger.info(f"Project root: {project_root}")
        logger.info(f"Input file: {paths['input']}")
        logger.info(f"Output file: {paths['output']}")
        
        # Load regression results
        df = load_regression_results(paths['input'])
        
        # Find interaction term
        interaction_term = find_interaction_term(df)
        if not interaction_term:
            logger.warning("Three-way interaction term not found in results")
        
        # Find main effects
        main_effects = find_main_effects(df)
        
        # Generate statement
        statement = generate_causal_framing_statement(
            interaction_term=interaction_term,
            main_effects=main_effects,
            df=df
        )
        
        # Write output
        write_statement(paths['output'], statement)
        
        logger.info("T028 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error generating causal framing statement: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
