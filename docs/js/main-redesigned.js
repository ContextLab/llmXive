// Main JavaScript for redesigned llmXive site

// Global state
let currentSection = 'papers-completed';
let allData = {
    backlog: [],
    designs: [],
    plans: [],
    papersInProgress: [],
    papersCompleted: [],
    contributors: [],
    reviews: []
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
    
    // Submit idea button
    const submitBtn = document.querySelector('a[href="#submit"]');
    if (submitBtn) {
        submitBtn.addEventListener('click', (e) => {
            e.preventDefault();
            showSubmitModal();
        });
    }
    
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
    const filterMapping = {
        'backlogSortSelect': 'backlog',
        'designsSortSelect': 'designs',
        'plansSortSelect': 'plans',
        'papersInProgressSortSelect': 'papersInProgress',
        'papersCompletedSortSelect': 'papersCompleted'
    };
    
    Object.entries(filterMapping).forEach(([selectId, section]) => {
        const select = document.getElementById(selectId);
        if (select) {
            select.addEventListener('change', (e) => {
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
            loadReviewsData(),
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
        // Load from technical_design_documents README table
        allData.designs = await window.api.loadTechnicalDesigns();
        
        console.log(`Loaded ${allData.designs.length} technical designs`);
    } catch (error) {
        console.error('Error loading designs:', error);
        allData.designs = [];
    }
}

async function loadPlansData() {
    try {
        // Load from implementation_plans README table
        allData.plans = await window.api.loadImplementationPlans();
        
        console.log(`Loaded ${allData.plans.length} implementation plans`);
    } catch (error) {
        console.error('Error loading plans:', error);
        allData.plans = [];
    }
}

async function loadPapersData() {
    try {
        // Load from papers README tables
        const papersData = await window.api.loadPapers();
        allData.papersInProgress = papersData.inProgress;
        allData.papersCompleted = papersData.completed;
        
        console.log(`Loaded ${allData.papersInProgress.length} in-progress papers, ${allData.papersCompleted.length} completed papers`);
    } catch (error) {
        console.error('Error loading papers:', error);
        allData.papersInProgress = [];
        allData.papersCompleted = [];
    }
}

async function loadReviewsData() {
    try {
        // Load from reviews README table
        allData.reviews = await window.api.loadReviews();
        
        console.log(`Loaded ${allData.reviews.length} reviews`);
    } catch (error) {
        console.error('Error loading reviews:', error);
        allData.reviews = [];
    }
}

async function loadContributorsData() {
    try {
        // Load contributors from all README tables
        allData.contributors = await window.api.loadContributors();
        
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
        grid.innerHTML = createEmptyState('No completed papers found', 'robot');
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
                    ${item.realAuthor && item.realAuthor.type === 'ai' ? 
                        `<i class="fas fa-robot"></i>` : 
                        `<img src="${item.user.avatar_url}" alt="${item.user.login}" class="meta-avatar">`}
                    ${item.realAuthor ? item.realAuthor.name : item.user.login}
                    ${item.realAuthor && item.realAuthor.type === 'ai' ? '<span class="author-type">(AI)</span>' : ''}
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
    const title = item.title || 'Untitled Design';
    const author = item.author || 'Unknown';
    
    return `
        <div class="card" onclick="openDocumentModal('${item.id}', 'design')">
            <div class="card-header">
                <h3 class="card-title">${escapeHtml(title)}</h3>
                <div class="card-status design">Design</div>
            </div>
            <div class="card-meta">
                <span><i class="fas fa-calendar"></i> ${item.date || 'Unknown date'}</span>
                <span><i class="fas fa-user"></i> ${author}</span>
            </div>
            <div class="card-description">
                Technical design document for ${escapeHtml(title)}
            </div>
            <div class="card-footer">
                <div class="card-author">
                    <i class="fas fa-drafting-compass"></i>
                    ${author}
                </div>
                <div class="card-links">
                    ${item.issueUrl ? `<a href="${item.issueUrl}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-link"></i> Issue
                    </a>` : ''}
                    ${item.designUrl ? `<a href="${item.designUrl}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-file-alt"></i> Design
                    </a>` : ''}
                </div>
            </div>
        </div>
    `;
}

function createPlanCard(item) {
    const title = item.title || 'Untitled Plan';
    const author = item.author || 'Unknown';
    
    return `
        <div class="card" onclick="openDocumentModal('${item.id}', 'plan')">
            <div class="card-header">
                <h3 class="card-title">${escapeHtml(title)}</h3>
                <div class="card-status ready">Ready</div>
            </div>
            <div class="card-meta">
                <span><i class="fas fa-calendar"></i> ${item.date || 'Unknown date'}</span>
                <span><i class="fas fa-user"></i> ${author}</span>
            </div>
            <div class="card-description">
                Implementation plan for ${escapeHtml(title)}
            </div>
            <div class="card-footer">
                <div class="card-author">
                    <i class="fas fa-project-diagram"></i>
                    ${author}
                </div>
                <div class="card-links">
                    ${item.issueUrl ? `<a href="${item.issueUrl}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-link"></i> Issue
                    </a>` : ''}
                    ${item.planUrl ? `<a href="${item.planUrl}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-file-alt"></i> Plan
                    </a>` : ''}
                </div>
            </div>
        </div>
    `;
}

function createPaperCard(item) {
    const statusClass = item.status.toLowerCase().replace(' ', '-');
    
    return `
        <div class="card" onclick="openDocumentModal('${item.id}', 'paper')">
            <div class="card-header">
                <h3 class="card-title">${escapeHtml(item.title)}</h3>
                <div class="card-status ${statusClass}">${item.status === 'completed' ? 'Completed' : 'In Progress'}</div>
            </div>
            <div class="card-meta">
                <span><i class="fas fa-users"></i> ${item.authors.split(',').length} authors</span>
                <span><i class="fas fa-file-alt"></i> Paper</span>
            </div>
            <div class="card-description">
                Research paper: ${escapeHtml(item.title)}
            </div>
            <div class="card-footer">
                <div class="card-author">
                    <i class="fas fa-users"></i>
                    ${item.authors.split(',').slice(0, 2).join(', ')}${item.authors.split(',').length > 2 ? '...' : ''}
                </div>
                <div class="card-links">
                    ${item.paperUrl ? `<a href="${item.paperUrl}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-file-pdf"></i> Paper
                    </a>` : ''}
                    ${item.codeUrl ? `<a href="${item.codeUrl}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-code"></i> Code
                    </a>` : ''}
                    ${item.dataUrl ? `<a href="${item.dataUrl}" class="card-link" onclick="event.stopPropagation();">
                        <i class="fas fa-database"></i> Data
                    </a>` : ''}
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

// Modal functions
function openIssueModal(issueNumber) {
    console.log('Opening issue modal for:', issueNumber);
    if (window.documentViewer) {
        window.documentViewer.openDocument('issue', issueNumber);
    }
}

function openDocumentModal(documentId, documentType) {
    console.log('Opening document modal for:', documentId, documentType);
    if (window.documentViewer) {
        window.documentViewer.openDocument(documentType, documentId);
    }
}

// Submit form handling
async function handleIdeaSubmission(event) {
    event.preventDefault();
    
    const title = document.getElementById('ideaTitle').value;
    const description = document.getElementById('ideaDescription').value;
    const keywords = document.getElementById('ideaKeywords').value;
    
    try {
        console.log('Submitting idea:', { title, description, keywords });
        
        // Submit via GitHub API using the correct method
        const result = await window.api.createIssue(
            title,
            `**Description**: ${description}\n\n**Keywords**: ${keywords}\n\n---\n*Submitted via llmXive web interface*`,
            ['backlog', 'idea', 'Score: 0']
        );
        
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
function showSubmitModal() {
    const modal = document.getElementById('submitModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeSubmitModal() {
    const modal = document.getElementById('submitModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
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
    
    const sortSelect = document.getElementById(`${section}SortSelect`);
    if (!sortSelect) return;
    
    const sortBy = sortSelect.value;
    let dataArray;
    
    // Get the appropriate data array
    switch (section) {
        case 'backlog':
            dataArray = allData.backlog;
            break;
        case 'designs':
            dataArray = allData.designs;
            break;
        case 'plans':
            dataArray = allData.plans;
            break;
        case 'papersInProgress':
        case 'papers-in-progress':
            dataArray = allData.papersInProgress;
            break;
        case 'papersCompleted':
        case 'papers-completed':
            dataArray = allData.papersCompleted;
            break;
        default:
            return;
    }
    
    // Apply sorting
    const sortFunctions = {
        'updated': (a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at),
        'created': (a, b) => new Date(b.created_at) - new Date(a.created_at),
        'title': (a, b) => a.title.localeCompare(b.title),
        'upvotes': (a, b) => (b.votes?.up || 0) - (a.votes?.up || 0),
        'status': (a, b) => {
            const statusOrder = ['Backlog', 'Ready', 'In Progress', 'In Review', 'Done'];
            const aStatus = a.projectStatus || 'Backlog';
            const bStatus = b.projectStatus || 'Backlog';
            return statusOrder.indexOf(aStatus) - statusOrder.indexOf(bStatus);
        }
    };
    
    if (sortFunctions[sortBy]) {
        dataArray.sort(sortFunctions[sortBy]);
        
        // Re-render the section
        switch (section) {
            case 'backlog':
                renderBacklog();
                break;
            case 'designs':
                renderDesigns();
                break;
            case 'plans':
                renderPlans();
                break;
            case 'papersInProgress':
            case 'papers-in-progress':
                renderPapersInProgress();
                break;
            case 'papersCompleted':
            case 'papers-completed':
                renderPapersCompleted();
                break;
        }
    }
}

// Export for other modules
window.mainApp = {
    showSection,
    loadSectionData,
    currentSection,
    allData
};

// Make allData available globally for document viewer
window.allData = allData;