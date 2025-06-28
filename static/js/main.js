// Main JavaScript file for Bookkeeping App

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize alerts auto-dismiss
    initializeAlerts();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize table row highlighting
    initializeTableHighlighting();
    
    // Initialize copy-to-clipboard functionality
    initializeCopyToClipboard();
    
    // Initialize search form enhancements
    initializeSearchEnhancements();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [title]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            placement: 'top',
            trigger: 'hover focus'
        });
    });
}

/**
 * Auto-dismiss alerts after 10 seconds
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 10000); // 10 seconds
    });
}

/**
 * Initialize form validations
 */
function initializeFormValidations() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // File input validation
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(event) {
            validateFileInput(event.target);
        });
    });
}

/**
 * Validate file input
 */
function validateFileInput(input) {
    const file = input.files[0];
    if (!file) return;
    
    const maxSize = 16 * 1024 * 1024; // 16MB
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/tiff', 'image/webp'];
    
    // Check file size
    if (file.size > maxSize) {
        showAlert('File is too large. Maximum size is 16MB.', 'danger');
        input.value = '';
        return false;
    }
    
    // Check file type
    if (!allowedTypes.includes(file.type)) {
        showAlert('Invalid file type. Please select an image file.', 'danger');
        input.value = '';
        return false;
    }
    
    return true;
}

/**
 * Initialize table row highlighting
 */
function initializeTableHighlighting() {
    const tableRows = document.querySelectorAll('table tbody tr');
    tableRows.forEach(function(row) {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(var(--bs-primary-rgb), 0.05)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
}

/**
 * Initialize copy-to-clipboard functionality
 */
function initializeCopyToClipboard() {
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            copyToClipboard(textToCopy);
        });
    });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showAlert('Copied to clipboard!', 'success');
        }).catch(function(err) {
            console.error('Could not copy text: ', err);
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

/**
 * Fallback copy to clipboard for older browsers
 */
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showAlert('Copied to clipboard!', 'success');
        } else {
            showAlert('Could not copy to clipboard.', 'warning');
        }
    } catch (err) {
        console.error('Fallback copy failed: ', err);
        showAlert('Could not copy to clipboard.', 'warning');
    }
    
    document.body.removeChild(textArea);
}

/**
 * Initialize search form enhancements
 */
function initializeSearchEnhancements() {
    const searchForm = document.querySelector('form[method="GET"]');
    if (!searchForm) return;
    
    // Add loading state to search button
    searchForm.addEventListener('submit', function() {
        const submitButton = this.querySelector('button[type="submit"]');
        if (submitButton) {
            const originalContent = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Searching...';
            submitButton.disabled = true;
            
            // Re-enable after 5 seconds (fallback)
            setTimeout(function() {
                submitButton.innerHTML = originalContent;
                submitButton.disabled = false;
            }, 5000);
        }
    });
    
    // Auto-submit on enter in search field
    const searchInput = searchForm.querySelector('input[name="query"]');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                searchForm.submit();
            }
        });
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertsContainer = document.querySelector('.container');
    if (!alertsContainer) return;
    
    const alertId = 'alert-' + Date.now();
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert" id="${alertId}">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    alertsContainer.insertAdjacentHTML('afterbegin', alertHTML);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 5000);
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

/**
 * Debounce function for search inputs
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

/**
 * Highlight search terms in text
 */
function highlightSearchTerms(text, searchTerm) {
    if (!searchTerm || !text) return text;
    
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

/**
 * Truncate text with ellipsis
 */
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Get file size in human readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate phone number format
 */
function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
}

/**
 * Get query parameter from URL
 */
function getQueryParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

/**
 * Set page title
 */
function setPageTitle(title) {
    document.title = title + ' - Bookkeeping App';
}

/**
 * Show loading spinner
 */
function showLoadingSpinner(element) {
    if (element) {
        const spinner = '<div class="spinner-border spinner-border-sm me-2" role="status"><span class="visually-hidden">Loading...</span></div>';
        element.insertAdjacentHTML('afterbegin', spinner);
    }
}

/**
 * Hide loading spinner
 */
function hideLoadingSpinner(element) {
    if (element) {
        const spinner = element.querySelector('.spinner-border');
        if (spinner) {
            spinner.remove();
        }
    }
}

/**
 * Scroll to top of page
 */
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

/**
 * Check if element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Export functions for use in other scripts
window.BookkeepingApp = {
    showAlert,
    formatCurrency,
    formatDate,
    copyToClipboard,
    truncateText,
    formatFileSize,
    isValidEmail,
    isValidPhone,
    showLoadingSpinner,
    hideLoadingSpinner,
    scrollToTop,
    isInViewport
};
