"""
Streamlit Survey Application for Visual Aesthetics and Credibility Study.
Implements US0 (Consent) and US1 (Data Collection, Randomization, Ratings).
"""
import os
import csv
import uuid
import hashlib
import json
import time
import streamlit as st
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.survey.constants import METADATA_SCHEMA, LATIN_SQUARE_SEQUENCES
from code.survey.metadata import extract_metadata
from code.survey.randomization import select_sequence, get_sequences_for_stimuli
from code.utils.helpers import (
    get_project_root,
    get_submissions_csv_path,
    hash_ip,
    generate_user_id,
    write_atomic,
    get_irb_protocol_id,
    ensure_data_dirs
)
from code.utils.checksums import verify_stimuli_integrity
from code.utils.stimuli_hash import load_stored_hashes, compute_stimuli_hashes, save_stimuli_hashes

# --- Configuration ---
SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', 30))
ABANDONMENT_LOG_PATH = get_project_root() / "data" / "processed" / "abandonment_log.csv"

# --- Session State Management ---

def init_session_state():
    """Initialize session state variables if they don't exist."""
    if 'participant_id' not in st.session_state:
        st.session_state.participant_id = str(uuid.uuid4())
    if 'start_time' not in st.session_state:
        st.session_state.start_time = datetime.now(timezone.utc).isoformat()
    if 'last_activity_time' not in st.session_state:
        st.session_state.last_activity_time = time.time()
    if 'consent_given' not in st.session_state:
        st.session_state.consent_given = False
    if 'stimuli_order' not in st.session_state:
        # Will be set after consent
        st.session_state.stimuli_order = []
    if 'current_stimulus_index' not in st.session_state:
        st.session_state.current_stimulus_index = 0
    if 'ratings' not in st.session_state:
        st.session_state.ratings = {}
    if 'session_ended' not in st.session_state:
        st.session_state.session_ended = False

def update_activity():
    """Update the last activity timestamp."""
    st.session_state.last_activity_time = time.time()

def check_session_timeout():
    """
    Check if the session has timed out due to inactivity.
    Returns True if timed out, False otherwise.
    If timed out, clears session state and logs abandonment.
    """
    current_time = time.time()
    last_activity = st.session_state.get('last_activity_time', current_time)
    
    if current_time - last_activity > (SESSION_TIMEOUT_MINUTES * 60):
        # Session timed out
        participant_id = st.session_state.get('participant_id', 'unknown')
        
        # Log abandonment BEFORE clearing state
        log_abandonment(participant_id)
        
        # Clear session state (resetting the user to a fresh state or stopping them)
        # We keep participant_id if we want to track the abandoned session, 
        # but clear ratings and progress.
        keys_to_clear = [
            'consent_given', 'stimuli_order', 'current_stimulus_index', 
            'ratings', 'session_ended'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Reset indices
        st.session_state.current_stimulus_index = 0
        st.session_state.ratings = {}
        st.session_state.consent_given = False
        
        # Update last activity to now to prevent immediate re-trigger if page refreshes
        st.session_state.last_activity_time = current_time
        
        return True
    
    return False

def log_abandonment(participant_id=None):
    """
    Log an abandoned session to data/processed/abandonment_log.csv.
    Schema: participant_id, timestamp, reason, IRB_PROTOCOL_ID
    """
    if participant_id is None:
        participant_id = st.session_state.get('participant_id', 'unknown')
    
    timestamp = datetime.now(timezone.utc).isoformat()
    reason = 'session_timeout'
    irb_protocol_id = get_irb_protocol_id()
    
    # Ensure directory exists
    ensure_data_dirs()
    
    file_path = ABANDONMENT_LOG_PATH
    fieldnames = ['participant_id', 'timestamp', 'reason', 'IRB_PROTOCOL_ID']
    
    file_exists = os.path.exists(file_path)
    
    with open(file_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'participant_id': participant_id,
            'timestamp': timestamp,
            'reason': reason,
            'IRB_PROTOCOL_ID': irb_protocol_id
        })

# --- UI Components ---

def render_consent_modal():
    """Display the IRB-approved consent form."""
    st.title("Informed Consent")
    st.markdown("### Participation in Visual Aesthetics and Credibility Study")
    
    # Load IRB text
    try:
        from code.utils.config import load_consent_text
        consent_text = load_consent_text()
    except Exception as e:
        st.error(f"Error loading consent text: {e}")
        st.stop()
    
    st.info(consent_text)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("I Agree", key="consent_agree"):
            st.session_state.consent_given = True
            # Initialize stimuli order upon consent
            stimuli_files = ['professional.html', 'minimalist.html', 'low_quality.html', 'neutral.html']
            st.session_state.stimuli_order = select_sequence(stimuli_files)
            st.rerun()
    
    with col2:
        if st.button("I Do Not Agree", key="consent_disagree"):
            # Redirect to withdrawal page
            st.switch_page("code/survey/withdrawal.py")

