/**
 * Mobile-responsive camera capture functionality
 * Provides camera access, photo capture, and upload capabilities
 */

class CameraCapture {
    constructor() {
        this.stream = null;
        this.video = null;
        this.canvas = null;
        this.isCapturing = false;
        this.isMobile = this.checkMobileDevice();
        
        // Initialize camera capture interface
        this.init();
    }
    
    checkMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               (navigator.maxTouchPoints && navigator.maxTouchPoints > 2);
    }
    
    init() {
        // Create camera capture modal
        this.createCameraModal();
        
        // Add camera button to upload interface
        this.addCameraButton();
        
        // Event listeners
        this.setupEventListeners();
    }
    
    createCameraModal() {
        const modalHtml = `
            <div class="modal fade" id="cameraModal" tabindex="-1" aria-labelledby="cameraModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-fullscreen-md-down modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="cameraModalLabel">
                                <i class="fas fa-camera me-2"></i>Capture Okra Leaf Photo
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body p-0">
                            <div class="camera-container position-relative">
                                <!-- Video stream -->
                                <video id="cameraVideo" class="w-100 h-auto" autoplay muted playsinline style="max-height: 70vh; object-fit: cover;"></video>
                                
                                <!-- Camera controls overlay -->
                                <div class="camera-controls position-absolute bottom-0 start-0 w-100 p-3" style="background: linear-gradient(transparent, rgba(0,0,0,0.7));">
                                    <div class="d-flex justify-content-center align-items-center gap-3">
                                        <!-- Flip camera button (mobile only) -->
                                        <button id="flipCameraBtn" class="btn btn-outline-light rounded-circle d-none" style="width: 50px; height: 50px;">
                                            <i class="fas fa-sync-alt"></i>
                                        </button>
                                        
                                        <!-- Capture button -->
                                        <button id="captureBtn" class="btn btn-success rounded-circle" style="width: 70px; height: 70px;">
                                            <i class="fas fa-camera fa-lg"></i>
                                        </button>
                                        
                                        <!-- Gallery button -->
                                        <button id="galleryBtn" class="btn btn-outline-light rounded-circle" style="width: 50px; height: 50px;">
                                            <i class="fas fa-images"></i>
                                        </button>
                                    </div>
                                </div>
                                
                                <!-- Loading overlay -->
                                <div id="cameraLoading" class="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center bg-dark bg-opacity-75 d-none">
                                    <div class="text-center text-white">
                                        <div class="spinner-border mb-3" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                        <p>Accessing camera...</p>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Preview captured image -->
                            <div id="capturePreview" class="d-none p-3">
                                <div class="text-center">
                                    <h6>Captured Photo</h6>
                                    <canvas id="captureCanvas" class="img-fluid border rounded mb-3" style="max-width: 100%; max-height: 400px;"></canvas>
                                    
                                    <div class="d-flex gap-2 justify-content-center">
                                        <button id="retakeBtn" class="btn btn-outline-secondary">
                                            <i class="fas fa-redo me-2"></i>Retake
                                        </button>
                                        <button id="usePhotoBtn" class="btn btn-success">
                                            <i class="fas fa-check me-2"></i>Use Photo
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer d-none" id="cameraModalFooter">
                            <small class="text-muted">
                                <i class="fas fa-info-circle me-1"></i>
                                Take a clear photo of the okra leaf in good lighting for best results
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Get references
        this.modal = new bootstrap.Modal(document.getElementById('cameraModal'));
        this.video = document.getElementById('cameraVideo');
        this.canvas = document.getElementById('captureCanvas');
    }
    
    addCameraButton() {
        // Find file input and add camera button next to it
        const fileInput = document.querySelector('input[type="file"][name="file"]');
        if (!fileInput || !fileInput.parentElement) return;
        
        const container = fileInput.parentElement;
        
        // Check camera support
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            // Camera is supported - create button
            const cameraBtn = document.createElement('button');
            cameraBtn.type = 'button';
            cameraBtn.className = 'btn btn-success ms-2';
            cameraBtn.id = 'openCameraBtn';
            cameraBtn.innerHTML = '<i class="fas fa-camera me-2"></i>Take Photo';
            
            // Add mobile-specific styling
            if (this.isMobile) {
                cameraBtn.classList.add('btn-lg');
                cameraBtn.innerHTML = '<i class="fas fa-camera me-2"></i>Camera';
            }
            
            container.appendChild(cameraBtn);
            
            // Add mobile-first layout for file input area
            if (this.isMobile) {
                container.classList.add('d-flex', 'flex-column', 'gap-2');
                fileInput.classList.add('mb-0');
            }
        } else {
            // Camera not supported - update UI messages
            if (this.isMobile) {
                const mobileInfo = document.getElementById('mobileInfo');
                const cameraWarning = document.getElementById('cameraNotSupported');
                
                if (mobileInfo) mobileInfo.classList.add('d-none');
                if (cameraWarning) cameraWarning.classList.remove('d-none');
            }
        }
    }
    
    setupEventListeners() {
        // Open camera button
        document.getElementById('openCameraBtn')?.addEventListener('click', () => {
            this.openCamera();
        });
        
        // Camera modal events
        document.getElementById('cameraModal')?.addEventListener('shown.bs.modal', () => {
            this.startCamera();
        });
        
        document.getElementById('cameraModal')?.addEventListener('hidden.bs.modal', () => {
            this.stopCamera();
        });
        
        // Capture button
        document.getElementById('captureBtn')?.addEventListener('click', () => {
            this.capturePhoto();
        });
        
        // Flip camera button
        document.getElementById('flipCameraBtn')?.addEventListener('click', () => {
            this.flipCamera();
        });
        
        // Gallery button
        document.getElementById('galleryBtn')?.addEventListener('click', () => {
            this.openGallery();
        });
        
        // Preview buttons
        document.getElementById('retakeBtn')?.addEventListener('click', () => {
            this.retakePhoto();
        });
        
        document.getElementById('usePhotoBtn')?.addEventListener('click', () => {
            this.usePhoto();
        });
        
        // Handle device orientation changes
        if (this.isMobile) {
            window.addEventListener('orientationchange', () => {
                setTimeout(() => this.adjustCameraLayout(), 100);
            });
        }
    }
    
    async openCamera() {
        // Check camera support first
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.showError('Camera not supported on this device');
            return;
        }
        
        // Quick permission test
        try {
            this.showLoading(true, 'Requesting camera permission...');
            
            // Test camera access briefly
            const testStream = await navigator.mediaDevices.getUserMedia({ video: true });
            // Stop test stream immediately
            testStream.getTracks().forEach(track => track.stop());
            
            // Show success feedback
            this.showLoading(false);
            
        } catch (error) {
            this.showLoading(false);
            
            let message = 'Camera access failed. ';
            if (error.name === 'NotAllowedError') {
                message += 'Please click "Allow" when your browser asks for camera permission.';
            } else if (error.name === 'NotFoundError') {
                message += 'No camera found on this device.';
            } else {
                message += 'Please check your camera is working and not used by other apps.';
            }
            
            this.showError(message);
            return;
        }
        
        // Open modal after permission granted
        this.modal.show();
    }
    
    async startCamera() {
        try {
            this.showLoading(true);
            
            // Add timeout for camera initialization
            const initCamera = async () => {
                // Try with preferred constraints first
                let constraints = {
                    video: {
                        facingMode: this.isMobile ? { ideal: 'environment' } : 'user',
                        width: { ideal: 1280, max: 1920 },
                        height: { ideal: 720, max: 1080 }
                    }
                };
                
                try {
                    this.stream = await navigator.mediaDevices.getUserMedia(constraints);
                } catch (error) {
                    console.warn('Failed with preferred constraints, trying basic:', error);
                    // Fallback to basic video
                    this.stream = await navigator.mediaDevices.getUserMedia({ video: true });
                }
                
                this.video.srcObject = this.stream;
                
                // Wait for video to load
                return new Promise((resolve, reject) => {
                    this.video.onloadedmetadata = () => {
                        this.video.play()
                            .then(resolve)
                            .catch(reject);
                    };
                    this.video.onerror = reject;
                });
            };
            
            // Add 10 second timeout
            await Promise.race([
                initCamera(),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Camera initialization timeout')), 10000)
                )
            ]);
            
            // Show flip button on mobile if multiple cameras available
            if (this.isMobile) {
                try {
                    const devices = await navigator.mediaDevices.enumerateDevices();
                    const videoDevices = devices.filter(device => device.kind === 'videoinput');
                    if (videoDevices.length > 1) {
                        document.getElementById('flipCameraBtn').classList.remove('d-none');
                    }
                } catch (e) {
                    console.warn('Could not enumerate devices:', e);
                }
            }
            
            this.showLoading(false);
            this.isCapturing = true;
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.showLoading(false);
            
            let message = 'Unable to access camera. ';
            if (error.name === 'NotAllowedError') {
                message += 'Please allow camera permissions and try again.';
            } else if (error.name === 'NotFoundError') {
                message += 'No camera found on this device.';
            } else if (error.name === 'NotReadableError') {
                message += 'Camera is being used by another application.';
            } else if (error.message === 'Camera initialization timeout') {
                message += 'Camera took too long to load. Please try again.';
            } else {
                message += 'Please check your browser settings.';
            }
            
            this.showError(message);
        }
    }
    
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        this.isCapturing = false;
        this.resetPreview();
    }
    
    async flipCamera() {
        if (!this.isMobile || !this.stream) return;
        
        try {
            // Get current facing mode
            const track = this.stream.getVideoTracks()[0];
            const settings = track.getSettings();
            const currentFacing = settings.facingMode;
            
            // Toggle facing mode
            const newFacing = currentFacing === 'environment' ? 'user' : 'environment';
            
            // Stop current stream
            this.stopCamera();
            
            // Start with new facing mode
            const constraints = {
                video: {
                    facingMode: newFacing,
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.stream;
            this.isCapturing = true;
            
        } catch (error) {
            console.error('Error flipping camera:', error);
            // Fallback to original camera
            this.startCamera();
        }
    }
    
    capturePhoto() {
        if (!this.isCapturing || !this.video || !this.canvas) return;
        
        // Set canvas size to video dimensions
        const videoWidth = this.video.videoWidth;
        const videoHeight = this.video.videoHeight;
        
        this.canvas.width = videoWidth;
        this.canvas.height = videoHeight;
        
        // Draw video frame to canvas
        const ctx = this.canvas.getContext('2d');
        ctx.drawImage(this.video, 0, 0, videoWidth, videoHeight);
        
        // Show preview
        this.showPreview();
        
        // Add capture feedback
        this.addCaptureEffect();
    }
    
    addCaptureEffect() {
        // Flash effect
        const flash = document.createElement('div');
        flash.className = 'position-fixed top-0 start-0 w-100 h-100';
        flash.style.cssText = 'background: white; z-index: 9999; opacity: 0.8; pointer-events: none;';
        document.body.appendChild(flash);
        
        // Remove flash after animation
        setTimeout(() => {
            flash.remove();
        }, 150);
        
        // Capture sound (if audio is available)
        if ('AudioContext' in window || 'webkitAudioContext' in window) {
            this.playShutterSound();
        }
    }
    
    playShutterSound() {
        // Simple shutter sound using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (error) {
            // Silent fail for audio
        }
    }
    
    showPreview() {
        // Hide video, show preview
        document.querySelector('.camera-container').classList.add('d-none');
        document.getElementById('capturePreview').classList.remove('d-none');
        document.getElementById('cameraModalFooter').classList.remove('d-none');
    }
    
    retakePhoto() {
        this.resetPreview();
    }
    
    resetPreview() {
        document.querySelector('.camera-container').classList.remove('d-none');
        document.getElementById('capturePreview').classList.add('d-none');
        document.getElementById('cameraModalFooter').classList.add('d-none');
    }
    
    async usePhoto() {
        try {
            // Convert canvas to blob
            const blob = await new Promise(resolve => {
                this.canvas.toBlob(resolve, 'image/jpeg', 0.8);
            });
            
            // Create file from blob
            const file = new File([blob], `okra_leaf_${Date.now()}.jpg`, {
                type: 'image/jpeg'
            });
            
            // Update file input
            this.updateFileInput(file);
            
            // Close modal
            this.modal.hide();
            
            // Show success message
            this.showSuccess('Photo captured successfully!');
            
        } catch (error) {
            console.error('Error processing photo:', error);
            this.showError('Error processing photo');
        }
    }
    
    updateFileInput(file) {
        const fileInput = document.querySelector('input[type="file"][name="file"]');
        if (fileInput) {
            // Create DataTransfer to update file input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            
            // Trigger change event
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            
            // Update UI to show selected file
            this.updateFileInputDisplay(file);
        }
    }
    
    updateFileInputDisplay(file) {
        // Create preview thumbnail
        const reader = new FileReader();
        reader.onload = (e) => {
            // Find upload area and add preview
            const uploadArea = document.querySelector('.upload-area') || 
                              document.querySelector('.card-body');
            
            if (uploadArea) {
                // Remove existing previews
                const existingPreview = uploadArea.querySelector('.camera-preview');
                if (existingPreview) {
                    existingPreview.remove();
                }
                
                // Create new preview
                const previewDiv = document.createElement('div');
                previewDiv.className = 'camera-preview mt-3 text-center';
                previewDiv.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">
                                <i class="fas fa-camera text-success me-2"></i>
                                Captured Photo Ready
                            </h6>
                            <img src="${e.target.result}" class="img-fluid rounded" style="max-height: 200px;">
                            <p class="text-muted small mt-2">${file.name}</p>
                            <p class="text-success small">
                                <i class="fas fa-check-circle me-1"></i>
                                Ready for disease detection
                            </p>
                        </div>
                    </div>
                `;
                
                uploadArea.appendChild(previewDiv);
            }
        };
        reader.readAsDataURL(file);
    }
    
    openGallery() {
        // Trigger file input click
        const fileInput = document.querySelector('input[type="file"][name="file"]');
        if (fileInput) {
            fileInput.click();
        }
    }
    
    showLoading(show, message = 'Accessing camera...') {
        const loading = document.getElementById('cameraLoading');
        if (loading) {
            loading.classList.toggle('d-none', !show);
            
            // Update message if provided
            const messageElement = loading.querySelector('p');
            if (messageElement && show) {
                messageElement.textContent = message;
            }
        }
    }
    
    adjustCameraLayout() {
        // Adjust layout after orientation change
        if (this.video && this.isCapturing) {
            // Force video element to recalculate dimensions
            this.video.style.height = 'auto';
            setTimeout(() => {
                this.video.style.height = '';
            }, 10);
        }
    }
    
    showError(message) {
        this.showAlert(message, 'danger');
    }
    
    showSuccess(message) {
        this.showAlert(message, 'success');
    }
    
    showAlert(message, type = 'info') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        alertDiv.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'danger' ? 'fa-exclamation-triangle' : 'fa-info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto dismiss after 4 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }
        }, 4000);
    }
}

// Initialize camera capture when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on pages with file upload
    if (document.querySelector('input[type="file"][name="file"]')) {
        window.cameraCapture = new CameraCapture();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CameraCapture;
}