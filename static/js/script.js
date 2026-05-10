/**
 * Main JavaScript File
 * Global functionality and interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
    initializeDropdowns();
    initializeTooltips();
    setupFormValidation();
});

/**
 * Sidebar Toggle Functionality
 */
function initializeSidebar() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (!sidebarToggle || !sidebar) return;
    
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('active');
        document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : 'auto';
    });
    
    // Close sidebar when clicking outside
    document.addEventListener('click', function(event) {
        if (!sidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
            sidebar.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    });
    
    // Close sidebar on window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 992) {
            sidebar.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    });
}

/**
 * Bootstrap Dropdowns Initialization
 */
function initializeDropdowns() {
    const dropdownElements = document.querySelectorAll('.dropdown-toggle');
    dropdownElements.forEach(element => {
        new bootstrap.Dropdown(element);
    });
}

/**
 * Bootstrap Tooltips Initialization
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipElements.forEach(element => {
        new bootstrap.Tooltip(element);
    });
}

/**
 * Form Validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

/**
 * Show Toast Notification
 */
function showToast(message, type = 'info') {
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${getIconForType(type)}"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const mainContent = document.querySelector('.main-content');
    const alertDiv = document.createElement('div');
    alertDiv.innerHTML = alertHTML;
    mainContent.insertBefore(alertDiv.firstElementChild, mainContent.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = mainContent.querySelector('.alert');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Confirm Delete
 */
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

/**
 * Format Currency
 */
function formatCurrency(amount, currency = 'Rs.') {
    return currency + ' ' + parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Format Date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

/**
 * Smooth Scroll to Element
 */
function smoothScroll(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Debounce Function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Search with Debouncing
 */
const searchInput = document.querySelector('.search-box input');
if (searchInput) {
    searchInput.addEventListener('input', debounce(function(e) {
        const query = e.target.value.toLowerCase();
        // Implement search functionality here
    }, 300));
}

/**
 * Prevent Double Submit
 */
function preventDoubleSubmit(formSelector) {
    const form = document.querySelector(formSelector);
    if (form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }
        });
    }
}

/**
 * Keyboard Shortcuts
 */
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchBox = document.querySelector('.search-box input');
        if (searchBox) searchBox.focus();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        });
    }
});

/**
 * Dynamic Content Loading with AJAX
 */
async function loadContent(url, targetSelector) {
    try {
        const response = await fetch(url);
        const content = await response.text();
        document.querySelector(targetSelector).innerHTML = content;
    } catch (error) {
        console.error('Error loading content:', error);
        showToast('Error loading content. Please try again.', 'danger');
    }
}
