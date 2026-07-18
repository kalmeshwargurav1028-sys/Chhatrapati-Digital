document.addEventListener('DOMContentLoaded', () => {
    // Smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Form Submission Handling
    const orderForm = document.getElementById('orderForm');
    const formStatus = document.getElementById('formStatus');

    if (orderForm) {
        orderForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const service = document.getElementById('serviceType').value;
            const details = document.getElementById('orderDetails').value;
            const submitBtn = orderForm.querySelector('button[type="submit"]');

            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
            formStatus.textContent = '';
            formStatus.className = 'form-status';

            try {
                const response = await fetch('/api/order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ service, details })
                });

                const result = await response.json();

                if (response.ok) {
                    formStatus.textContent = result.message;
                    formStatus.classList.remove('error');
                    orderForm.reset();
                } else {
                    throw new Error('Submission failed');
                }
            } catch (error) {
                formStatus.textContent = 'Error submitting order. Please try again.';
                formStatus.classList.add('error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Inquiry';
            }
        });
    }

    // Vendor Form Submission Handling
    const vendorForm = document.getElementById('vendorForm');
    if (vendorForm) {
        vendorForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const mobile = document.getElementById('vendorMobile').value;
            const city = document.getElementById('vendorCity').value;
            const category = document.getElementById('vendorCategory').value;
            const submitBtn = vendorForm.querySelector('button[type="submit"]');

            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';

            try {
                const response = await fetch('/api/vendor-inquiry', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mobile, city, category })
                });

                const result = await response.json();

                if (response.ok) {
                    alert(result.message || 'Details submitted successfully!');
                    vendorForm.reset();
                } else {
                    throw new Error('Submission failed');
                }
            } catch (error) {
                alert('Error submitting details. Please try again.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit';
            }
        });
    }

    // Intersection Observer for scroll animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.service-card, .gallery-item, .order-box, .pricing-card, .testimonial-card, .faq-item, .about-content, .footer-col').forEach((el, index) => {
        el.style.opacity = "0";
        el.style.transform = "translateY(20px)";
        el.style.transition = `all 0.5s ease ${index * 0.1}s`;
        observer.observe(el);
    });

    // Portfolio Filters Logic
    const filterBtns = document.querySelectorAll('.filter-btn');
    const galleryItems = document.querySelectorAll('.gallery-item');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            filterBtns.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            btn.classList.add('active');

            const filterValue = btn.getAttribute('data-filter');

            galleryItems.forEach(item => {
                if (filterValue === 'all' || item.getAttribute('data-category') === filterValue) {
                    item.classList.remove('hide');
                    // Small delay to allow display:block to apply before animating opacity
                    setTimeout(() => {
                        item.style.opacity = "1";
                        item.style.transform = "translateY(0)";
                    }, 50);
                } else {
                    item.classList.add('hide');
                    item.style.opacity = "0";
                }
            });
        });
    });

    // Before/After Slider Logic
    const sliderControl = document.getElementById('sliderControl');
    const beforeWrapper = document.getElementById('beforeWrapper');
    const sliderLine = document.getElementById('sliderLine');
    const sliderButton = document.getElementById('sliderButton');

    if (sliderControl) {
        sliderControl.addEventListener('input', (e) => {
            const sliderValue = e.target.value;
            beforeWrapper.style.width = `${sliderValue}%`;
            sliderLine.style.left = `${sliderValue}%`;
            sliderButton.style.left = `${sliderValue}%`;
        });
    }

    // Pricing Calculator Logic
    const budgetRange = document.getElementById('budgetRange');
    const budgetDisplay = document.getElementById('budgetDisplay');
    const estimateTotal = document.getElementById('estimateTotal');
    const toggles = [
        document.getElementById('srvLogo'),
        document.getElementById('srvPhoto'),
        document.getElementById('srvSignage')
    ];

    function calculateEstimate() {
        if (!budgetRange) return;
        let baseBudget = parseInt(budgetRange.value);
        let addOns = 0;
        
        toggles.forEach(toggle => {
            if (toggle && toggle.checked) {
                addOns += parseInt(toggle.value);
            }
        });

        let total = baseBudget + addOns;
        budgetDisplay.textContent = `₹${baseBudget.toLocaleString()}`;
        estimateTotal.textContent = `₹${total.toLocaleString()}`;
    }

    if (budgetRange) {
        budgetRange.addEventListener('input', calculateEstimate);
        toggles.forEach(toggle => {
            if (toggle) toggle.addEventListener('change', calculateEstimate);
        });
        // Initial Calculation
        calculateEstimate();
    }

    // FAQ Accordion Logic
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');
        
        question.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            
            // Close all other FAQs
            faqItems.forEach(otherItem => {
                otherItem.classList.remove('active');
                otherItem.querySelector('.faq-answer').style.maxHeight = null;
            });

            // Toggle current FAQ
            if (!isActive) {
                item.classList.add('active');
                answer.style.maxHeight = answer.scrollHeight + "px";
            }
        });
    });

    // Project Planner Modal Logic
    const plannerModal = document.getElementById('plannerModal');
    const openPlannerBtn = document.getElementById('openPlannerBtn');
    const closePlannerBtn = document.getElementById('closePlannerBtn');
    const plannerForm = document.getElementById('plannerForm');

    if (openPlannerBtn && plannerModal) {
        openPlannerBtn.addEventListener('click', (e) => {
            e.preventDefault();
            plannerModal.classList.add('active');
        });

        closePlannerBtn.addEventListener('click', () => {
            plannerModal.classList.remove('active');
        });

        // Close on outside click
        window.addEventListener('click', (e) => {
            if (e.target === plannerModal) {
                plannerModal.classList.remove('active');
            }
        });

        plannerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const submitBtn = plannerForm.querySelector('button[type="submit"]');
            submitBtn.textContent = 'Estimating...';
            submitBtn.disabled = true;
            
            const projectType = document.getElementById('modalProjectType').value;
            const details = document.getElementById('modalDetails').value;
            const timeline = document.getElementById('modalTimeline').value;
            
            const fullDetails = details + " | Timeline: " + timeline;
            
            fetch('/api/order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    service: projectType,
                    details: fullDetails
                })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message || "Thank you! Your estimate request has been received. We will contact you shortly.");
                plannerForm.reset();
                submitBtn.textContent = 'Request Estimate';
                submitBtn.disabled = false;
                plannerModal.classList.remove('active');
            })
            .catch(error => {
                alert("Something went wrong. Please try again.");
                submitBtn.textContent = 'Request Estimate';
                submitBtn.disabled = false;
            });
        });
    }

    // Lightbox Gallery Logic
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightboxImg');
    const lightboxCaption = document.getElementById('lightboxCaption');
    const closeLightbox = document.querySelector('.close-lightbox');
    const prevLightbox = document.querySelector('.prev-lightbox');
    const nextLightbox = document.querySelector('.next-lightbox');
    
    let currentFilteredItems = [];
    let currentIndex = 0;

    if (lightbox) {
        galleryItems.forEach(item => {
            item.addEventListener('click', () => {
                // Update current filtered items based on visibility
                currentFilteredItems = Array.from(galleryItems).filter(el => !el.classList.contains('hide'));
                currentIndex = currentFilteredItems.indexOf(item);
                
                showLightboxImage(currentIndex);
                lightbox.style.display = 'block';
            });
        });

        const showLightboxImage = (index) => {
            if (currentFilteredItems.length > 0) {
                const item = currentFilteredItems[index];
                const img = item.querySelector('img');
                const title = item.querySelector('h3').textContent;
                const category = item.querySelector('p').textContent;
                
                lightboxImg.src = img.src;
                lightboxCaption.innerHTML = `<strong>${title}</strong><br>${category}`;
            }
        };

        closeLightbox.addEventListener('click', () => {
            lightbox.style.display = 'none';
        });

        window.addEventListener('click', (e) => {
            if (e.target === lightbox) {
                lightbox.style.display = 'none';
            }
        });

        prevLightbox.addEventListener('click', () => {
            currentIndex = (currentIndex > 0) ? currentIndex - 1 : currentFilteredItems.length - 1;
            showLightboxImage(currentIndex);
        });

        nextLightbox.addEventListener('click', () => {
            currentIndex = (currentIndex < currentFilteredItems.length - 1) ? currentIndex + 1 : 0;
            showLightboxImage(currentIndex);
        });
    }
});

// Gallery Modal Logic
function openGalleryModal(element) {
    const title = element.getAttribute('data-title');
    const category = element.getAttribute('data-category');
    const image = element.getAttribute('data-image');
    const process = element.getAttribute('data-process');

    document.getElementById('modalTitle').innerText = title;
    document.getElementById('modalCategory').innerText = category;
    document.getElementById('modalImage').src = image;
    document.getElementById('modalProcess').innerText = process;

    const modal = document.getElementById('galleryModal');
    modal.style.display = 'flex';
}

function closeGalleryModal() {
    const modal = document.getElementById('galleryModal');
    modal.style.display = 'none';
}

// Close modal when clicking outside of it
window.addEventListener('click', function(event) {
    const modal = document.getElementById('galleryModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});
