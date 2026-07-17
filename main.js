// ---------- تفاعلات مشتركة عبر كل الصفحات ----------

document.addEventListener("DOMContentLoaded", () => {
  injectHeaderFooter();
  initTiltCards();
  initMobileNav();
  initHeaderScroll();
});

function initHeaderScroll() {
  const header = document.querySelector("header.site-header");
  if (!header) return;
  window.addEventListener("scroll", () => {
    header.classList.toggle("scrolled", window.scrollY > 8);
  }, { passive: true });
}

// يضيف أيقونة صغيرة تشير إلى أن الصورة قابلة للتدوير التفاعلي (عند وجود أكثر من صورة واحدة)
function addRotateIndicators() {
  document.querySelectorAll(".thumb-wrap, .pd-main").forEach((el) => {
    if (el.querySelector(".rotate-indicator")) return;
    const raw = el.dataset.images;
    const count = raw ? JSON.parse(raw).length : el.querySelectorAll("img").length;
    if (count > 1) {
      const icon = document.createElement("div");
      icon.className = "rotate-indicator";
      icon.innerHTML = "↔";
      icon.title = "حرّك الماوس لتدوير المنتج";
      el.appendChild(icon);
    }
  });
}

function injectHeaderFooter() {
  const headerEl = document.getElementById("site-header");
  const footerEl = document.getElementById("site-footer");
  const current = document.body.dataset.page || "";

  if (headerEl) {
    headerEl.innerHTML = `
      <div class="topbar">
        <div class="container">
          <div class="tb-links">
            <a href="tel:0552420934">📞 0552 42 09 34</a>
            <a href="tel:0671946690">📞 0671 94 66 90</a>
          </div>
          <div class="tb-links">
            <span>باتنة، طريق عين التوتة — توصيل و تركيب عبر كامل الوطن</span>
          </div>
        </div>
      </div>
      <header class="site-header">
        <div class="container nav-row">
          <a href="index.html" class="logo">
            <img src="img/logo.png" alt="أثاث الثقة باتنة 05">
            <small>Meuble Confiance — باتنة 05</small>
          </a>
          <nav class="main-nav">
            <a href="index.html" class="${current === "home" ? "active" : ""}">الرئيسية</a>
            <a href="catalogue.html" class="${current === "catalogue" ? "active" : ""}">الكتالوج</a>
            <a href="catalogue.html?cat=صالونات">صالونات</a>
            <a href="catalogue.html?cat=غرف نوم">غرف نوم</a>
            <a href="index.html#contact">اتصل بنا</a>
          </nav>
          <div class="nav-actions">
            <a href="tel:0671946690" class="btn-call">
              📞 <span class="long">اطلب الآن</span>
            </a>
            <button class="burger" id="burgerBtn" aria-label="القائمة">
              <span></span><span></span><span></span>
            </button>
          </div>
        </div>
        <div id="mobileNav" style="display:none; border-top:1px solid var(--line); padding:16px 24px;">
          <a href="index.html" style="display:block; padding:10px 0;">الرئيسية</a>
          <a href="catalogue.html" style="display:block; padding:10px 0;">الكتالوج الكامل</a>
          <a href="catalogue.html?cat=صالونات" style="display:block; padding:10px 0;">صالونات</a>
          <a href="catalogue.html?cat=غرف نوم" style="display:block; padding:10px 0;">غرف نوم</a>
          <a href="catalogue.html?cat=مطابخ" style="display:block; padding:10px 0;">مطابخ</a>
        </div>
      </header>
    `;
  }

  if (footerEl) {
    footerEl.innerHTML = `
      <footer id="contact">
        <div class="container">
          <div class="foot-grid">
            <div>
              <div class="foot-logo"><img src="img/logo.png" alt="أثاث الثقة باتنة 05"></div>
              <p>شركة جزائرية مختصة في صناعة وبيع كل أنواع الأثاث المنزلي: صالونات، غرف نوم، طاولات وديكور، بخبرة تمتد عبر آلاف العملاء الراضين في كامل الوطن.</p>
              <div class="social-row">
                <a href="https://www.facebook.com/Meuble.Confiance.Batna.05/" target="_blank" rel="noopener" aria-label="فيسبوك">f</a>
                <a href="https://www.instagram.com/meuble.confiance.batna/" target="_blank" rel="noopener" aria-label="انستغرام">◎</a>
              </div>
            </div>
            <div>
              <h4>روابط سريعة</h4>
              <a href="index.html">الرئيسية</a>
              <a href="catalogue.html">الكتالوج</a>
              <a href="index.html#categories">التصنيفات</a>
            </div>
            <div>
              <h4>خدمة العملاء</h4>
              <a href="tel:0552420934">0552 42 09 34 — صالونات وغرف نوم</a>
              <a href="tel:0671946690">0671 94 66 90 — طاولات</a>
              <a href="tel:0557580951">0557 58 09 51 — ديكور</a>
              <a href="#">الدفع عند الاستلام</a>
            </div>
            <div>
              <h4>معلومات</h4>
              <p>طريق عين التوتة، مقابل عمارات برالة، قاعة حفلات بن يحي سابقاً — باتنة</p>
              <p>مفتوح كل الأيام</p>
              <a href="https://www.ethikameuble.com" target="_blank" rel="noopener">www.ethikameuble.com</a>
            </div>
          </div>
          <div class="foot-bottom">
            <span>© 2026 أثاث الثقة باتنة 05 — جميع الحقوق محفوظة</span>
            <span>موقع تجريبي — بعض الصور للعرض فقط</span>
          </div>
        </div>
      </footer>
    `;
  }

  const waFloat = document.createElement("a");
  waFloat.href = "https://wa.me/213671946690";
  waFloat.target = "_blank";
  waFloat.rel = "noopener";
  waFloat.className = "wa-float";
  waFloat.setAttribute("aria-label", "تواصل عبر واتساب");
  waFloat.innerHTML = `<svg width="26" height="26" viewBox="0 0 24 24" fill="white"><path d="M12 2C6.5 2 2 6.5 2 12c0 1.85.5 3.58 1.36 5.08L2 22l5.06-1.33A9.94 9.94 0 0 0 12 22c5.5 0 10-4.5 10-10S17.5 2 12 2zm5.2 14.2c-.22.62-1.28 1.18-1.76 1.24-.45.06-1.02.08-1.65-.1-.38-.11-.87-.28-1.5-.55-2.64-1.14-4.36-3.8-4.5-3.98-.13-.18-1.08-1.44-1.08-2.74 0-1.3.68-1.94.92-2.2.24-.26.53-.32.7-.32.18 0 .35 0 .5.01.16.01.38-.06.6.46.22.53.75 1.83.82 1.96.07.13.11.28.02.46-.09.18-.13.28-.26.43-.13.15-.27.34-.39.46-.13.13-.26.27-.11.53.15.26.68 1.12 1.46 1.82 1 .89 1.85 1.17 2.11 1.3.26.13.41.11.56-.07.15-.18.64-.75.81-1.01.17-.26.34-.21.57-.13.23.09 1.47.69 1.72.82.25.13.42.19.48.3.06.11.06.62-.16 1.24z"/></svg>`;
  document.body.appendChild(waFloat);
}

