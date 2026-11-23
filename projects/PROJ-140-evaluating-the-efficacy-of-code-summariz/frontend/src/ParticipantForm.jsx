import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

/**
 * ParticipantForm Component
 * 
 * Implements the frontend interface for the User Story 1 data collection study.
 * Based on API contract defined in contracts/api_participant.md (T018a).
 * 
 * Features:
 * - Session initialization
 * - Task rendering (Code + Summary display)
 * - Interaction logging (line selection, timestamps)
 * - Task completion and session termination
 */

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const ParticipantForm = () => {
  // Session State
  const [sessionId, setSessionId] = useState(null);
  const [participantId, setParticipantId] = useState(null);
  const [consentVerified, setConsentVerified] = useState(false);
  
  // Task State
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0);
  const [tasks, setTasks] = useState([]);
  const [currentTask, setCurrentTask] = useState(null);
  
  // Interaction State
  const [selectedLine, setSelectedLine] = useState(null);
  const [startTime, setStartTime] = useState(null);
  const [isTaskActive, setIsTaskActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize Participant ID on mount
  useEffect(() => {
    const storedId = localStorage.getItem('participant_id');
    if (storedId) {
      setParticipantId(storedId);
    } else {
      const newId = uuidv4();
      setParticipantId(newId);
      localStorage.setItem('participant_id', newId);
    }
  }, []);

  // Initialize Session
  const initializeSession = async () => {
    if (!participantId || !consentVerified) {
      setError("Participant ID and Consent verification required.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/participant/session/init`, {
        participant_id: participantId,
        consent_verified: consentVerified
      });

      const { session_id, assigned_tasks } = response.data;
      setSessionId(session_id);
      setTasks(assigned_tasks);
      setCurrentTask(assigned_tasks[0]);
      setIsTaskActive(true);
      console.log(`Session initialized: ${session_id}`);
    } catch (err) {
      setError(`Failed to initialize session: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Handle Line Selection
  const handleLineClick = (lineNumber) => {
    if (!isTaskActive || !currentTask) return;
    
    setSelectedLine(lineNumber);
    // Auto-submit or wait for explicit submit? 
    // For study rigor, we might wait for a "Submit Selection" button, 
    // but for UX, we can auto-log on selection if desired. 
    // Here we assume explicit submit for better latency measurement control.
  };

  // Submit Interaction / Complete Task
  const submitTask = async () => {
    if (!selectedLine || !currentTask) {
      setError("Please select a line to continue.");
      return;
    }

    setLoading(true);
    setError(null);

    const endTime = Date.now();
    const latencyMs = startTime ? (endTime - startTime) : 0;

    try {
      // 1. Log Interaction
      await axios.post(`${API_BASE_URL}/api/participant/interaction`, {
        session_id: sessionId,
        task_id: currentTask.task_id,
        condition: currentTask.condition,
        timestamp_ms: endTime,
        selected_line: selectedLine,
        ground_truth_line: currentTask.ground_truth_line, // Sent for validation, stored in backend
        latency_ms: latencyMs
      });

      // 2. Mark Task Complete
      const completionResponse = await axios.post(`${API_BASE_URL}/api/participant/task/complete`, {
        session_id: sessionId,
        task_id: currentTask.task_id,
        final_selected_line: selectedLine,
        time_to_decision_ms: latencyMs
      });

      // 3. Move to next task or end session
      if (completionResponse.data.next_task_available) {
        const nextIndex = currentTaskIndex + 1;
        if (nextIndex < tasks.length) {
          setCurrentTaskIndex(nextIndex);
          setCurrentTask(tasks[nextIndex]);
          setSelectedLine(null);
          setStartTime(Date.now());
          setError(null);
        } else {
          endSession();
        }
      } else {
        endSession();
      }

    } catch (err) {
      setError(`Submission failed: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // End Session
  const endSession = async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/api/participant/session/end`, {
        session_id: sessionId,
        dropout_flag: false
      });
      alert("Thank you for participating! Session ended.");
      setSessionId(null);
      setTasks([]);
      setCurrentTask(null);
      setIsTaskActive(false);
    } catch (err) {
      console.error("Failed to end session:", err);
      alert("Session ended locally, but server sync failed.");
    } finally {
      setLoading(false);
    }
  };

  // Consent Modal
  if (!consentVerified) {
    return (
      <div style={styles.consentContainer}>
        <h2>Study Consent Form</h2>
        <p>You are invited to participate in a research study on code summarization.</p>
        <p>Your participation involves localizing bugs in provided code snippets.</p>
        <p>Data collected will be anonymized and used for research purposes only.</p>
        <div style={styles.buttonGroup}>
          <button 
            style={styles.button} 
            onClick={() => setConsentVerified(true)}
            disabled={!participantId}
          >
            I Consent
          </button>
          <button 
            style={styles.buttonSecondary} 
            onClick={() => alert("Consent required to proceed.")}
          >
            Decline
          </button>
        </div>
      </div>
    );
  }

  // Initial Load / Session Init
  if (!sessionId) {
    return (
      <div style={styles.container}>
        <h2>Study Initialization</h2>
        <p>Participant ID: {participantId}</p>
        <p>Consent Status: Verified</p>
        {loading && <p>Initializing session...</p>}
        {error && <p style={styles.error}>{error}</p>}
        <button 
          style={styles.button} 
          onClick={initializeSession}
          disabled={loading}
        >
          Start Study
        </button>
      </div>
    );
  }

  // Task Rendering
  if (currentTask && isTaskActive) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <h3>Task {currentTaskIndex + 1} of {tasks.length}</h3>
          <span style={styles.conditionBadge}>{currentTask.condition}</span>
        </div>
        
        <div style={styles.codeContainer}>
          <h4>Code Snippet (ID: {currentTask.buggy_method_id})</h4>
          <pre style={styles.codeBlock}>
            {currentTask.source_code.split('\n').map((line, idx) => (
              <div 
                key={idx} 
                style={{
                  display: 'flex', 
                  cursor: 'pointer',
                  backgroundColor: selectedLine === (idx + 1) ? '#e6f3ff' : 'transparent'
                }}
                onClick={() => handleLineClick(idx + 1)}
              >
                <span style={styles.lineNumber}>{idx + 1}</span>
                <span style={styles.lineContent}>{line}</span>
              </div>
            ))}
          </pre>
        </div>

        {currentTask.summary && (
          <div style={styles.summaryBox}>
            <h4>Summary</h4>
            <p>{currentTask.summary}</p>
          </div>
        )}

        <div style={styles.actions}>
          {error && <p style={styles.error}>{error}</p>}
          <button 
            style={styles.submitButton} 
            onClick={submitTask}
            disabled={selectedLine === null || loading}
          >
            {loading ? 'Submitting...' : 'Submit Selection'}
          </button>
        </div>
      </div>
    );
  }

  return <div>Session Ended</div>;
};

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: 'Arial, sans-serif'
  },
  consentContainer: {
    maxWidth: '600px',
    margin: '50px auto',
    padding: '30px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    backgroundColor: '#f9f9f9'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px'
  },
  conditionBadge: {
    backgroundColor: '#007bff',
    color: 'white',
    padding: '5px 10px',
    borderRadius: '4px',
    fontSize: '0.9em'
  },
  codeContainer: {
    backgroundColor: '#f4f4f4',
    padding: '15px',
    borderRadius: '5px',
    overflowX: 'auto',
    marginBottom: '20px'
  },
  codeBlock: {
    margin: 0,
    fontFamily: 'Consolas, Monaco, monospace',
    fontSize: '14px',
    lineHeight: '1.5'
  },
  lineNumber: {
    width: '30px',
    textAlign: 'right',
    paddingRight: '10px',
    color: '#888',
    userSelect: 'none'
  },
  lineContent: {
    whiteSpace: 'pre',
    userSelect: 'none'
  },
  summaryBox: {
    backgroundColor: '#eef',
    padding: '15px',
    borderRadius: '5px',
    marginBottom: '20px',
    borderLeft: '4px solid #007bff'
  },
  actions: {
    textAlign: 'center',
    marginTop: '20px'
  },
  button: {
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '16px',
    margin: '5px'
  },
  buttonSecondary: {
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '16px',
    margin: '5px'
  },
  submitButton: {
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '16px'
  },
  error: {
    color: '#dc3545',
    marginBottom: '10px'
  }
};

export default ParticipantForm;
