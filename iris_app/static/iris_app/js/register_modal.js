/* ============================================
   REGISTRATION MODAL JAVASCRIPT
   ============================================ */

class RegistrationModal {
    constructor() {
        this.modal = null;
        this.overlay = null;
        this.closeBtn = null;
        this.isLoading = false;
        this.init();
    }

    init() {
        //this.createModalHTML();
        this.attachEventListeners();
    }

    createModalHTML() {
        // Create modal HTML structure if it doesn't exist
        if (!document.getElementById('registerModal')) {
            const modalHTML = `
                <div id="registerModal" class="register-modal-overlay">
                    <div class="register-modal-dialog">
                        <div class="register-modal-header">
                            <h2 class="register-modal-title">Challenge Registration</h2>
                            <button class="register-modal-close" aria-label="Close modal">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        <div class="register-modal-body">
                            <div id="registerModalContent" class="register-modal-content">
                                <div class="register-modal-loading">
                                    <div class="spinner-border" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }

        this.modal = document.getElementById('registerModal');
        this.overlay = this.modal.querySelector('.register-modal-overlay');
        this.closeBtn = this.modal.querySelector('.register-modal-close');
        this.contentContainer = document.getElementById('registerModalContent');
    }

    attachEventListeners() {
        // Close button click
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.close());
        }

        // Close on overlay click
        if (this.modal) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.close();
                }
            });
        }

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('active')) {
                this.close();
            }
        });

        // Attach to all Register Now buttons
        this.attachToButtons();
    }

    attachToButtons() {
        document.addEventListener('click', (e) => {
            const registerBtn = e.target.closest('[data-register-modal]');
            if (registerBtn) {
                e.preventDefault();
                const url = registerBtn.getAttribute('data-register-url') || registerBtn.href;
                const challengeId = registerBtn.getAttribute('data-challenge-id');
                this.open(url, challengeId);
            }
        });
    }

    open(url, challengeId) {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showLoading();
        this.modal.classList.add('active');
        document.body.classList.add('register-modal-open');

        // Fetch the registration form
        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error('Failed to load registration page');
                return response.text();
            })
            .then(html => {
                this.loadFormContent(html);
                this.attachFormHandlers();
            })
            .catch(error => {
                console.error('Error loading registration form:', error);
                this.showError('Failed to load registration form. Please try again.');
            })
            .finally(() => {
                this.isLoading = false;
            });
    }

    loadFormContent(html) {
        // Extract the registration form content from the full page
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        // Find the main registration content
        const regContent = doc.querySelector('.reg-content') || doc.querySelector('.reg-container');

        if (regContent) {
            // Clone and clean the content
            const clonedContent = regContent.cloneNode(true);

            // Remove or hide any unnecessary styling and page elements
            clonedContent.classList.add('register-modal-content');

            // Clear the container and add new content
            this.contentContainer.innerHTML = '';
            this.contentContainer.appendChild(clonedContent);

            // Adjust heights and styles for modal
            this.optimizeFormForModal();
        } else {
            this.showError('Could not load registration form.');
        }
    }

    optimizeFormForModal() {
        // Remove or adjust styles that don't work well in modal
        const container = this.contentContainer.querySelector('.reg-container');
        if (container) {
            container.style.background = 'transparent';
            container.style.backgroundImage = 'none';
            container.style.outline = 'none';
            container.style.padding = '0';
        }

        // Ensure forms are properly sized
        const form = this.contentContainer.querySelector('form');
        if (form) {
            form.style.width = '100%';
        }
    }

    attachFormHandlers() {
        // Attach handlers for form submission
        const form = this.contentContainer.querySelector('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                this.handleFormSubmit(e, form);
            });
        }

        // Attach toggle switch handlers if they exist
        const toggleOptions = this.contentContainer.querySelectorAll('.toggle-option input[type="radio"]');
        toggleOptions.forEach(radio => {
            radio.addEventListener('change', (e) => this.handleToggleChange(e));
        });
    }

    handleFormSubmit(e, form) {
        const submitBtn = form.querySelector('.submit-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Submitting...';
        }

        // Let the form submit normally - it will handle the response
        // You can add AJAX submission here if needed
    }

    handleToggleChange(e) {
        // Handle toggle switch changes (e.g., show/hide team details)
        const section = e.target.closest('.form-section');
        if (section) {
            const teamDetailsSection = this.contentContainer.querySelector('.team-details-section');
            if (teamDetailsSection) {
                if (e.target.value === 'team') {
                    teamDetailsSection.classList.add('active');
                } else {
                    teamDetailsSection.classList.remove('active');
                }
            }
        }
    }

    showLoading() {
        this.contentContainer.innerHTML = `
            <div class="register-modal-loading">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    }

    showError(message) {
        this.contentContainer.innerHTML = `
            <div class="register-modal-error">
                <i class="fas fa-exclamation-circle me-2"></i>
                ${message}
            </div>
        `;
    }

    showSuccess(message) {
        const successHTML = `
            <div class="register-modal-success">
                <i class="fas fa-check-circle"></i>
                ${message}
            </div>
        `;
        const errorDiv = this.contentContainer.querySelector('.register-modal-error');
        if (errorDiv) {
            errorDiv.remove();
        }
        this.contentContainer.insertAdjacentHTML('afterbegin', successHTML);
    }

    close() {
        if (!this.modal.classList.contains('active')) return;

        this.modal.classList.add('closing');

        setTimeout(() => {
            this.modal.classList.remove('active', 'closing');
            document.body.classList.remove('register-modal-open');
            this.contentContainer.innerHTML = `
                <div class="register-modal-loading">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            `;
        }, 300);
    }
}

// Initialize modal when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.registrationModal = new RegistrationModal();
});