function initMobileNav() {
  const btn = document.getElementById("burgerBtn");
  const nav = document.getElementById("mobileNav");
  if (!btn || !nav) return;
  btn.addEventListener("click", () => {
    nav.style.display = nav.style.display === "none" ? "block" : "none";
  });
}

// تكبير خفيف ومسطح عند المرور فوق البطاقة (بدون إمالة ثلاثية الأبعاد، تصميم مسطح)
function initTiltCards() {
  document.querySelectorAll(".tilt-card, .product-card .thumb-wrap").forEach((card) => {
    card.style.transition = "transform .3s ease";
  });
}

// معرض دوّار: يبدّل بين صور المنتج حسب موضع الماوس الأفقي لمحاكاة الدوران
function initRotateGallery(el, images, dotsEl) {
  const imgs = el.querySelectorAll("img");
  let current = 0;
  const setActive = (i) => {
    imgs.forEach((im, idx) => im.classList.toggle("active", idx === i));
    if (dotsEl) {
      dotsEl.querySelectorAll("span").forEach((d, idx) => d.classList.toggle("active", idx === i));
    }
    current = i;
  };
  el.addEventListener("mousemove", (e) => {
    const rect = el.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    const idx = Math.min(imgs.length - 1, Math.max(0, Math.floor(ratio * imgs.length)));
    if (idx !== current) setActive(idx);
  });
  el.addEventListener("mouseleave", () => setActive(0));
  return { setActive };
}
