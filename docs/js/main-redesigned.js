// Main JavaScript for redesigned llmXive site

// Global state
let currentSection = 'papers-completed';
let allData = {
    backlog: [],
    designs: [],
    plans: [],
    papersInProgress: [],
    papersCompleted: [],
    contributors: []
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    console.log('Initializing redesigned llmXive app...');
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    loadAllData();
    
    // Show default section
    showSection('papers-completed');
}

function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', (e) => {
            const section = e.currentTarget.getAttribute('onclick').match(/'([^']+)'/)[1];
            showSection(section);
        });
    });
    
    // Search inputs
    setupSearchListeners();
    
    // Filter dropdowns
    setupFilterListeners();
    
    // Submit form
    setupSubmitForm();
}

function setupSearchListeners() {
    const searchInputs = [
        'backlogSearchInput',
        'designsSearchInput', 
        'plansSearchInput',
        'papersInProgressSearchInput',
        'papersCompletedSearchInput'
    ];
    
    searchInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('input', (e) => {
                const section = inputId.replace('SearchInput', '').replace('papersInProgress', 'papers-in-progress').replace('papersCompleted', 'papers-completed');
                filterSection(section, e.target.value);
            });
        }
    });
}

function setupFilterListeners() {
    const filterSelects = [
        'backlogStatusFilter',
        'backlogSortSelect',
        'designsSortSelect',
        'plansSortSelect', 
        'papersInProgressSortSelect',
        'papersCompletedSortSelect'
    ];
    
    filterSelects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.addEventListener('change', (e) => {
                const section = selectId.replace(/Sort|Status|Filter/g, '').replace('Select', '').replace('backlog', 'backlog').replace('designs', 'designs').replace('plans', 'plans').replace('papersInProgress', 'papers-in-progress').replace('papersCompleted', 'papers-completed');
                applySorting(section);
            });
        }
    });
}

function setupSubmitForm() {
    const submitForm = document.getElementById('submitForm');
    if (submitForm) {
        submitForm.addEventListener('submit', handleIdeaSubmission);
    }
}

// Section management
function showSection(sectionName) {
    console.log('Showing section:', sectionName);
    
    // Update current section
    currentSection = sectionName;
    
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show target section
    const targetSection = document.getElementById(sectionName);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    const activeButton = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    // Load section data if needed
    loadSectionData(sectionName);
}