def render_stimulus(stimulus_file_path):
    """Render the HTML stimulus."""
    if not os.path.exists(stimulus_file_path):
        st.error(f"Stimulus file not found: {stimulus_file_path}")
        st.stop()
    
    with open(stimulus_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    st.markdown(html_content, unsafe_allow_html=True)

def render_rating_form(stimulus_name, stimulus_index):
    """Render Likert scale inputs for Credibility and Professionalism."""
    st.subheader(f"Stimulus {stimulus_index + 1}: {stimulus_name.replace('.html', '').title()}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        credibility = st.radio(
            "Rate Credibility (1=Very Low, 7=Very High)",
            options=[1, 2, 3, 4, 5, 6, 7],
            key=f"cred_{stimulus_name}",
            horizontal=True
        )
    
    with col2:
        professionalism = st.radio(
            "Rate Professionalism (1=Very Low, 7=Very High)",
            options=[1, 2, 3, 4, 5, 6, 7],
            key=f"prof_{stimulus_name}",
            horizontal=True
        )
    
    return credibility, professionalism

def submit_survey_data():
    """Collect all ratings and demographic metadata, then save to CSV."""
    # Verify all stimuli rated
    stimuli_files = ['professional.html', 'minimalist.html', 'low_quality.html', 'neutral.html']
    required_keys = [f"cred_{s}" for s in stimuli_files] + [f"prof_{s}" for s in stimuli_files]
    
    if not all(k in st.session_state for k in required_keys):
        st.warning("Please rate all stimuli before submitting.")
        return False
    
    # Extract metadata
    metadata = extract_metadata(st.session_state.participant_id)
    
    # Compile row
    row = {
        'participant_id': st.session_state.participant_id,
        'age': metadata['age'],
        'education': metadata['education'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'hashed_ip': metadata['hashed_ip'],
        'browser_version': metadata['browser_version'],
        'session_start_time': metadata['session_start_time'],
        'stimulus_id': ','.join([s.replace('.html', '') for s in st.session_state.stimuli_order]),
        'credibility_rating': ','.join([str(st.session_state[f"cred_{s}"]) for s in stimuli_files]),
        'professionalism_rating': ','.join([str(st.session_state[f"prof_{s}"]) for s in stimuli_files])
    }
    
    # Write atomically
    try:
        write_atomic(get_submissions_csv_path(), row, fieldnames=METADATA_SCHEMA.keys())
        st.success("Survey submitted successfully! Thank you for your participation.")
        st.session_state.session_ended = True
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

# --- Main Logic ---

def main():
    """Main entry point for the Streamlit app."""
    init_session_state()
    
    # Update activity on every render
    update_activity()
    
    # Check for timeout
    if check_session_timeout():
        st.warning("Your session has timed out due to inactivity. Please start over.")
        st.stop()
    
    # Render Consent if not given
    if not st.session_state.consent_given:
        render_consent_modal()
        return
    
    # Verify Stimulus Integrity
    # (Assuming T070 has run and populated state/stimuli_hashes.json)
    # If hashes mismatch, halt.
    try:
        verify_stimuli_integrity()
    except Exception as e:
        st.error(f"Stimulus integrity check failed: {e}")
        st.stop()
    
    # Render Stimuli Loop
    stimuli_order = st.session_state.stimuli_order
    current_idx = st.session_state.current_stimulus_index
    
    if current_idx < len(stimuli_order):
        current_stimulus = stimuli_order[current_idx]
        stimulus_path = get_project_root() / "code" / "stimuli" / current_stimulus
        
        render_stimulus(str(stimulus_path))
        
        cred, prof = render_rating_form(current_stimulus, current_idx)
        
        if st.button("Next Stimulus", key="btn_next"):
            st.session_state.ratings[current_stimulus] = {'cred': cred, 'prof': prof}
            st.session_state.current_stimulus_index += 1
            st.rerun()
    else:
        # All stimuli rated
        st.header("Submit Survey")
        st.write("Please review your responses and submit.")
        
        # Display summary (optional)
        for i, stim in enumerate(stimuli_order):
            st.write(f"{stim}: Credibility {st.session_state.ratings[stim]['cred']}, Professionalism {st.session_state.ratings[stim]['prof']}")
        
        if st.button("Submit Survey", key="btn_submit"):
            if submit_survey_data():
                st.rerun()

if __name__ == "__main__":
    main()
