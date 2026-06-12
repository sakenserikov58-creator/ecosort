/* ═══════════════════════════════════════════════
   EcoLife — Animations & Interactivity
   ═══════════════════════════════════════════════ */

// ─── Утилиты ─────────────────────────────────
function esc(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ─── Данные пунктов приёма ────────────────────
const stations = [
  { name: "EcoPoint Mega", city: "Алматы", address: "ул. Розыбакиева, 247А",
    types: ["Пластик", "Бумага", "Батарейки"], lat: 43.2029, lng: 76.8926, x: 30, y: 35 },
  { name: "Green Hub Dostyk", city: "Алматы", address: "пр. Достык, 91",
    types: ["Стекло", "Металл", "Пластик"], lat: 43.2421, lng: 76.9577, x: 57, y: 27 },
  { name: "Recycle Center Expo", city: "Астана", address: "пр. Кабанбай Батыра, 53",
    types: ["Пластик", "Бумага", "Стекло", "Металл"], lat: 51.0907, lng: 71.4180, x: 68, y: 62 },
  { name: "Battery Box Khan Shatyr", city: "Астана", address: "пр. Туран, 37",
    types: ["Батарейки", "Электроника"], lat: 51.1320, lng: 71.4037, x: 42, y: 68 },
  { name: "Qyzylorda EcoBox", city: "Кызылорда", address: "ул. Коркыт Ата, 12",
    types: ["Пластик", "Бумага", "Батарейки"], lat: 44.8488, lng: 65.4823, x: 24, y: 74 },
  { name: "Clean Step Station", city: "Кызылорда", address: "мкр. Шугыла, 18",
    types: ["Стекло", "Металл"], lat: 44.8231, lng: 65.5177, x: 78, y: 41 },
];

/* ═══════════════════════════════════════════════
   1. INTRO LOADER
   Анимация загрузки при первом посещении,
   как на bluemarinefoundation.com
   ═══════════════════════════════════════════════ */
function setupIntroLoader() {
  // Показываем лоадер только если пользователь ещё не видел его в этой сессии
  if (sessionStorage.getItem("ecolife_loaded")) return;

  const loaderHTML = `
    <div id="intro-loader">
      <div class="loader-label">Инициализация системы</div>
      <div class="loader-brand">Eco<span>Sort</span></div>
      <div class="loader-bar-wrap"><div class="loader-bar" id="loaderBar"></div></div>
      <div class="loader-status" id="loaderStatus">Подключение...</div>
    </div>
  `;
  document.body.insertAdjacentHTML("afterbegin", loaderHTML);

  const bar    = document.getElementById("loaderBar");
  const status = document.getElementById("loaderStatus");
  const loader = document.getElementById("intro-loader");

  const steps = [
    { pct: 20, msg: "Загрузка базы данных..." },
    { pct: 45, msg: "Получение данных о пунктах приёма..." },
    { pct: 70, msg: "Инициализация карты..." },
    { pct: 90, msg: "Подготовка интерфейса..." },
    { pct: 100, msg: "Соединение установлено ✓" },
  ];

  let i = 0;
  function nextStep() {
    if (i >= steps.length) {
      setTimeout(() => {
        loader.classList.add("hide");
        setTimeout(() => loader.remove(), 800);
      }, 400);
      return;
    }
    const step = steps[i++];
    bar.style.width = step.pct + "%";
    status.textContent = step.msg;
    setTimeout(nextStep, i < steps.length ? 280 : 500);
  }

  // Небольшая пауза, потом запускаем
  setTimeout(nextStep, 200);
  sessionStorage.setItem("ecolife_loaded", "1");
}

/* ═══════════════════════════════════════════════
   2. PARALLAX ГЕРОЙ
   Фон движется медленнее при скролле
   ═══════════════════════════════════════════════ */
function setupParallax() {
  const bg = document.querySelector(".hero-bg");
  if (!bg) return;

  let ticking = false;
  window.addEventListener("scroll", () => {
    if (ticking) return;
    requestAnimationFrame(() => {
      const y = window.scrollY;
      bg.style.transform = `translateY(${y * 0.38}px)`;
      ticking = false;
    });
    ticking = true;
  }, { passive: true });
}

/* ═══════════════════════════════════════════════
   3. REVEAL при скролле (все типы)
   ═══════════════════════════════════════════════ */
function setupReveal() {
  const selectors = [".reveal", ".reveal-left", ".reveal-right", ".reveal-scale", ".glow-line"];
  const items = document.querySelectorAll(selectors.join(","));

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const el = entry.target;

      // Stagger для элементов внутри .reveal-grid
      const parent = el.closest(".reveal-grid");
      if (parent) {
        const siblings = [...parent.querySelectorAll(".reveal")];
        const idx = siblings.indexOf(el);
        el.style.transitionDelay = (idx * 0.07) + "s";
      }

      el.classList.add("is-visible");
      observer.unobserve(el);
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });

  items.forEach((item) => observer.observe(item));
}

