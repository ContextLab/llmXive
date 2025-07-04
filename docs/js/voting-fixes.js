// Voting System Fixes

window.votingFixes = {
    // Track voting state properly
    votingState: new Map(),
    
    // Apply fixes to the voting system
    applyFixes(boardUI, githubAuth) {
        // Override the vote method in BoardUI
        const originalVote = boardUI.vote.bind(boardUI);
        
        boardUI.vote = async function(issueNumber, reaction) {
            const voteKey = `${issueNumber}-${reaction}`;
            const oppositeKey = `${issueNumber}-${reaction === '+1' ? '-1' : '+1'}`;
            
            // Check if we're already processing this vote
            if (window.votingFixes.votingState.get(voteKey) === 'processing') {
                return;
            }
            
            // Mark as processing
            window.votingFixes.votingState.set(voteKey, 'processing');
            
            // Disable both vote buttons and add visual feedback
            const upButton = document.getElementById(`vote-up-${issueNumber}`);
            const downButton = document.getElementById(`vote-down-${issueNumber}`);
            const modalUpButton = document.getElementById(`modal-vote-up-${issueNumber}`);
            const modalDownButton = document.getElementById(`modal-vote-down-${issueNumber}`);
            
            const allButtons = [upButton, downButton, modalUpButton, modalDownButton].filter(b => b);
            
            // Add loading state
            allButtons.forEach(btn => {
                btn.disabled = true;
                btn.classList.add('voting');
            });
            
            try {
                const result = await window.votingFixes.enhancedVote(issueNumber, reaction, githubAuth);
                
                if (result.success) {
                    // Update the UI immediately without visual glitches
                    const project = this.projects.find(p => p.number === issueNumber);
                    if (project) {
                        // Initialize userReactions if needed
                        if (!project.userReactions) {
                            project.userReactions = { up: false, down: false };
                        }
                        
                        // Apply the changes
                        if (reaction === '+1') {
                            if (result.action === 'removed') {
                                project.votes.up = Math.max(0, project.votes.up - 1);
                                project.userReactions.up = false;
                            } else {
                                project.votes.up++;
                                project.userReactions.up = true;
                                // Handle opposite reaction
                                if (project.userReactions.down) {
                                    project.votes.down = Math.max(0, project.votes.down - 1);
                                    project.userReactions.down = false;
                                }
                            }
                        } else {
                            if (result.action === 'removed') {
                                project.votes.down = Math.max(0, project.votes.down - 1);
                                project.userReactions.down = false;
                            } else {
                                project.votes.down++;
                                project.userReactions.down = true;
                                // Handle opposite reaction
                                if (project.userReactions.up) {
                                    project.votes.up = Math.max(0, project.votes.up - 1);
                                    project.userReactions.up = false;
                                }
                            }
                        }
                        
                        // Update the buttons without re-rendering everything
                        window.votingFixes.updateVoteButtons(project);
                    }
                    
                    // Fetch fresh data after a delay
                    setTimeout(() => {
                        this.loadProjects();
                    }, 2000);
                }
            } catch (error) {
                console.error('Voting error:', error);
                boardUI.showToast('Failed to register vote. Please try again.', 'error');
            } finally {
                // Clear processing state
                window.votingFixes.votingState.delete(voteKey);
                
                // Re-enable buttons
                allButtons.forEach(btn => {
                    btn.disabled = false;
                    btn.classList.remove('voting');
                });
            }
        };
    },
    
    // Enhanced vote function with proper toggle support
    async enhancedVote(issueNumber, reaction, githubAuth) {
        if (!githubAuth.isAuthenticated()) {
            githubAuth.login();
            return { success: false };
        }
        
        try {
            // Get current user's reactions
            const currentReactions = await this.getUserReactions(issueNumber, githubAuth);
            
            // Check if user already has this reaction
            const hasReaction = reaction === '+1' ? currentReactions.up : currentReactions.down;
            const hasOpposite = reaction === '+1' ? currentReactions.down : currentReactions.up;
            
            // Remove opposite reaction first if it exists
            if (hasOpposite) {
                const oppositeType = reaction === '+1' ? '-1' : '+1';
                const oppositeId = reaction === '+1' ? currentReactions.downId : currentReactions.upId;
                
                if (oppositeId) {
                    await this.removeReaction(issueNumber, oppositeId, githubAuth);
                }
            }
            
            // Toggle the requested reaction
            let action = 'added';
            if (hasReaction) {
                // Remove it (toggle off)
                const reactionId = reaction === '+1' ? currentReactions.upId : currentReactions.downId;
                if (reactionId) {
                    await this.removeReaction(issueNumber, reactionId, githubAuth);
                    action = 'removed';
                }
            } else {
                // Add it
                await this.addReaction(issueNumber, reaction, githubAuth);
                action = 'added';
            }
            
            return { success: true, action, removedOpposite: hasOpposite };
            
        } catch (error) {
            console.error('Enhanced vote error:', error);
            return { success: false, error };
        }
    },
    
    // Get user's current reactions
    async getUserReactions(issueNumber, githubAuth) {
        const response = await fetch(
            `https://api.github.com/repos/${CONFIG.github.owner}/${CONFIG.github.repo}/issues/${issueNumber}/reactions`,
            {
                headers: {
                    ...githubAuth.getAuthHeaders(),
                    'Accept': 'application/vnd.github.squirrel-girl-preview+json'
                }
            }
        );
        
        if (!response.ok) {
            throw new Error('Failed to fetch reactions');
        }
        
        const reactions = await response.json();
        const currentUser = githubAuth.getUser();
        const userReactions = reactions.filter(r => r.user.login === currentUser.login);
        
        const result = {
            up: false,
            down: false,
            upId: null,
            downId: null
        };
        
        userReactions.forEach(r => {
            if (r.content === '+1') {
                result.up = true;
                result.upId = r.id;
            } else if (r.content === '-1') {
                result.down = true;
                result.downId = r.id;
            }
        });
        
        return result;
    },
    
    // Add a reaction
    async addReaction(issueNumber, reaction, githubAuth) {
        const response = await fetch(
            `https://api.github.com/repos/${CONFIG.github.owner}/${CONFIG.github.repo}/issues/${issueNumber}/reactions`,
            {
                method: 'POST',
                headers: {
                    ...githubAuth.getAuthHeaders(),
                    'Accept': 'application/vnd.github.squirrel-girl-preview+json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: reaction })
            }
        );
        
        if (!response.ok) {
            throw new Error('Failed to add reaction');
        }
        
        return await response.json();
    },
    
    // Remove a reaction
    async removeReaction(issueNumber, reactionId, githubAuth) {
        const response = await fetch(
            `https://api.github.com/repos/${CONFIG.github.owner}/${CONFIG.github.repo}/issues/${issueNumber}/reactions/${reactionId}`,
            {
                method: 'DELETE',
                headers: {
                    ...githubAuth.getAuthHeaders(),
                    'Accept': 'application/vnd.github.squirrel-girl-preview+json'
                }
            }
        );
        
        if (!response.ok && response.status !== 204) {
            throw new Error('Failed to remove reaction');
        }
    },
    
    // Update vote buttons without full re-render
    updateVoteButtons(project) {
        const userReacted = project.userReactions || { up: false, down: false };
        
        // Update card buttons
        const upBtn = document.getElementById(`vote-up-${project.number}`);
        const downBtn = document.getElementById(`vote-down-${project.number}`);
        
        if (upBtn) {
            upBtn.classList.toggle('active', userReacted.up);
            upBtn.innerHTML = `<i class="fas fa-thumbs-up"></i> ${project.votes.up}`;
        }
        
        if (downBtn) {
            downBtn.classList.toggle('active', userReacted.down);
            downBtn.innerHTML = `<i class="fas fa-thumbs-down"></i> ${project.votes.down}`;
        }
        
        // Update modal buttons if modal is open
        const modalUpBtn = document.getElementById(`modal-vote-up-${project.number}`);
        const modalDownBtn = document.getElementById(`modal-vote-down-${project.number}`);
        
        if (modalUpBtn) {
            modalUpBtn.classList.toggle('active', userReacted.up);
            modalUpBtn.innerHTML = `<i class="fas fa-thumbs-up"></i> ${project.votes.up}`;
        }
        
        if (modalDownBtn) {
            modalDownBtn.classList.toggle('active', userReacted.down);
            modalDownBtn.innerHTML = `<i class="fas fa-thumbs-down"></i> ${project.votes.down}`;
        }
    }
};