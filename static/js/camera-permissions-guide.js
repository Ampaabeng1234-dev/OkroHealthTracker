/**
 * Camera permissions guide and troubleshooting helper
 */

class CameraPermissionsGuide {
    constructor() {
        this.init();
    }
    
    init() {
        this.addPermissionsGuideModal();
        this.setupEventListeners();
    }
    
    addPermissionsGuideModal() {
        const modalHtml = `
            <div class="modal fade" id="cameraPermissionsModal" tabindex="-1" aria-labelledby="cameraPermissionsLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="cameraPermissionsLabel">
                                <i class="fas fa-camera me-2"></i>Camera Setup Guide
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                <strong>Camera access is needed to take photos of okra leaves</strong>
                            </div>
                            
                            <h6>How to allow camera access:</h6>
                            <ol class="mb-4">
                                <li>Look for a camera icon in your browser's address bar</li>
                                <li>Click the camera icon or "Allow" when prompted</li>
                                <li>If blocked, click the camera icon and select "Always allow"</li>
                                <li>Refresh the page if needed</li>
                            </ol>
                            
                            <div class="browser-guides">
                                <div class="accordion" id="browserAccordion">
                                    <div class="accordion-item">
                                        <h2 class="accordion-header">
                                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#chromeGuide">
                                                <i class="fab fa-chrome me-2"></i>Chrome / Edge
                                            </button>
                                        </h2>
                                        <div id="chromeGuide" class="accordion-collapse collapse">
                                            <div class="accordion-body">
                                                <small>
                                                    1. Click the camera icon in the address bar<br>
                                                    2. Select "Always allow" for camera access<br>
                                                    3. Click "Done" and refresh the page
                                                </small>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="accordion-item">
                                        <h2 class="accordion-header">
                                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#firefoxGuide">
                                                <i class="fab fa-firefox me-2"></i>Firefox
                                            </button>
                                        </h2>
                                        <div id="firefoxGuide" class="accordion-collapse collapse">
                                            <div class="accordion-body">
                                                <small>
                                                    1. Click the camera icon in the address bar<br>
                                                    2. Select "Allow" and check "Remember this decision"<br>
                                                    3. Refresh the page
                                                </small>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="accordion-item">
                                        <h2 class="accordion-header">
                                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#safariGuide">
                                                <i class="fab fa-safari me-2"></i>Safari (Mobile)
                                            </button>
                                        </h2>
                                        <div id="safariGuide" class="accordion-collapse collapse">
                                            <div class="accordion-body">
                                                <small>
                                                    1. Go to Settings > Safari > Camera<br>
                                                    2. Select "Allow" or "Ask"<br>
                                                    3. Return to the app and tap "Take Photo"
                                                </small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="alert alert-success mt-3">
                                <i class="fas fa-mobile-alt me-2"></i>
                                <strong>Alternative for Mobile Users:</strong><br>
                                <small>
                                    1. Take a photo with your device's camera app<br>
                                    2. Come back here and click "Choose File"<br>
                                    3. Select the photo from your gallery<br>
                                    4. Upload for disease analysis
                                </small>
                            </div>
                            
                            <div class="alert alert-warning mt-3">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                <strong>Quick Camera Test:</strong><br>
                                <button type="button" class="btn btn-sm btn-outline-primary" id="testCameraBtn">
                                    <i class="fas fa-video me-1"></i>Test Camera Access
                                </button>
                                <small class="d-block mt-1">Click to verify your camera is working</small>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                I'll use file upload instead
                            </button>
                            <button type="button" class="btn btn-success" id="tryAgainBtn">
                                <i class="fas fa-redo me-2"></i>Try Camera Again
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.modal = new bootstrap.Modal(document.getElementById('cameraPermissionsModal'));
    }
    
    setupEventListeners() {
        // Try again button
        document.getElementById('tryAgainBtn')?.addEventListener('click', () => {
            this.modal.hide();
            // Trigger camera open again
            const cameraBtn = document.getElementById('openCameraBtn');
            if (cameraBtn) {
                cameraBtn.click();
            }
        });
        
        // Camera help button
        document.getElementById('cameraHelpBtn')?.addEventListener('click', () => {
            this.show();
        });
        
        // Camera test button
        document.getElementById('testCameraBtn')?.addEventListener('click', () => {
            this.testCamera();
        });
    }
    
    show() {
        this.modal.show();
    }
    
    hide() {
        this.modal.hide();
    }
    
    async testCamera() {
        const testBtn = document.getElementById('testCameraBtn');
        const originalText = testBtn.innerHTML;
        
        try {
            testBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Testing...';
            testBtn.disabled = true;
            
            // Quick test
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            stream.getTracks().forEach(track => track.stop());
            
            testBtn.innerHTML = '<i class="fas fa-check me-1"></i>Camera Works!';
            testBtn.className = 'btn btn-sm btn-success';
            
            setTimeout(() => {
                testBtn.innerHTML = originalText;
                testBtn.className = 'btn btn-sm btn-outline-primary';
                testBtn.disabled = false;
            }, 2000);
            
        } catch (error) {
            testBtn.innerHTML = '<i class="fas fa-times me-1"></i>Camera Failed';
            testBtn.className = 'btn btn-sm btn-danger';
            
            setTimeout(() => {
                testBtn.innerHTML = originalText;
                testBtn.className = 'btn btn-sm btn-outline-primary';
                testBtn.disabled = false;
            }, 2000);
        }
    }
}

// Export for global use
window.CameraPermissionsGuide = CameraPermissionsGuide;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.cameraPermissionsGuide = new CameraPermissionsGuide();
});