/* ═══════════════════════════════════════════════
   4. SPLIT-TEXT АНИМАЦИЯ
   Заголовки разбиваются по словам — каждое
   слово появляется с задержкой (как на BMF)
   ═══════════════════════════════════════════════ */
function setupSplitText() {
  const targets = document.querySelectorAll("[data-split]");

  targets.forEach((el) => {
    const words = el.textContent.trim().split(/\s+/);
    el.innerHTML = words.map((w, i) =>
      `<span class="split-word" style="transition-delay:${i * 0.08}s">${w}</span>`
    ).join(" ");
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.querySelectorAll(".split-word").forEach((w) => {
        w.classList.add("is-visible");
      });
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.2 });

  targets.forEach((el) => observer.observe(el));
}

/* ═══════════════════════════════════════════════
   5. СЧЁТЧИКИ
   Числа анимированно считают до цели
   ═══════════════════════════════════════════════ */
function setupCounters() {
  const counters = document.querySelectorAll("[data-counter]");

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const target = Number(el.dataset.counter);
      if (!Number.isFinite(target)) return;

      let start = null;
      const duration = 1600;

      function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

      function tick(timestamp) {
        if (!start) start = timestamp;
        const progress = Math.min((timestamp - start) / duration, 1);
        el.textContent = Math.round(easeOut(progress) * target).toLocaleString("ru-RU");
        if (progress < 1) requestAnimationFrame(tick);
        else el.textContent = target.toLocaleString("ru-RU");
      }

      requestAnimationFrame(tick);
      observer.unobserve(el);
    });
  }, { threshold: 0.4 });

  counters.forEach((c) => observer.observe(c));
}

/* ═══════════════════════════════════════════════
   6. TOAST УВЕДОМЛЕНИЯ
   Зелёное уведомление исчезает через 4 сек
   ═══════════════════════════════════════════════ */
function setupToast() {
  const toast = document.querySelector(".toast");
  if (!toast) return;
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(-14px) scale(0.95)";
    toast.style.transition = "opacity 0.5s ease, transform 0.5s ease";
    setTimeout(() => toast.remove(), 600);
  }, 4000);
}

/* ═══════════════════════════════════════════════
   7. МОБИЛЬНОЕ МЕНЮ
   ═══════════════════════════════════════════════ */
function setupMenu() {
  const button = document.querySelector("[data-menu-button]");
  if (!button) return;

  button.addEventListener("click", () => {
    document.body.classList.toggle("is-menu-open");
    button.textContent = document.body.classList.contains("is-menu-open") ? "✕" : "☰";
  });

  // Закрываем меню при клике вне
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".site-header")) {
      document.body.classList.remove("is-menu-open");
      button.textContent = "☰";
    }
  });
}

/* ═══════════════════════════════════════════════
   8. КАРТА
   Leaflet или CSS-фолбэк
   ═══════════════════════════════════════════════ */
