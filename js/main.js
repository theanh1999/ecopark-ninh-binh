document.addEventListener('DOMContentLoaded', () => {
    // Noindex for non-primary domains (workers.dev, pages.dev)
    if (window.location.hostname !== 'ecoparkninhbinh.org' && window.location.hostname !== 'www.ecoparkninhbinh.org') {
        const meta = document.querySelector('meta[name="robots"]');
        if (meta) meta.setAttribute('content', 'noindex, nofollow');
    }

    // AOS — Animate On Scroll
    if (typeof AOS !== 'undefined') AOS.init({ duration: 800, easing: 'ease-out-cubic', once: true, offset: 60 });

    // GLightbox — Gallery lightbox
    if (typeof GLightbox !== 'undefined') GLightbox({ selector: '.glightbox', touchNavigation: true, loop: true });

    // Navbar scroll effect
    const navbar = document.getElementById('navbar');
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                const scrolled = window.scrollY > 60;
                navbar.classList.toggle('scrolled', scrolled);
                document.getElementById('backToTop').classList.toggle('visible', window.scrollY > 500);
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });

    // Back to top
    document.getElementById('backToTop').addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', function(e) {
            e.preventDefault();
            const t = document.querySelector(this.getAttribute('href'));
            if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' });
            const c = document.getElementById('navMenu');
            if (c && c.classList.contains('show') && typeof bootstrap !== 'undefined') {
                bootstrap.Collapse.getInstance(c)?.hide();
            }
        });
    });

    // Counter animation with IntersectionObserver
    const counters = document.querySelectorAll('.counter-number');
    const cObs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target, target = parseInt(el.dataset.target);
                let cur = 0;
                const step = target / 125;
                const timer = setInterval(() => {
                    cur += step;
                    if (cur >= target) { cur = target; clearInterval(timer); }
                    el.textContent = Math.floor(cur).toLocaleString('vi-VN');
                }, 16);
                cObs.unobserve(el);
            }
        });
    }, { threshold: 0.5 });
    counters.forEach(c => cObs.observe(c));

    // Lazy load images with IntersectionObserver
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    if ('IntersectionObserver' in window) {
        const imgObs = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    img.classList.add('loaded');
                    imgObs.unobserve(img);
                }
            });
        }, { rootMargin: '200px' });
        lazyImages.forEach(img => imgObs.observe(img));
    }

    // Form — EmailJS
    const EMAILJS_PK = 'YOUR_PUBLIC_KEY', EMAILJS_SID = 'YOUR_SERVICE_ID', EMAILJS_TID = 'YOUR_TEMPLATE_ID';
    if (typeof emailjs !== 'undefined' && EMAILJS_PK !== 'YOUR_PUBLIC_KEY') emailjs.init(EMAILJS_PK);

    const form = document.getElementById('contactForm');
    const formSuccess = document.getElementById('formSuccess');
    const submitBtn = document.getElementById('submitBtn');

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const n = document.getElementById('name').value.trim();
        const p = document.getElementById('phone').value.trim();
        if (!n || !p) { alert('Vui lòng nhập đầy đủ họ tên và số điện thoại.'); return; }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang gửi...';

        const params = {
            from_name: n,
            phone: p,
            email: document.getElementById('email').value.trim() || 'N/A',
            product: document.getElementById('product').value || 'N/A',
            message: document.getElementById('message').value.trim() || 'N/A',
            to_email: 'Huyentrangbkit@gmail.com'
        };

        if (EMAILJS_PK === 'YOUR_PUBLIC_KEY') {
            const body = `Họ tên: ${params.from_name}%0ASDT: ${params.phone}%0AEmail: ${params.email}%0ASP: ${params.product}%0ANhắn: ${params.message}`;
            window.open(`mailto:Huyentrangbkit@gmail.com?subject=[Ecopark NB] Khách: ${params.from_name}&body=${body}`, '_blank');
            form.style.display = 'none';
            formSuccess.classList.add('show');
            return;
        }

        emailjs.send(EMAILJS_SID, EMAILJS_TID, params)
            .then(() => { form.style.display = 'none'; formSuccess.classList.add('show'); })
            .catch(() => {
                alert('Có lỗi. Vui lòng gọi 0966 271 887.');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Gửi đăng ký tư vấn';
            });
    });
});
