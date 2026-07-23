document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Navbar Toggle
    const menuToggle = document.getElementById('menu-toggle');
    const navMenu = document.getElementById('nav-menu');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            const icon = menuToggle.querySelector('i');
            if (navMenu.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });

        // Close menu when clicking a link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                const icon = menuToggle.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            });
        });
    }

    // 2. Smooth Scrolling for Anchor Links & Active Nav Highlight
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // 3. Stats Counter Animation on Scroll
    const statNumbers = document.querySelectorAll('.stat-number');
    let animatedStats = false;

    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !animatedStats) {
                animatedStats = true;
                statNumbers.forEach(stat => {
                    const target = parseInt(stat.getAttribute('data-target'), 10);
                    let count = 0;
                    const increment = Math.ceil(target / 40);
                    const timer = setInterval(() => {
                        count += increment;
                        if (count >= target) {
                            stat.textContent = target + (target === 100 ? '%' : '+');
                            clearInterval(timer);
                        } else {
                            stat.textContent = count;
                        }
                    }, 40);
                });
            }
        });
    }, { threshold: 0.5 });

    const statsSection = document.querySelector('.stats-section');
    if (statsSection) {
        statsObserver.observe(statsSection);
    }

    // 4. Portfolio Category Filtering
    const filterBtns = document.querySelectorAll('.filter-btn');
    const galleryItems = document.querySelectorAll('.gallery-item');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const filter = btn.getAttribute('data-filter');

            galleryItems.forEach(item => {
                const category = item.getAttribute('data-category');
                if (filter === 'all' || category === filter) {
                    item.classList.remove('hide');
                    item.style.opacity = '1';
                    item.style.transform = 'scale(1)';
                } else {
                    item.classList.add('hide');
                    item.style.opacity = '0';
                    item.style.transform = 'scale(0.8)';
                }
            });
        });
    });

    // 5. FAQ Accordion Toggle
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const questionBtn = item.querySelector('.faq-question');
        questionBtn.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            
            // Close all FAQ items
            faqItems.forEach(i => i.classList.remove('active'));
            
            // If wasn't active, open it
            if (!isActive) {
                item.classList.add('active');
            }
        });
    });

    // 6. Element Scroll Fade-in Observer
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    const animatedElements = document.querySelectorAll('.service-card, .gallery-item, .order-box, .info-card, .contact-form-card, .testimonial-card, .ba-card');
    
    animatedElements.forEach((el, index) => {
        el.style.opacity = "0";
        el.style.transform = "translateY(30px)";
        el.style.transition = `opacity 0.6s ease ${index * 0.08}s, transform 0.6s ease ${index * 0.08}s, box-shadow 0.3s ease, border-color 0.3s ease`;
        observer.observe(el);
    });

    // 7. Interactive Quote Calculator
    const serviceSelect = document.getElementById('quote-service');
    const sizeInput = document.getElementById('quote-size');
    const sizeGroup = document.getElementById('size-group');
    const priceDisplay = document.getElementById('estimated-price');
    const whatsappBtn = document.getElementById('send-whatsapp-quote');

    function calculatePrice() {
        if (!serviceSelect || !priceDisplay) return;

        const selectedOption = serviceSelect.options[serviceSelect.selectedIndex];
        const rate = parseFloat(selectedOption.getAttribute('data-rate')) || 0;
        const isFixed = selectedOption.getAttribute('data-fixed') === 'true';

        if (isFixed) {
            if (sizeGroup) sizeGroup.style.display = 'none';
            priceDisplay.textContent = `₹${rate.toLocaleString('en-IN')}`;
        } else {
            if (sizeGroup) sizeGroup.style.display = 'block';
            const size = parseFloat(sizeInput.value) || 0;
            const total = Math.round(rate * size);
            priceDisplay.textContent = `₹${total.toLocaleString('en-IN')}`;
        }
    }

    if (serviceSelect && sizeInput) {
        serviceSelect.addEventListener('change', calculatePrice);
        sizeInput.addEventListener('input', calculatePrice);
        calculatePrice();
    }

    if (whatsappBtn && serviceSelect) {
        whatsappBtn.addEventListener('click', () => {
            const selectedOption = serviceSelect.options[serviceSelect.selectedIndex];
            const serviceName = selectedOption.textContent.split('(')[0].trim();
            const isFixed = selectedOption.getAttribute('data-fixed') === 'true';
            const finalPrice = priceDisplay ? priceDisplay.textContent : '';
            
            let message = `Hello Chhatrapati Digital, I would like to place an order for:\n`;
            message += `• Service: ${serviceName}\n`;
            if (!isFixed && sizeInput) {
                message += `• Size/Area: ${sizeInput.value} sq. ft.\n`;
            }
            message += `• Estimated Price: ${finalPrice}\n\nPlease let me know the next steps!`;

            window.open(`https://wa.me/919876543210?text=${encodeURIComponent(message)}`, '_blank');
        });
    }

    // 8. Portfolio Lightbox Modal
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxCaption = document.getElementById('lightbox-caption');
    const lightboxClose = document.getElementById('lightbox-close');

    document.querySelectorAll('.gallery-item').forEach(item => {
        item.addEventListener('click', () => {
            const src = item.getAttribute('data-src') || item.querySelector('img').getAttribute('src');
            const caption = item.getAttribute('data-caption') || item.querySelector('span').textContent;

            if (lightbox && lightboxImg && lightboxCaption) {
                lightboxImg.src = src;
                lightboxCaption.textContent = caption;
                lightbox.classList.add('active');
            }
        });
    });

    if (lightboxClose) {
        lightboxClose.addEventListener('click', () => {
            lightbox.classList.remove('active');
        });
    }

    if (lightbox) {
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox) {
                lightbox.classList.remove('active');
            }
        });
    }

    // 9. Contact Form Submission Handler
    const inquiryForm = document.getElementById('inquiry-form');
    if (inquiryForm) {
        inquiryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = document.getElementById('contact-name').value;
            const phone = document.getElementById('contact-phone').value;
            const msg = document.getElementById('contact-message').value;

            let fullMsg = `New Website Inquiry:\n`;
            fullMsg += `• Name: ${name}\n`;
            fullMsg += `• Phone: ${phone}\n`;
            fullMsg += `• Requirements: ${msg}`;

            window.open(`https://wa.me/919876543210?text=${encodeURIComponent(fullMsg)}`, '_blank');
        });
    }
});
