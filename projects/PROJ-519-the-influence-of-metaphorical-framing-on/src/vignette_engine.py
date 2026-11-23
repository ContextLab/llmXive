"""
Vignette Engine for generating metaphorically-framed experimental stimuli.

Implements FR-001: Generate three distinct vignette texts (Battle, Journey, Medical)
with constant clinical details and varying metaphors.
"""
from typing import Dict


def generate_vignettes() -> Dict[str, str]:
    """
    Generate three distinct vignette texts with different metaphorical framings.
    
    All vignettes share identical clinical details (symptoms, duration, impact)
    but use different metaphorical language to describe the experience.
    
    Returns:
        Dict[str, str]: Dictionary mapping condition names to vignette text.
                        Keys: 'battle', 'journey', 'medical'
    """
    # Core clinical details (constant across all conditions)
    clinical_base = """
    Alex has been experiencing significant emotional difficulties for the past two years. 
    During this time, Alex has reported persistent feelings of sadness, loss of interest 
    in previously enjoyed activities, and difficulty sleeping. These experiences have 
    impacted Alex's ability to maintain employment and has led to withdrawal from 
    social relationships. Alex describes feeling isolated and often experiences 
    thoughts of hopelessness about the future.
    """
    
    # Battle framing
    battle_vignette = clinical_base + """
    Alex describes this period as an ongoing battle against an overwhelming enemy. 
    Alex feels like they are constantly fighting a war within their own mind, 
    struggling against forces that seem impossible to defeat. Alex speaks of 
    needing to find the strength to soldier on, even when the enemy feels too 
    powerful. Alex views their emotional state as an adversary that must be 
    conquered through sheer will and determination.
    """
    
    # Journey framing
    journey_vignette = clinical_base + """
    Alex describes this period as a difficult journey through unfamiliar territory. 
    Alex feels like they are walking a long, winding road without a clear destination. 
    Alex speaks of taking small steps forward, even when the path seems unclear. 
    Alex views their emotional state as a traveler navigating through challenging 
    landscapes, seeking direction and hoping to eventually find their way to a 
    better place.
    """
    
    # Medical framing
    medical_vignette = clinical_base + """
    Alex describes this period as experiencing a clinical condition that requires 
    professional treatment. Alex feels like they are undergoing a diagnostic process 
    to understand their symptoms. Alex speaks of the need for therapy and medical 
    intervention to address the underlying issues. Alex views their emotional state 
    as a health condition that can be managed through proper clinical care and 
    prescribed treatment plans.
    """
    
    return {
        "battle": battle_vignette.strip(),
        "journey": journey_vignette.strip(),
        "medical": medical_vignette.strip()
    }
