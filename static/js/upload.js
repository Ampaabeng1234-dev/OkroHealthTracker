// Upload functionality and UI enhancements for OkroHealthDetector

document.addEventListener('DOMContentLoaded', function() {
    // Initialize upload functionality
    initializeFileUpload();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize progress tracking
    initializeProgressTracking();
});

function initializeFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const uploadForm = document.getElementById('uploadForm');
    
    if (!fileInput) return;
    
    // File input change handler
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        if (file) {
            // Validate file size (16MB limit)
            if (file.size > 16 * 1024 * 1024) {
                showAlert('File size must be less than 16MB', 'error');
                fileInput.value = '';
                hideImagePreview();
                return;
            }
            
            // Validate file type
            if (!isValidImageType(file)) {
                showAlert('Please select a valid image file (PNG, JPG, JPEG, GIF)', 'error');
                fileInput.value = '';
                hideImagePreview();
                return;
            }
            
            // Show image preview
            showImagePreview(file);
            
            // Check if this is from camera capture
            const isCameraCapture = file.name && file.name.includes('okra_leaf_');
            if (isCameraCapture) {
                // Add camera capture indicator
                addCameraCaptureIndicator();
            }
            
            // Auto-submit after preview (optional)
            if (document.getElementById('autoSubmit') && document.getElementById('autoSubmit').checked) {
                setTimeout(() => {
                    uploadForm.submit();
                }, 1000);
            }
        } else {
            hideImagePreview();
        }
    });
    
    // Form submission handler
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                return false;
            }
            
            showLoadingState();
        });
    }
    
    // Drag and drop functionality
    initializeDragAndDrop();
}

function showImagePreview(file) {
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    
    if (!imagePreview || !previewImg) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImg.src = e.target.result;
        imagePreview.style.display = 'block';
        
        // Add fade-in animation
        imagePreview.style.opacity = '0';
        setTimeout(() => {
            imagePreview.style.transition = 'opacity 0.3s ease-in-out';
            imagePreview.style.opacity = '1';
        }, 10);
        
        // Update file info
        updateFileInfo(file);
    };
    reader.readAsDataURL(file);
}

function hideImagePreview() {
    const imagePreview = document.getElementById('imagePreview');
    if (imagePreview) {
        imagePreview.style.display = 'none';
    }
    
    clearFileInfo();
}

function updateFileInfo(file) {
    // Create or update file info display
    let fileInfo = document.getElementById('fileInfo');
    if (!fileInfo) {
        fileInfo = document.createElement('div');
        fileInfo.id = 'fileInfo';
        fileInfo.className = 'mt-2 small text-muted';
        
        const imagePreview = document.getElementById('imagePreview');
        if (imagePreview) {
            imagePreview.appendChild(fileInfo);
        }
    }
    
    const fileSizeKB = Math.round(file.size / 1024);
    const fileSizeMB = Math.round(file.size / (1024 * 1024) * 10) / 10;
    
    fileInfo.innerHTML = `
        <i class="fas fa-info-circle me-1"></i>
        <strong>${file.name}</strong> 
        (${fileSizeMB > 1 ? fileSizeMB + ' MB' : fileSizeKB + ' KB'})
    `;
}

function clearFileInfo() {
    const fileInfo = document.getElementById('fileInfo');
    if (fileInfo) {
        fileInfo.remove();
    }
}

function isValidImageType(file) {
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
    return validTypes.includes(file.type.toLowerCase());
}

function validateForm() {
    const fileInput = document.getElementById('fileInput');
    
    if (!fileInput || !fileInput.files[0]) {
        showAlert('Please select an image file first.', 'error');
        return false;
    }
    
    const file = fileInput.files[0];
    
    if (!isValidImageType(file)) {
        showAlert('Please select a valid image file.', 'error');
        return false;
    }
    
    if (file.size > 16 * 1024 * 1024) {
        showAlert('File size must be less than 16MB.', 'error');
        return false;
    }
    
    return true;
}

function showLoadingState() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const submitBtn = document.getElementById('submitBtn');
    
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
    }
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...';
    }
    
    // Simulate progress
    simulateProgress();
}

function simulateProgress() {
    const progressBar = document.querySelector('#loadingIndicator .progress-bar');
    if (!progressBar) return;
    
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) {
            progress = 90;
            clearInterval(interval);
        }
        progressBar.style.width = progress + '%';
    }, 200);
}

function initializeDragAndDrop() {
    const uploadArea = document.getElementById('uploadForm');
    if (!uploadArea) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        uploadArea.classList.add('drag-over');
    }
    
    function unhighlight(e) {
        uploadArea.classList.remove('drag-over');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            const fileInput = document.getElementById('fileInput');
            if (fileInput) {
                fileInput.files = files;
                // Trigger change event
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            }
        }
    }
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

function initializeProgressTracking() {
    // Track upload progress if supported
    const uploadForm = document.getElementById('uploadForm');
    if (!uploadForm) return;
    
    // Add progress tracking for form submission
    uploadForm.addEventListener('submit', function(e) {
        // This would be used for actual AJAX uploads
        // For now, we just show the loading state
        console.log('Form submitted, tracking progress...');
    });
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    
    const iconClass = type === 'error' ? 'fa-exclamation-triangle' : 
                     type === 'success' ? 'fa-check-circle' : 'fa-info-circle';
    
    alertDiv.innerHTML = `
        <i class="fas ${iconClass} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of container
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.classList.remove('show');
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.remove();
                    }
                }, 150);
            }
        }, 5000);
    }
}

// Utility functions for result page
function flagPrediction(filename, prediction) {
    if (confirm('Are you sure this diagnosis is incorrect?')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/flag_prediction';
        
        const filenameInput = document.createElement('input');
        filenameInput.type = 'hidden';
        filenameInput.name = 'filename';
        filenameInput.value = filename;
        
        const predictionInput = document.createElement('input');
        predictionInput.type = 'hidden';
        predictionInput.name = 'prediction';
        predictionInput.value = prediction;
        
        form.appendChild(filenameInput);
        form.appendChild(predictionInput);
        document.body.appendChild(form);
        form.submit();
    }
}

function addCameraCaptureIndicator() {
    // Add visual indicator that image was captured from camera
    const preview = document.getElementById('imagePreview');
    if (preview) {
        const indicator = document.createElement('div');
        indicator.className = 'camera-capture-indicator mt-2 text-center';
        indicator.innerHTML = `
            <span class="badge bg-success">
                <i class="fas fa-camera me-1"></i>Camera Captured
            </span>
            <small class="d-block text-muted mt-1">
                Photo taken with device camera
            </small>
        `;
        
        // Remove existing indicator
        const existing = preview.querySelector('.camera-capture-indicator');
        if (existing) existing.remove();
        
        // Add new indicator
        preview.appendChild(indicator);
    }
}

// Export functions for global use
window.OkroHealthDetector = {
    showAlert,
    flagPrediction,
    validateForm,
    showImagePreview,
    hideImagePreview,
    addCameraCaptureIndicator
};