function setupMap() {
  const board      = document.querySelector("[data-map-board]");
  const list       = document.querySelector("[data-station-list]");
  const cityFilter = document.querySelector("[data-city-filter]");
  const typeFilters = [...document.querySelectorAll("[data-type-filter]")];
  if (!board || !list || !cityFilter) return;

  let map = null;
  let markerLayer = null;

  if (window.L) {
    // Тёмная тема для Leaflet
    map = L.map(board, { scrollWheelZoom: true, zoomControl: true })
           .setView([47.9, 67.3], 5);

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap &copy; CARTO",
    }).addTo(map);

    markerLayer = L.layerGroup().addTo(map);
  } else {
    board.classList.add("map-board");
  }

  // Кастомная иконка маркера
  const customIcon = window.L ? L.divIcon({
    className: "",
    html: `<div style="
      width:30px;height:30px;
      background:var(--accent,#32F86D);
      border:3px solid rgba(50,248,109,0.35);
      border-radius:50%;
      box-shadow:0 0 16px rgba(50,248,109,0.5);
      display:grid;place-items:center;
      color:#002E2A;font-weight:900;font-size:12px;
    "></div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  }) : null;

  function activeTypes() {
    return typeFilters.filter((i) => i.checked).map((i) => i.value);
  }

  function render() {
    const city  = cityFilter.value;
    const types = activeTypes();
    const visible = stations.filter((s) => {
      const cityMatch = city === "all" || s.city === city;
      const typeMatch = s.types.some((t) => types.includes(t));
      return cityMatch && typeMatch;
    });

    if (map && markerLayer) {
      markerLayer.clearLayers();
      visible.forEach((s) => {
        const marker = customIcon
          ? L.marker([s.lat, s.lng], { icon: customIcon })
          : L.marker([s.lat, s.lng]);
        marker.addTo(markerLayer).bindPopup(`
          <strong>${esc(s.name)}</strong><br>
          ${esc(s.city)}, ${esc(s.address)}<br>
          <span style="color:#32F86D">${esc(s.types.join(", "))}</span>
        `);
      });
      if (visible.length) {
        const bounds = L.latLngBounds(visible.map((s) => [s.lat, s.lng]));
        map.fitBounds(bounds.pad(0.25));
      }
    } else {
      board.innerHTML = visible.map((s, i) => `
        <button class="map-marker" style="left:${s.x}%;top:${s.y}%;" title="${esc(s.name)}">
          ${i + 1}
        </button>
      `).join("");
    }

    list.innerHTML = visible.length
      ? visible.map((s) => `
          <article class="station-card">
            <h3>${esc(s.name)}</h3>
            <p>${esc(s.city)}, ${esc(s.address)}</p>
            <p style="color:var(--accent);font-weight:700;font-size:12px;margin-top:6px">${esc(s.types.join(" · "))}</p>
          </article>
        `).join("")
      : `<article class="station-card"><h3>Пункты не найдены</h3><p>Измените фильтры поиска.</p></article>`;
  }

  cityFilter.addEventListener("change", render);
  typeFilters.forEach((i) => i.addEventListener("change", render));
  render();
}

/* ═══════════════════════════════════════════════
   9. ГЛОУ-ЛИНИИ
   Анимированные разделительные линии
   ═══════════════════════════════════════════════ */
function setupGlowLines() {
  document.querySelectorAll(".section-head").forEach((head) => {
    // Добавляем линию после eyebrow
    const eyebrow = head.querySelector(".eyebrow");
    if (!eyebrow) return;
    const line = document.createElement("span");
    line.className = "glow-line";
    line.style.width = "80px";
    line.style.marginTop = "12px";
    line.style.marginBottom = "8px";
    eyebrow.insertAdjacentElement("afterend", line);
  });
}

/* ═══════════════════════════════════════════════
   10. HOVER-ГОУ на карточках — добавляем
   лёгкое свечение при наведении (JS усиливает CSS)
   ═══════════════════════════════════════════════ */
function setupCardGlow() {
  // Карточки БЕЗ фонового фото — меняем background напрямую
  const plainCards = document.querySelectorAll(".impact-card, .admin-stats article");
  plainCards.forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width)  * 100;
      const y = ((e.clientY - rect.top)  / rect.height) * 100;
      card.style.background = `radial-gradient(circle at ${x}% ${y}%, rgba(50,248,109,0.09) 0%, var(--surface2) 65%)`;
    });
    card.addEventListener("mouseleave", () => {
      card.style.background = "";
    });
  });

  // Карточки акций — у них background-image (фото), поэтому используем
  // отдельный overlay-div, чтобы не затирать фото
  document.querySelectorAll(".event-card").forEach((card) => {
    // Создаём невидимый overlay для эффекта свечения курсора
    const overlay = document.createElement("div");
    overlay.className = "event-glow-overlay";
    card.appendChild(overlay);

    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width)  * 100;
      const y = ((e.clientY - rect.top)  / rect.height) * 100;
      overlay.style.background = `radial-gradient(circle at ${x}% ${y}%, rgba(50,248,109,0.18) 0%, transparent 65%)`;
      overlay.style.opacity = "1";
    });

    card.addEventListener("mouseleave", () => {
      overlay.style.opacity = "0";
    });
  });
}

/* ═══════════════════════════════════════════════
   11. API ПИНГ
   ═══════════════════════════════════════════════ */
async function setupApiPing() {
  try {
    const res = await fetch("/api/stats", { headers: { Accept: "application/json" } });
    if (!res.ok) return;
    const stats = await res.json();
    document.documentElement.dataset.apiReady = "true";
    document.documentElement.dataset.users  = stats.users;
    document.documentElement.dataset.events = stats.events;
  } catch {
    document.documentElement.dataset.apiReady = "false";
  }
}

/* ═══════════════════════════════════════════════
   12. ДОБАВЛЯЕМ REVEAL-КЛАССЫ К HTML
   Назначаем анимации конкретным блокам:
   героические элементы, грид-карточки и т.д.
   ═══════════════════════════════════════════════ */
function assignAnimationClasses() {
  // Гриды получают класс reveal-grid для stagger
  document.querySelectorAll(
    ".role-grid, .process-grid, .feature-grid, .impact-grid, .info-grid, .compact-grid, .event-grid, .response-grid"
  ).forEach((g) => g.classList.add("reveal-grid"));

  // Заголовки героя — split-text
  const heroH1 = document.querySelector(".hero h1");
  if (heroH1) heroH1.dataset.split = "true";

  // Подзаголовки секций — split-text
  document.querySelectorAll(".section h2").forEach((h) => {
    h.dataset.split = "true";
  });

  // Добавляем reveal-left для левых колонок two-col
  document.querySelectorAll(".two-col > *:first-child").forEach((el) => {
    if (!el.classList.contains("reveal")) {
      el.classList.add("reveal-left");
    }
  });

  // Добавляем reveal-right для правых колонок two-col
  document.querySelectorAll(".two-col > *:last-child").forEach((el) => {
    if (!el.classList.contains("reveal")) {
      el.classList.add("reveal-right");
    }
  });
}

/* ═══════════════════════════════════════════════
   13. ДОБАВЛЯЕМ HERO-BG DIV для параллакса
   и цветные орбы
   ═══════════════════════════════════════════════ */
function setupHeroElements() {
  const hero = document.querySelector(".hero");
  if (!hero) return;

  // Переносим фоновое изображение в отдельный div
  const bg = document.createElement("div");
  bg.className = "hero-bg";
  hero.prepend(bg);

  // Добавляем анимированные орбы
  const orb1 = document.createElement("div");
  orb1.className = "hero-orb hero-orb-1";
  hero.prepend(orb1);

  const orb2 = document.createElement("div");
  orb2.className = "hero-orb hero-orb-2";
  hero.prepend(orb2);
}

/* ═══════════════════════════════════════════════
   ЗАПУСК
   ═══════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {
  setupIntroLoader();
  setupHeroElements();
  assignAnimationClasses();
  setupGlowLines();
  setupReveal();
  setupSplitText();
  setupCounters();
  setupToast();
  setupMenu();
  setupMap();
  setupCardGlow();
  setupParallax();
  setupApiPing();
});
