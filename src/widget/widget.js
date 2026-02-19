/**
 * repOWR Reputation Widget v3.0
 * Встраиваемый виджет репутации на TON блокчейне
 * 
 * Использование:
 * <script src="widget.js"></script>
 * <div class="repowr-widget" data-default-address="UQA..."></div>
 */

(function () {
    'use strict';

    // ===== КОНФИГУРАЦИЯ =====
    const API_URL = 'https://repowr.tech/api/index.php';
    const DEFAULT_ADDRESS = 'UQATKnigdlBIuU3FJ57VSh4Aqxel9oLbQ4hBzIZ6YzWkbZys';

    // ===== СТИЛИ ВИДЖЕТА =====
    // Вставляем CSS прямо в страницу, чтобы виджет работал без внешних файлов
    const STYLES = `
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700&display=swap');

        .rw-root {
            --rw-bg: #0d0f14;
            --rw-card: #13161e;
            --rw-border: #1e2330;
            --rw-accent: #00e5ff;
            --rw-accent2: #7c3aed;
            --rw-text: #e2e8f0;
            --rw-muted: #64748b;
            --rw-gold: #f59e0b;
            --rw-green: #10b981;
            --rw-red: #ef4444;
            font-family: 'Syne', sans-serif;
            background: var(--rw-bg);
            border: 1px solid var(--rw-border);
            border-radius: 16px;
            padding: 24px;
            max-width: 420px;
            color: var(--rw-text);
            box-sizing: border-box;
            position: relative;
            overflow: hidden;
        }

        /* Декоративный фоновый элемент */
        .rw-root::before {
            content: '';
            position: absolute;
            top: -60px; right: -60px;
            width: 200px; height: 200px;
            background: radial-gradient(circle, rgba(0,229,255,0.06) 0%, transparent 70%);
            pointer-events: none;
        }

        /* Светлая тема */
        .rw-root.rw-light {
            --rw-bg: #f8fafc;
            --rw-card: #ffffff;
            --rw-border: #e2e8f0;
            --rw-accent: #0ea5e9;
            --rw-accent2: #7c3aed;
            --rw-text: #0f172a;
            --rw-muted: #94a3b8;
        }

        /* ===== ПОЛЕ ВВОДА АДРЕСА ===== */
        .rw-search {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
        }

        .rw-input {
            flex: 1;
            background: var(--rw-card);
            border: 1px solid var(--rw-border);
            border-radius: 8px;
            padding: 8px 12px;
            color: var(--rw-text);
            font-family: 'Space Mono', monospace;
            font-size: 11px;
            outline: none;
            transition: border-color 0.2s;
            min-width: 0; /* чтобы не выходил за пределы flex */
        }

        .rw-input:focus {
            border-color: var(--rw-accent);
        }

        .rw-input::placeholder {
            color: var(--rw-muted);
        }

        .rw-btn {
            background: var(--rw-accent);
            color: #000;
            border: none;
            border-radius: 8px;
            padding: 8px 14px;
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            font-size: 12px;
            cursor: pointer;
            white-space: nowrap;
            transition: opacity 0.2s, transform 0.1s;
        }

        .rw-btn:hover { opacity: 0.85; }
        .rw-btn:active { transform: scale(0.97); }

        /* ===== ПРОФИЛЬ ===== */
        .rw-profile {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 20px;
        }

        .rw-avatar {
            width: 56px !important; height: 56px !important;
            border-radius: 14px !important;
            object-fit: cover !important;
            border: 2px solid var(--rw-accent) !important;
            flex-shrink: 0;
            display: block;
        }

        /* Заглушка если нет аватара */
        .rw-avatar-placeholder {
            width: 56px; height: 56px;
            border-radius: 14px !important;
            background: linear-gradient(135deg, var(--rw-accent2), var(--rw-accent));
            display: flex; align-items: center; justify-content: center;
            font-size: 22px;
            flex-shrink: 0;
        }

        .rw-name {
            font-size: 18px;
            font-weight: 700;
            line-height: 1.2;
        }

        .rw-bio {
            font-size: 13px;
            color: var(--rw-muted);
            margin-top: 3px;
        }

        .rw-address {
            font-family: 'Space Mono', monospace;
            font-size: 10px;
            color: var(--rw-accent);
            margin-top: 4px;
            word-break: break-all;
        }

        /* ===== БЛОК РЕПУТАЦИИ ===== */
        .rw-rep {
            background: var(--rw-card);
            border: 1px solid var(--rw-border);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
        }

        .rw-score-row {
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-bottom: 12px;
        }

        .rw-score-big {
            font-family: 'Space Mono', monospace;
            font-size: 36px;
            font-weight: 700;
            color: var(--rw-accent);
            line-height: 1;
        }

        .rw-score-label {
            font-size: 12px;
            color: var(--rw-muted);
        }

        .rw-stars {
            font-size: 16px;
            letter-spacing: 2px;
            margin-bottom: 12px;
        }

        /* Сетка мини-статистики */
        .rw-stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }

        .rw-stat {
            background: var(--rw-bg);
            border-radius: 8px;
            padding: 8px 10px;
        }

        .rw-stat-val {
            font-family: 'Space Mono', monospace;
            font-size: 16px;
            font-weight: 700;
        }

        .rw-stat-key {
            font-size: 11px;
            color: var(--rw-muted);
            margin-top: 2px;
        }

        /* ===== СКИЛЛЫ ===== */
        .rw-skills {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 14px;
        }

        .rw-skill {
            background: rgba(124,58,237,0.15);
            color: #a78bfa;
            border: 1px solid rgba(124,58,237,0.3);
            border-radius: 20px;
            padding: 3px 10px;
            font-size: 11px;
        }

        /* ===== ССЫЛКИ ===== */
        .rw-links {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 14px;
        }

        .rw-link {
            color: var(--rw-accent);
            text-decoration: none;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: opacity 0.2s;
        }

        .rw-link:hover { opacity: 0.7; }

        /* ===== ОТЗЫВЫ ===== */
        .rw-reviews-title {
            font-size: 13px;
            font-weight: 700;
            color: var(--rw-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .rw-review {
            background: var(--rw-card);
            border: 1px solid var(--rw-border);
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 8px;
            font-size: 13px;
        }

        .rw-review-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }

        .rw-review-stars { color: var(--rw-gold); }

        .rw-review-date {
            font-size: 11px;
            color: var(--rw-muted);
            font-family: 'Space Mono', monospace;
        }

        .rw-review-text { color: var(--rw-muted); }

        /* ===== СОСТОЯНИЯ ===== */
        .rw-loading {
            text-align: center;
            padding: 30px;
            color: var(--rw-muted);
            font-size: 13px;
        }

        .rw-spinner {
            display: inline-block;
            width: 20px; height: 20px;
            border: 2px solid var(--rw-border);
            border-top-color: var(--rw-accent);
            border-radius: 50%;
            animation: rw-spin 0.8s linear infinite;
            margin-bottom: 8px;
        }

        @keyframes rw-spin {
            to { transform: rotate(360deg); }
        }

        .rw-error {
            background: rgba(239,68,68,0.1);
            border: 1px solid rgba(239,68,68,0.3);
            border-radius: 8px;
            padding: 12px;
            color: var(--rw-red);
            font-size: 13px;
            text-align: center;
        }

        /* ===== ФУТЕР ===== */
        .rw-footer {
            margin-top: 16px;
            text-align: center;
            font-size: 11px;
            color: var(--rw-muted);
        }

        .rw-footer a {
            color: var(--rw-muted);
            text-decoration: none;
        }

        .rw-footer a:hover { color: var(--rw-accent); }
    `;

    // ===== КОНВЕРТАЦИЯ АДРЕСА =====
    // TON адреса бывают двух форматов:
    // - user-friendly: UQATKnig... (base64url, 48 символов)
    // - raw: 0:5324a7b... (workchain:hex)
    // В базе хранится raw формат, поэтому конвертируем перед запросом
    function toRawAddress(address) {
        // Если уже raw формат (начинается с "0:" или "-1:") — возвращаем как есть
        if (/^-?[0-9]+:[a-fA-F0-9]{64}$/.test(address)) {
            return address;
        }

        try {
            // Заменяем URL-safe base64 символы на стандартные
            const b64 = address.replace(/-/g, '+').replace(/_/g, '/');
            // Декодируем base64 в бинарные данные
            const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
            // Структура TON адреса: 2 байта флагов + 1 байт workchain + 32 байта хэша + 2 байта CRC
            // Байт 1 = workchain (подписанный байт)
            const workchain = new Int8Array([bytes[1]])[0]; // signed byte
            // Байты 2-33 = 32 байта хэша адреса
            const hash = Array.from(bytes.slice(2, 34))
                .map(b => b.toString(16).padStart(2, '0'))
                .join('');
            return `${workchain}:${hash}`;
        } catch (e) {
            // Если не удалось конвертировать — возвращаем как есть
            return address;
        }
    }

    // ===== ОСНОВНОЙ КЛАСС ВИДЖЕТА =====
    class RepOWRWidget {

        constructor(element) {
            this.element = element;

            // Читаем настройки из data-атрибутов HTML-элемента
            this.defaultAddress = element.getAttribute('data-default-address') || DEFAULT_ADDRESS;
            this.theme = element.getAttribute('data-theme') || 'dark';
            this.showReviews = element.getAttribute('data-show-reviews') !== 'false'; // по умолчанию показываем

            // Рендерим обёртку и загружаем данные дефолтного адреса
            this.buildShell();
            this.load(this.defaultAddress);
        }

        // Строим каркас виджета: поле ввода + контейнер для данных
        buildShell() {
            this.element.innerHTML = '';

            // Создаём корневой div с нужной темой
            this.root = document.createElement('div');
            this.root.className = `rw-root${this.theme === 'light' ? ' rw-light' : ''}`;

            // Поле ввода адреса
            const searchDiv = document.createElement('div');
            searchDiv.className = 'rw-search';

            this.input = document.createElement('input');
            this.input.className = 'rw-input';
            this.input.type = 'text';
            this.input.placeholder = 'UQ... или EQ... адрес кошелька';
            this.input.value = this.defaultAddress;

            const btn = document.createElement('button');
            btn.className = 'rw-btn';
            btn.textContent = '→ Найти';

            // Клик по кнопке — загружаем введённый адрес
            btn.addEventListener('click', () => {
                const addr = this.input.value.trim();
                if (addr) this.load(addr);
            });

            // Enter в поле тоже срабатывает
            this.input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const addr = this.input.value.trim();
                    if (addr) this.load(addr);
                }
            });

            searchDiv.appendChild(this.input);
            searchDiv.appendChild(btn);
            this.root.appendChild(searchDiv);

            // Контейнер куда будем вставлять данные
            this.content = document.createElement('div');
            this.root.appendChild(this.content);

            this.element.appendChild(this.root);
        }

        // Показываем спиннер загрузки
        showLoading() {
            this.content.innerHTML = `
                <div class="rw-loading">
                    <div class="rw-spinner"></div><br>
                    Загрузка данных...
                </div>
            `;
        }

        // Показываем ошибку
        showError(msg) {
            this.content.innerHTML = `<div class="rw-error">⚠️ ${msg}</div>`;
        }

        // Загружаем данные с API и рендерим
        async load(address) {
            this.showLoading();

            try {
                // Конвертируем адрес в raw формат (0:hex) — именно так хранится в базе
                const rawAddress = toRawAddress(address);

                // Параллельно запрашиваем репутацию и отзывы
                const repUrl = `${API_URL}?endpoint=reputation&address=${encodeURIComponent(rawAddress)}`;
                const revUrl = `${API_URL}?endpoint=reviews&address=${encodeURIComponent(rawAddress)}&limit=3`;

                const promises = [this.fetchJSON(repUrl)];
                if (this.showReviews) promises.push(this.fetchJSON(revUrl));

                const [repData, revData] = await Promise.all(promises);

                if (!repData.success) throw new Error(repData.error || 'Ошибка загрузки');

                this.render(repData.data, revData ? revData.data : null);

            } catch (err) {
                this.showError(err.message);
            }
        }

        // Универсальный fetch с таймаутом
        async fetchJSON(url) {
            const ctrl = new AbortController();
            const tid = setTimeout(() => ctrl.abort(), 10000);
            try {
                const res = await fetch(url, { signal: ctrl.signal });
                clearTimeout(tid);
                if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
                return await res.json();
            } catch (e) {
                clearTimeout(tid);
                if (e.name === 'AbortError') throw new Error('Превышено время ожидания');
                throw e;
            }
        }

        // Рендерим весь профиль
        render(data, reviews) {
            const profile = data.profile || null;
            const rep = data.reputation;
            const address = data.address;

            let html = '';

            // ── ПРОФИЛЬ ─────────────────────────────────
            html += '<div class="rw-profile">';

            if (profile && profile.avatar) {
                html += `<img class="rw-avatar" src="${this.esc(profile.avatar)}" alt="avatar">`;
            } else {
                html += `<div class="rw-avatar-placeholder">👤</div>`;
            }

            html += '<div style="flex:1;min-width:0;">';
            html += `<div class="rw-name">${this.esc(profile ? profile.nickname : 'Неизвестный')}</div>`;
            if (profile && profile.bio) {
                html += `<div class="rw-bio">${this.esc(profile.bio)}</div>`;
            }
            // Укороченный адрес (первые 6 и последние 4 символа)
            const shortAddr = address.length > 12
                ? address.slice(0, 6) + '...' + address.slice(-4)
                : address;
            html += `<div class="rw-address">${shortAddr}</div>`;
            html += '</div></div>';

            // ── БЛОК РЕПУТАЦИИ ────────────────────────────
            const stars = this.renderStars(rep.avg_rating);
            html += `
                <div class="rw-rep">
                    <div class="rw-score-row">
                        <span class="rw-score-big">${rep.final_score}</span>
                        <span class="rw-score-label">итоговый балл</span>
                    </div>
                    <div class="rw-stars">${stars}</div>
                    <div class="rw-stats-grid">
                        <div class="rw-stat">
                            <div class="rw-stat-val">${rep.avg_rating}</div>
                            <div class="rw-stat-key">⭐ ср. оценка</div>
                        </div>
                        <div class="rw-stat">
                            <div class="rw-stat-val">${rep.total_ratings}</div>
                            <div class="rw-stat-key">📊 отзывов</div>
                        </div>
                    </div>
                </div>
            `;

            // ── СКИЛЛЫ ────────────────────────────────────
            if (profile && profile.skills) {
                let skills = profile.skills;
                // Если skills хранится как JSON-строка — парсим
                if (typeof skills === 'string') {
                    try { skills = JSON.parse(skills); } catch (e) { skills = []; }
                }
                if (skills.length > 0) {
                    html += '<div class="rw-skills">';
                    skills.forEach(s => {
                        html += `<span class="rw-skill">${this.esc(s)}</span>`;
                    });
                    html += '</div>';
                }
            }

            // ── ССЫЛКИ ────────────────────────────────────
            if (profile && profile.links) {
                let links = profile.links;
                if (typeof links === 'string') {
                    try { links = JSON.parse(links); } catch (e) { links = {}; }
                }
                const entries = Object.entries(links);
                if (entries.length > 0) {
                    const icons = { telegram: '✈️', github: '💻', website: '🌐', twitter: '🐦', linkedin: '💼' };
                    html += '<div class="rw-links">';
                    entries.forEach(([platform, url]) => {
                        const icon = icons[platform.toLowerCase()] || '🔗';
                        html += `<a class="rw-link" href="${this.esc(url)}" target="_blank" rel="noopener">${icon} ${this.esc(platform)}</a>`;
                    });
                    html += '</div>';
                }
            }

            // ── ОТЗЫВЫ ────────────────────────────────────
            if (reviews && reviews.received && reviews.received.length > 0) {
                html += '<div class="rw-reviews-title">Последние отзывы</div>';
                reviews.received.slice(0, 3).forEach(r => {
                    const date = new Date(r.timestamp * 1000).toLocaleDateString('ru-RU');
                    const stars2 = this.renderStars(r.rating);
                    html += `
                        <div class="rw-review">
                            <div class="rw-review-meta">
                                <span class="rw-review-stars">${stars2}</span>
                                <span class="rw-review-date">${date}</span>
                            </div>
                            ${r.comment ? `<div class="rw-review-text">${this.esc(r.comment)}</div>` : ''}
                        </div>
                    `;
                });
            }

            // ── ФУТЕР ─────────────────────────────────────
            html += `
                <div class="rw-footer">
                    <a href="https://openrep.world" target="_blank">Powered by repOWR</a>
                </div>
            `;

            this.content.innerHTML = html;
        }

        // Генерируем строку звёзд по рейтингу (от 1 до 5)
        renderStars(rating) {
            const full = Math.round(rating);
            let stars = '';
            for (let i = 1; i <= 5; i++) {
                stars += i <= full ? '★' : '☆';
            }
            return stars;
        }

        // Экранируем HTML чтобы не было XSS
        esc(str) {
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
        }
    }

    // ===== ВСТАВКА СТИЛЕЙ В СТРАНИЦУ =====
    // Добавляем стили один раз, даже если виджетов несколько
    function injectStyles() {
        if (document.getElementById('repowr-styles')) return;
        const style = document.createElement('style');
        style.id = 'repowr-styles';
        style.textContent = STYLES;
        document.head.appendChild(style);
    }

    // ===== ИНИЦИАЛИЗАЦИЯ ВСЕХ ВИДЖЕТОВ НА СТРАНИЦЕ =====
    function initAll() {
        injectStyles();
        // Ищем все элементы с классом repowr-widget
        document.querySelectorAll('.repowr-widget').forEach(el => {
            // Не инициализируем повторно
            if (!el.dataset.rwInit) {
                el.dataset.rwInit = '1';
                new RepOWRWidget(el);
            }
        });
    }

    // Ждём загрузки DOM, потом инициализируем
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }

    // Экспортируем класс для ручного использования
    window.RepOWRWidget = RepOWRWidget;

})();