// Data loading
async function loadAllData() {
    console.log('Loading all data...');
    
    try {
        // Load different types of data in parallel
        await Promise.all([
            loadBacklogData(),
            loadDesignsData(),
            loadPlansData(),
            loadPapersData(),
            loadContributorsData()
        ]);
        
        console.log('All data loaded successfully');
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

async function loadSectionData(sectionName) {
    switch (sectionName) {
        case 'backlog':
            await loadBacklogData();
            renderBacklog();
            break;
        case 'designs':
            await loadDesignsData();
            renderDesigns();
            break;
        case 'plans':
            await loadPlansData();
            renderPlans();
            break;
        case 'papers-in-progress':
            await loadPapersData();
            renderPapersInProgress();
            break;
        case 'papers-completed':
            await loadPapersData();
            renderPapersCompleted();
            break;
        case 'contributors':
            await loadContributorsData();
            renderContributors();
            break;
    }
}

async function loadBacklogData() {
    try {
        // Load from GitHub API using existing working method
        const issues = await window.api.fetchProjectIssues();
        allData.backlog = issues.filter(issue => {
            const status = issue.projectStatus || 'Backlog';
            return status !== 'Done';
        });
        
        console.log(`Loaded ${allData.backlog.length} backlog items`);
    } catch (error) {
        console.error('Error loading backlog:', error);
        allData.backlog = [];
    }
}

async function loadDesignsData() {
    try {
        // TODO: Implement proper technical designs loading
        // For now, return empty array to prevent errors
        allData.designs = [];
        
        console.log(`Loaded ${allData.designs.length} technical designs`);
    } catch (error) {
        console.error('Error loading designs:', error);
        allData.designs = [];
    }
}

async function loadPlansData() {
    try {
        // TODO: Implement proper implementation plans loading
        // For now, return empty array to prevent errors
        allData.plans = [];
        
        console.log(`Loaded ${allData.plans.length} implementation plans`);
    } catch (error) {
        console.error('Error loading plans:', error);
        allData.plans = [];
    }
}

async function loadPapersData() {
    try {
        // TODO: Implement proper papers loading
        // For now, return empty arrays to prevent errors
        allData.papersInProgress = [];
        allData.papersCompleted = [];
        
        console.log(`Loaded ${allData.papersInProgress.length} in-progress papers, ${allData.papersCompleted.length} completed papers`);
    } catch (error) {
        console.error('Error loading papers:', error);
        allData.papersInProgress = [];
        allData.papersCompleted = [];
    }
}

async function loadContributorsData() {
    try {
        // TODO: Implement proper contributors loading
        // For now, return empty array to prevent errors
        allData.contributors = [];
        
        console.log(`Loaded ${allData.contributors.length} contributors`);
    } catch (error) {
        console.error('Error loading contributors:', error);
        allData.contributors = [];
    }
}

// Rendering functions
function renderBacklog() {
    const grid = document.getElementById('backlogGrid');
    if (!grid) return;
    
    if (allData.backlog.length === 0) {
        grid.innerHTML = createEmptyState('No backlog items found', 'lightbulb');
        return;
    }
    
    const html = allData.backlog.map(item => createBacklogCard(item)).join('');
    grid.innerHTML = html;
}

function renderDesigns() {
    const grid = document.getElementById('designsGrid');
    if (!grid) return;
    
    if (allData.designs.length === 0) {
        grid.innerHTML = createEmptyState('No technical designs found', 'drafting-compass');
        return;
    }
    
    const html = allData.designs.map(item => createDesignCard(item)).join('');
    grid.innerHTML = html;
}

function renderPlans() {
    const grid = document.getElementById('plansGrid');
    if (!grid) return;
    
    if (allData.plans.length === 0) {
        grid.innerHTML = createEmptyState('No implementation plans found', 'project-diagram');
        return;
    }
    
    const html = allData.plans.map(item => createPlanCard(item)).join('');
    grid.innerHTML = html;
}

function renderPapersInProgress() {
    const grid = document.getElementById('papersInProgressGrid');
    if (!grid) return;
    
    if (allData.papersInProgress.length === 0) {
        grid.innerHTML = createEmptyState('No papers in progress', 'file-alt');
        return;
    }
    
    const html = allData.papersInProgress.map(item => createPaperCard(item)).join('');
    grid.innerHTML = html;
}

function renderPapersCompleted() {
    const grid = document.getElementById('papersCompletedGrid');
    if (!grid) return;
    
    if (allData.papersCompleted.length === 0) {
        grid.innerHTML = createEmptyState('No completed papers found', 'trophy');
        return;
    }
    
    const html = allData.papersCompleted.map(item => createPaperCard(item)).join('');
    grid.innerHTML = html;
}

function renderContributors() {
    // This will be handled by contributors.js
    if (window.contributorsModule) {
        window.contributorsModule.render(allData.contributors);
    }
}

// Card creation functions
function createBacklogCard(item) {
    const status = item.projectStatus || 'Backlog';
    const statusClass = status.toLowerCase().replace(' ', '-');
    
    return `
        <div class="card" onclick="openIssueModal(${item.number})">
            <div class="card-header">
                <h3 class="card-title">${escapeHtml(item.title)}</h3>
                <div class="card-status ${statusClass}">${status}</div>
            </div>
            <div class="card-meta">
                <span><i class="fas fa-calendar"></i> ${formatDate(item.created_at)}</span>
                <span><i class="fas fa-comments"></i> ${item.comments || 0}</span>
                <span><i class="fas fa-thumbs-up"></i> ${item.votes?.up || 0}</span>
            </div>
            <div class="card-description">
                ${escapeHtml(item.body || 'No description provided').substring(0, 200)}...
            </div>
            <div class="card-footer">
                <div class="card-author">
                    <img src="${item.user.avatar_url}" alt="${item.user.login}" class="meta-avatar">
                    ${item.user.login}
                </div>
                <div class="card-links">
                    <a href="${item.html_url}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-external-link-alt"></i> GitHub
                    </a>
                </div>
            </div>
        </div>
    `;
}

function createDesignCard(item) {
    return `
        <div class="card" onclick="openDesignModal('${item.id}')">
            <div class="card-header">
                <h3 class="card-title">${escapeHtml(item.title)}</h3>
                <div class="card-status ${item.status.toLowerCase()}">${item.status}</div>
            </div>
            <div class="card-meta">
                <span><i class="fas fa-calendar"></i> ${formatDate(item.date)}</span>
                <span><i class="fas fa-user"></i> ${item.author}</span>
            </div>
            <div class="card-description">
                ${escapeHtml(item.description || 'Technical design document').substring(0, 200)}...
            </div>
            <div class="card-footer">
                <div class="card-author">
                    <i class="fas fa-drafting-compass"></i>
                    ${item.author}
                </div>
                <div class="card-links">
                    <a href="${item.issueUrl}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-link"></i> Issue
                    </a>
                    <a href="${item.designUrl}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-file-alt"></i> Design
                    </a>
                </div>
            </div>
        </div>
    `;
}

function createPlanCard(item) {
    return `
        <div class="card" onclick="openPlanModal('${item.id}')">
            <div class="card-header">
                <h3 class="card-title">${escapeHtml(item.title)}</h3>
                <div class="card-status ${item.status.toLowerCase()}">${item.status}</div>
            </div>
            <div class="card-meta">
                <span><i class="fas fa-calendar"></i> ${formatDate(item.date)}</span>
                <span><i class="fas fa-user"></i> ${item.author}</span>
            </div>
            <div class="card-description">
                ${escapeHtml(item.description || 'Implementation plan document').substring(0, 200)}...
            </div>
            <div class="card-footer">
                <div class="card-author">
                    <i class="fas fa-project-diagram"></i>
                    ${item.author}
                </div>
                <div class="card-links">
                    <a href="${item.issueUrl}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-link"></i> Issue
                    </a>
                    <a href="${item.planUrl}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-file-alt"></i> Plan
                    </a>
                </div>
            </div>
        </div>
    `;
}

function createPaperCard(item) {
    return `
        <div class="card" onclick="openPaperModal('${item.id}')">
            <div class="card-header">
                <h3 class="card-title">${escapeHtml(item.title)}</h3>
                <div class="card-status ${item.status.toLowerCase().replace(' ', '-')}">${item.status}</div>
            </div>
            <div class="card-meta">
                <span><i class="fas fa-calendar"></i> ${formatDate(item.date)}</span>
                <span><i class="fas fa-users"></i> ${item.contributors.length} contributors</span>
            </div>
            <div class="card-description">
                ${escapeHtml(item.abstract || item.description || 'Research paper').substring(0, 200)}...
            </div>
            <div class="card-footer">
                <div class="card-author">
                    <i class="fas fa-file-alt"></i>
                    ${item.contributors.slice(0, 2).join(', ')}${item.contributors.length > 2 ? '...' : ''}
                </div>
                <div class="card-links">
                    ${item.paperUrl ? `<a href="${item.paperUrl}" class="card-link" onclick="event.stopPropagation();"><i class="fas fa-file-pdf"></i> Paper</a>` : ''}
                    ${item.codeUrl ? `<a href="${item.codeUrl}" class="card-link" onclick="event.stopPropagation();"><i class="fas fa-code"></i> Code</a>` : ''}
                    ${item.dataUrl ? `<a href="${item.dataUrl}" class="card-link" onclick="event.stopPropagation();"><i class="fas fa-database"></i> Data</a>` : ''}
                </div>
            </div>
        </div>
    `;
}

// Utility functions
function createEmptyState(message, icon) {
    return `
        <div class="empty-state">
            <i class="fas fa-${icon}"></i>
            <h3>Nothing Here Yet</h3>
            <p>${message}</p>
        </div>
    `;
}


function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Modal functions (placeholders)
function openIssueModal(issueNumber) {
    console.log('Opening issue modal for:', issueNumber);
    // Will be implemented by document-viewer.js
}

function openDesignModal(designId) {
    console.log('Opening design modal for:', designId);
    // Will be implemented by document-viewer.js
}

function openPlanModal(planId) {
    console.log('Opening plan modal for:', planId);
    // Will be implemented by document-viewer.js
}

function openPaperModal(paperId) {
    console.log('Opening paper modal for:', paperId);
    // Will be implemented by document-viewer.js
}

// Submit form handling
async function handleIdeaSubmission(event) {
    event.preventDefault();
    
    const title = document.getElementById('ideaTitle').value;
    const description = document.getElementById('ideaDescription').value;
    const keywords = document.getElementById('ideaKeywords').value;
    
    try {
        console.log('Submitting idea:', { title, description, keywords });
        
        // Submit via GitHub API
        const result = await githubAPI.createIssue({
            title,
            body: `**Description**: ${description}\n\n**Keywords**: ${keywords}\n\n---\n*Submitted via llmXive web interface*`,
            labels: ['backlog', 'idea', 'Score: 0']
        });
        
        if (result) {
            alert('Idea submitted successfully!');
            closeSubmitModal();
            document.getElementById('submitForm').reset();
            
            // Refresh backlog
            await loadBacklogData();
            if (currentSection === 'backlog') {
                renderBacklog();
            }
        }
        
    } catch (error) {
        console.error('Error submitting idea:', error);
        alert('Error submitting idea. Please try again.');
    }
}

// Modal management
function closeSubmitModal() {
    const modal = document.getElementById('submitModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function closeDocumentModal() {
    const modal = document.getElementById('documentModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Filtering and sorting
function filterSection(section, searchTerm) {
    console.log(`Filtering ${section} with term: ${searchTerm}`);
    // Implementation depends on current rendering
    // This would filter the currently displayed cards
}

function applySorting(section) {
    console.log(`Applying sorting to ${section}`);
    // Implementation depends on current data and sort selection
}

// Export for other modules
window.mainApp = {
    showSection,
    loadSectionData,
    currentSection,
    allData
};