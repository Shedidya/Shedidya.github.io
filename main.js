// Main JavaScript file for HMAgram
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeImageUpload();
    initializeDragAndDrop();
    initializeFormValidation();
    initializeLazyLoading();
    
    // Initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
});

// Image Upload Preview
function initializeImageUpload() {
    const imageInput = document.getElementById('imageInput');
    const uploadArea = document.getElementById('uploadArea');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                handleImagePreview(file);
            }
        });
    }
    
    if (uploadArea) {
        uploadArea.addEventListener('click', function() {
            imageInput?.click();
        });
    }
    
    function handleImagePreview(file) {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                if (previewImg && imagePreview) {
                    previewImg.src = e.target.result;
                    imagePreview.style.display = 'block';
                    uploadArea?.classList.add('has-image');
                }
            };
            reader.readAsDataURL(file);
        }
    }
}

// Drag and Drop functionality
function initializeDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    
    if (!uploadArea || !imageInput) return;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        uploadArea.classList.add('dragover');
    }
    
    function unhighlight(e) {
        uploadArea.classList.remove('dragover');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            imageInput.files = files;
            handleImagePreview(files[0]);
        }
    }
    
    function handleImagePreview(file) {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const previewImg = document.getElementById('previewImg');
                const imagePreview = document.getElementById('imagePreview');
                if (previewImg && imagePreview) {
                    previewImg.src = e.target.result;
                    imagePreview.style.display = 'block';
                }
            };
            reader.readAsDataURL(file);
        }
    }
}

// Form Validation Enhancement
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            } else {
                // Add loading state to submit button
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    const originalText = submitBtn.textContent;
                    submitBtn.textContent = 'Processing...';
                    
                    // Reset button after 10 seconds as fallback
                    setTimeout(() => {
                        submitBtn.disabled = false;
                        submitBtn.textContent = originalText;
                    }, 10000);
                }
            }
            form.classList.add('was-validated');
        });
        
        // Real-time validation for inputs
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.value.trim() !== '') {
                    this.classList.add('was-validated');
                }
            });
        });
    });
}

// Lazy Loading for Images
function initializeLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => imageObserver.observe(img));
    }
}

// Hashtag Helper
function initializeHashtagHelper() {
    const hashtagInput = document.querySelector('input[name="hashtags"]');
    
    if (hashtagInput) {
        hashtagInput.addEventListener('input', function(e) {
            let value = e.target.value;
            
            // Auto-add # if not present at the start of words
            value = value.replace(/(?:^|\s)([^#\s]+)/g, ' #$1');
            value = value.trim();
            
            e.target.value = value;
        });
        
        hashtagInput.addEventListener('blur', function(e) {
            // Clean up multiple spaces and ensure proper formatting
            let value = e.target.value;
            value = value.replace(/\s+/g, ' ').trim();
            e.target.value = value;
        });
    }
}

// Infinite Scroll (if needed)
function initializeInfiniteScroll() {
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (!loadMoreBtn) return;
    
    let loading = false;
    
    function loadMoreContent() {
        if (loading) return;
        loading = true;
        
        loadMoreBtn.textContent = 'Loading...';
        loadMoreBtn.disabled = true;
        
        // Simulate loading (replace with actual AJAX call)
        setTimeout(() => {
            loading = false;
            loadMoreBtn.textContent = 'Load More';
            loadMoreBtn.disabled = false;
        }, 1000);
    }
    
    loadMoreBtn.addEventListener('click', loadMoreContent);
    
    // Auto-load when near bottom
    window.addEventListener('scroll', () => {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
            loadMoreContent();
        }
    });
}

// Search Enhancement
function initializeSearch() {
    const searchInput = document.querySelector('input[name="query"]');
    const searchForm = document.querySelector('.search-form');
    
    if (searchInput && searchForm) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length > 2) {
                searchTimeout = setTimeout(() => {
                    // Auto-submit search after user stops typing
                    searchForm.submit();
                }, 500);
            }
        });
    }
}

// Like Button Animation
function initializeLikeAnimation() {
    const likeButtons = document.querySelectorAll('a[href*="like"]');
    
    likeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const heartIcon = this.querySelector('[data-feather="heart"]');
            if (heartIcon) {
                heartIcon.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    heartIcon.style.transform = 'scale(1)';
                }, 150);
            }
        });
    });
}

// Image Error Handling
function initializeImageErrorHandling() {
    const images = document.querySelectorAll('img');
    
    images.forEach(img => {
        img.addEventListener('error', function() {
            this.style.display = 'none';
            // Optionally show a placeholder
            const placeholder = document.createElement('div');
            placeholder.className = 'image-placeholder';
            placeholder.innerHTML = '<i data-feather="image"></i><span>Image not available</span>';
            this.parentNode.appendChild(placeholder);
            
            // Re-initialize feather icons for the new placeholder
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        });
    });
}

// Utility Functions
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => document.body.removeChild(toast), 300);
    }, 3000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return '1 day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.ceil(diffDays / 30)} months ago`;
    
    return `${Math.ceil(diffDays / 365)} years ago`;
}

// Initialize additional components when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeHashtagHelper();
    initializeInfiniteScroll();
    initializeSearch();
    initializeLikeAnimation();
    initializeImageErrorHandling();
});

// Handle navigation active states
function updateNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const currentPath = window.location.pathname;
    
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

// Call on page load
updateNavigation();

