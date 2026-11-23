import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';

/**
 * ParticipantForm Component
 * 
 * Implements the frontend UI for User Story 1 (Data Collection) based on 
 * the API contract defined in T018a (contracts/api_participant.md).
 * 
 * Responsibilities:
 * 1. Manage participant session state (ID, consent, task assignment).
 * 2. Render the interactive bug localization task interface.
 * 3. Capture interaction data (timestamps, line selections) with high precision.
 * 4. Submit data to the backend endpoint defined in the API contract.
 */
const ParticipantForm = () => {
  // --- State Management ---
  const [sessionData, setSessionData] = useState({
    participantId: null,
    condition: null, // 'baseline', 'llm', 'rule'
    taskId: null,
    codeSnippet: '',
    groundTruthLine: null, // Hidden for the participant, used for logging
    startTime: null,
  });

  const [interactionLogs, setInteractionLogs] = useState([]);
  const [currentLine, setCurrentLine] = useState(null);
  const [selectedLine, setSelectedLine] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [consentGiven, setConsentGiven] = useState(false);

  // --- Constants (Derived from API Contract T018a) ---
  const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';
  const ENDPOINT_SUBMIT_INTERACTION = `${API_BASE_URL}/participant/submit`;
  const ENDPOINT_GET_TASK = `${API_BASE_URL}/participant/task`;

  // --- Initialization & Session Setup ---
  useEffect(() => {
    // Initialize session ID if not present (simulating client-side session start)
    const storedSession = localStorage.getItem('participant_session');
    if (!storedSession) {
      const newSessionId = uuidv4();
      localStorage.setItem('participant_session', newSessionId);
      setSessionData(prev => ({ ...prev, participantId: newSessionId }));
    } else {
      setSessionData(prev => ({ ...prev, participantId: storedSession }));
    }

    // Fetch initial task assignment (Latin Square logic handled by backend T018c)
    fetchInitialTask();
  }, []);

  const fetchInitialTask = async () => {
    try {
      const response = await axios.get(ENDPOINT_GET_TASK);
      if (response.data && response.data.task) {
        setSessionData(prev => ({
          ...prev,
          taskId: response.data.task.task_id,
          condition: response.data.task.condition,
          codeSnippet: response.data.task.code_snippet,
          groundTruthLine: response.data.task.ground_truth_line, // Backend provides this for logging only
          startTime: Date.now()
        }));
      }
    } catch (err) {
      console.error("Failed to fetch task assignment", err);
      setError("Could not load task. Please refresh.");
    }
  };

  // --- Interaction Handling ---
  
  /**
   * Logs a user interaction (hover, click, scroll) with millisecond precision.
   * Matches API contract: { participant_id, task_id, condition, timestamp_ms, selected_line }
   */
  const logInteraction = (lineIndex, actionType) => {
    const timestamp = Date.now();
    const logEntry = {
      participant_id: sessionData.participantId,
      task_id: sessionData.taskId,
      condition: sessionData.condition,
      timestamp_ms: timestamp,
      selected_line: lineIndex,
      action: actionType
    };

    setInteractionLogs(prev => [...prev, logEntry]);
  };

  const handleLineHover = (lineIndex) => {
    setCurrentLine(lineIndex);
    logInteraction(lineIndex, 'hover');
  };

  const handleLineClick = (lineIndex) => {
    setSelectedLine(lineIndex);
    logInteraction(lineIndex, 'select');
  };

  const handleConsent = () => {
    setConsentGiven(true);
    // In a real flow, this would trigger a consent form submission to backend
    logInteraction(0, 'consent_given');
  };

  // --- Submission Logic ---
  const handleSubmit = async () => {
    if (!selectedLine) {
      alert("Please select a line before submitting.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const finalLog = {
      participant_id: sessionData.participantId,
      task_id: sessionData.taskId,
      condition: sessionData.condition,
      timestamp_ms: Date.now(),
      selected_line: selectedLine,
      ground_truth_line: sessionData.groundTruthLine, // Included for validation if backend allows
      session_duration_ms: Date.now() - sessionData.startTime
    };

    try {
      await axios.post(ENDPOINT_SUBMIT_INTERACTION, {
        session: finalLog,
        logs: interactionLogs
      });

      alert("Submission successful!");
      // Optional: Fetch next task or show completion screen
      // fetchInitialTask(); 
    } catch (err) {
      console.error("Submission failed", err);
      setError("Failed to submit data. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- Render ---
  if (!sessionData.participantId) {
    return <div className="loading">Initializing session...</div>;
  }

  if (!consentGiven) {
    return (
      <div className="consent-container">
        <h2>Participant Consent Form</h2>
        <p>
          This study evaluates code summarization techniques for bug localization.
          Your participation involves reviewing code snippets and identifying bug locations.
          All data will be anonymized and stored securely.
        </p>
        <button onClick={handleConsent} className="btn-primary">
          I Agree to Participate
        </button>
      </div>
    );
  }

  if (!sessionData.codeSnippet) {
    return <div className="loading">Loading task...</div>;
  }

  const lines = sessionData.codeSnippet.split('\n');

  return (
    <div className="participant-form-container">
      <header className="form-header">
        <h3>Task: Bug Localization</h3>
        <span className="condition-badge">Condition: {sessionData.condition}</span>
        <span className="task-id">ID: {sessionData.taskId}</span>
      </header>

      <div className="code-viewer">
        <p className="instruction">
          Please review the code below and click on the line you believe contains the bug.
        </p>
        <div className="code-lines">
          {lines.map((line, index) => (
            <div
              key={index}
              className={`code-line ${currentLine === index ? 'hovered' : ''} ${selectedLine === index ? 'selected' : ''}`}
              onMouseEnter={() => handleLineHover(index + 1)} // 1-based indexing for display
              onClick={() => handleLineClick(index + 1)}
            >
              <span className="line-number">{index + 1}</span>
              <span className="line-content">{line}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="action-bar">
        {error && <div className="error-msg">{error}</div>}
        <button 
          onClick={handleSubmit} 
          disabled={isSubmitting || !selectedLine}
          className="btn-submit"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Selection'}
        </button>
      </div>
    </div>
  );
};

export default ParticipantForm;
