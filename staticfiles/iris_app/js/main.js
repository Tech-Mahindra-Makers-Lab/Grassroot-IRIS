// DOM Content Loaded - Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('IRIS Application initialized');
    initializeApp();
});

// Initialize the application
function initializeApp() {
    setupEventListeners();
    setupCarousel();
    setupSmoothScroll();
}

// Setup Event Listeners
function setupEventListeners() {
    // Explore Challenges Button
    const exploreChallengesBtn = document.querySelector('.hero .btn-primary');
    if (exploreChallengesBtn) {
        exploreChallengesBtn.addEventListener('click', handleExploreChallenges);
    }

    // Submit Ideas Buttons
    const submitButtons = document.querySelectorAll('.btn-primary[disabled], .challenge-card .btn-primary');
    submitButtons.forEach(btn => {
        btn.addEventListener('click', handleSubmitIdeas);
    });

    // FAQ Accordion
    setupFAQAccordion();
}

// Setup FAQ Accordion
function setupFAQAccordion() {
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const header = item.querySelector('.faq-header');
        const toggle = item.querySelector('.faq-toggle');
        if (header) {
            header.addEventListener('click', () => {
                toggleFAQItem(item);
            });
        }
    });
}

// Toggle FAQ Item
function toggleFAQItem(item) {
    const isActive = item.classList.contains('active');
    const toggle = item.querySelector('.faq-toggle');

    // Close all other items
    document.querySelectorAll('.faq-item').forEach(faqItem => {
        faqItem.classList.remove('active');
        const faqToggle = faqItem.querySelector('.faq-toggle');
        if (faqToggle) {
            faqToggle.textContent = '+';
        }
    });

    // Toggle current item
    if (!isActive) {
        item.classList.add('active');
        if (toggle) {
            toggle.textContent = '−';
        }
    }
}

// Carousel functionality
function setupCarousel() {
    const carousel = document.querySelector('.carousel-controls');
    if (!carousel) return;

    const dots = document.querySelectorAll('.dot');
    const prevBtn = document.querySelector('.carousel-btn.prev');
    const nextBtn = document.querySelector('.carousel-btn.next');
    let currentSlide = 0;

    if (prevBtn) {
        prevBtn.addEventListener('click', () => previousSlide());
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => nextSlide());
    }

    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => goToSlide(index));
    });

    function nextSlide() {
        currentSlide = (currentSlide + 1) % dots.length;
        updateCarousel();
    }

    function previousSlide() {
        currentSlide = (currentSlide - 1 + dots.length) % dots.length;
        updateCarousel();
    }

    function goToSlide(index) {
        currentSlide = index;
        updateCarousel();
    }

    function updateCarousel() {
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentSlide);
        });
    }
}

// Smooth scroll for navigation links
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#' || href === '') return;

            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Handle Explore Challenges
function handleExploreChallenges() {
    console.log('Explore Challenges clicked');
    const challengesSection = document.getElementById('challenges');
    if (challengesSection) {
        challengesSection.scrollIntoView({ behavior: 'smooth' });
    }
}

// Handle Submit Ideas
function handleSubmitIdeas(e) {
    e.preventDefault();
    console.log('Submit Ideas clicked');
    showNotification('Great! We are excited to see your innovative ideas.');
    // Add your logic here - could open a form, navigate to submission page, etc.
}

// Show Notification
function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #27ae60;
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        max-width: 400px;
    `;

    document.body.appendChild(notification);

    // Remove notification after 4 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// CSS Animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.7;
        }
    }
`;
document.head.appendChild(style);

// Utility: Fetch Data Example
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        return null;
    }
}

// Utility: Debounce Function
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
}

// Utility: Throttle Function
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Intersection Observer for lazy loading and animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.animation = 'fadeIn 0.6s ease-in-out';
        }
    });
}, observerOptions);

// Observe sections for animation
document.querySelectorAll('section').forEach(section => {
    section.style.opacity = '0';
    observer.observe(section);
});

console.log('IRIS - Innovation, Collaboration, Reward Platform');
