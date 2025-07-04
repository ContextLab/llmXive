// Refactored voting system for clean toggle behavior

window.votingSystemRefactor = {
    // Track voting operations in progress
    operations: new Map(),
    
    applyFix() {
        if (!window.ui || !window.githubAuth) {
            console.warn('UI or GitHub Auth not found');
            return;
        }
        
        // Replace the vote method with cleaner implementation
        window.ui.vote = async function(issueNumber, reaction) {
            const operationKey = `${issueNumber}-vote`;
            
            // Prevent concurrent operations on same issue
            if (window.votingSystemRefactor.operations.has(operationKey)) {
                return;
            }
            
            window.votingSystemRefactor.operations.set(operationKey, true);
            
            try {
                // Get all relevant buttons
                const buttons = window.votingSystemRefactor.getVoteButtons(issueNumber);
                const isUpvote = reaction === '+1';
                const clickedButtons = isUpvote ? buttons.up : buttons.down;
                const oppositeButtons = isUpvote ? buttons.down : buttons.up;
                
                // Disable all vote buttons for this issue
                [...buttons.up, ...buttons.down].forEach(btn => {
                    if (btn) {
                        btn.disabled = true;
                        btn.style.cursor = 'wait';
                    }
                });
                
                // Perform the vote
                const result = await window.votingSystemRefactor.performVote(
                    issueNumber, 
                    reaction,
                    window.ui.projects.find(p => p.number === issueNumber)
                );
                
                if (result.success) {
                    // Update the local project data
                    const project = window.ui.projects.find(p => p.number === issueNumber);
                    if (project) {
                        window.votingSystemRefactor.updateProjectVotes(project, reaction, result.action);
                        
                        // Update button states without full re-render
                        window.votingSystemRefactor.updateButtonStates(
                            buttons,
                            project.userReactions
                        );
                    }
                    
                    // Refresh data after a delay for accuracy
                    setTimeout(() => {
                        window.ui.loadProjects();
                    }, 1500);
                } else {
                    window.ui.showToast('Failed to register vote', 'error');
                }
                
            } catch (error) {
                console.error('Voting error:', error);
                window.ui.showToast('An error occurred while voting', 'error');
            } finally {
                // Re-enable buttons
                const buttons = window.votingSystemRefactor.getVoteButtons(issueNumber);
                [...buttons.up, ...buttons.down].forEach(btn => {
                    if (btn) {
                        btn.disabled = false;
                        btn.style.cursor = 'pointer';
                    }
                });
                
                window.votingSystemRefactor.operations.delete(operationKey);
            }
        };
        
        console.log('Voting system refactor applied');
    },
    
    // Get all vote buttons for an issue
    getVoteButtons(issueNumber) {
        return {
            up: [
                document.getElementById(`vote-up-${issueNumber}`),
                document.getElementById(`modal-vote-up-${issueNumber}`)
            ].filter(Boolean),
            down: [
                document.getElementById(`vote-down-${issueNumber}`),
                document.getElementById(`modal-vote-down-${issueNumber}`)
            ].filter(Boolean)
        };
    },
    
    // Perform the actual vote with clean toggle logic
    async performVote(issueNumber, reaction, project) {
        if (!window.githubAuth.isAuthenticated()) {
            window.githubAuth.login();
            return { success: false };
        }
        
        try {
            // Get current reactions for this user
            const userReactions = await this.getUserReactions(issueNumber);
            
            const isUpvote = reaction === '+1';
            const hasThisReaction = isUpvote ? userReactions.up : userReactions.down;
            const hasOppositeReaction = isUpvote ? userReactions.down : userReactions.up;
            
            // Determine what actions to take
            const actions = [];
            
            // If user has opposite reaction, remove it
            if (hasOppositeReaction) {
                const oppositeId = isUpvote ? userReactions.downId : userReactions.upId;
                actions.push({
                    type: 'remove',
                    reactionId: oppositeId,
                    reactionType: isUpvote ? '-1' : '+1'
                });
            }
            
            // Toggle the clicked reaction
            if (hasThisReaction) {
                // Remove it (toggle off)
                const reactionId = isUpvote ? userReactions.upId : userReactions.downId;
                actions.push({
                    type: 'remove',
                    reactionId: reactionId,
                    reactionType: reaction
                });
            } else {
                // Add it (toggle on)
                actions.push({
                    type: 'add',
                    reactionType: reaction
                });
            }
            
            // Execute actions
            for (const action of actions) {
                if (action.type === 'remove') {
                    await this.removeReaction(issueNumber, action.reactionId);
                } else {
                    await this.addReaction(issueNumber, action.reactionType);
                }
            }
            
            return {
                success: true,
                action: hasThisReaction ? 'removed' : 'added',
                removedOpposite: hasOppositeReaction
            };
            
        } catch (error) {
            console.error('Vote operation failed:', error);
            return { success: false, error };
        }
    },
    
    // Get user's current reactions
    async getUserReactions(issueNumber) {
        const response = await fetch(
            `https://api.github.com/repos/${CONFIG.github.owner}/${CONFIG.github.repo}/issues/${issueNumber}/reactions`,
            {
                headers: {
                    ...window.githubAuth.getAuthHeaders(),
                    'Accept': 'application/vnd.github.squirrel-girl-preview+json'
                }
            }
        );
        
        if (!response.ok) {
            throw new Error('Failed to fetch reactions');
        }
        
        const reactions = await response.json();
        const currentUser = window.githubAuth.getUser();
        const userReactions = reactions.filter(r => r.user.login === currentUser.login);
        
        return {
            up: userReactions.some(r => r.content === '+1'),
            down: userReactions.some(r => r.content === '-1'),
            upId: userReactions.find(r => r.content === '+1')?.id,
            downId: userReactions.find(r => r.content === '-1')?.id
        };
    },
    
    // Add a reaction
    async addReaction(issueNumber, reactionType) {
        const response = await fetch(
            `https://api.github.com/repos/${CONFIG.github.owner}/${CONFIG.github.repo}/issues/${issueNumber}/reactions`,
            {
                method: 'POST',
                headers: {
                    ...window.githubAuth.getAuthHeaders(),
                    'Accept': 'application/vnd.github.squirrel-girl-preview+json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: reactionType })
            }
        );
        
        if (!response.ok) {
            throw new Error('Failed to add reaction');
        }
    },
    
    // Remove a reaction
    async removeReaction(issueNumber, reactionId) {
        const response = await fetch(
            `https://api.github.com/repos/${CONFIG.github.owner}/${CONFIG.github.repo}/issues/${issueNumber}/reactions/${reactionId}`,
            {
                method: 'DELETE',
                headers: {
                    ...window.githubAuth.getAuthHeaders(),
                    'Accept': 'application/vnd.github.squirrel-girl-preview+json'
                }
            }
        );
        
        if (!response.ok && response.status !== 204) {
            throw new Error('Failed to remove reaction');
        }
    },
    
    // Update local project vote counts
    updateProjectVotes(project, reaction, action) {
        if (!project.userReactions) {
            project.userReactions = { up: false, down: false };
        }
        
        const isUpvote = reaction === '+1';
        
        // Update vote counts based on action
        if (action === 'removed') {
            // Removed the vote
            if (isUpvote) {
                project.votes.up = Math.max(0, project.votes.up - 1);
                project.userReactions.up = false;
            } else {
                project.votes.down = Math.max(0, project.votes.down - 1);
                project.userReactions.down = false;
            }
        } else {
            // Added the vote
            if (isUpvote) {
                project.votes.up++;
                project.userReactions.up = true;
                // If had opposite vote, remove it
                if (project.userReactions.down) {
                    project.votes.down = Math.max(0, project.votes.down - 1);
                    project.userReactions.down = false;
                }
            } else {
                project.votes.down++;
                project.userReactions.down = true;
                // If had opposite vote, remove it
                if (project.userReactions.up) {
                    project.votes.up = Math.max(0, project.votes.up - 1);
                    project.userReactions.up = false;
                }
            }
        }
    },
    
    // Update button states without re-rendering
    updateButtonStates(buttons, userReactions) {
        // Update up vote buttons
        buttons.up.forEach(btn => {
            if (btn) {
                btn.classList.toggle('active', userReactions.up);
                const count = btn.querySelector('.vote-count') || btn;
                const currentCount = parseInt(count.textContent.match(/\d+/)?.[0] || '0');
                count.innerHTML = `<i class="fas fa-thumbs-up"></i> ${currentCount}`;
            }
        });
        
        // Update down vote buttons
        buttons.down.forEach(btn => {
            if (btn) {
                btn.classList.toggle('active', userReactions.down);
                const count = btn.querySelector('.vote-count') || btn;
                const currentCount = parseInt(count.textContent.match(/\d+/)?.[0] || '0');
                count.innerHTML = `<i class="fas fa-thumbs-down"></i> ${currentCount}`;
            }
        });
    }
};