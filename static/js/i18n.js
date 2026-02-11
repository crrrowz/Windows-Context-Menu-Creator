/**
 * i18n.js — Language & Theme engine.
 * Loads translations from /lang/{code}.json, applies RTL/LTR,
 * and toggles dark/light theme via CSS custom properties.
 */

/* ── SVG Icon Library ─────────────────────────────────────── */
const ICONS = {
    search: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
    refresh: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>`,
    plus: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
    folder: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`,
    trash: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`,
    archive: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>`,
    edit: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
    clipboard: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>`,
    sun: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`,
    moon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`,
    globe: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`,
    folder_open: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/><path d="M2 10h20"/></svg>`,
    chevron_down: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`,
    x: `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
};

/* ── State ────────────────────────────────────────────────── */
let _strings = {};
let _currentLang = localStorage.getItem('app_lang') || 'en';
let _currentTheme = localStorage.getItem('app_theme') || 'dark';

/* ── Public API ───────────────────────────────────────────── */

/** Get a translation string by dot-path, e.g. t('menu.file') */
function t(path, replacements = {}) {
    const keys = path.split('.');
    let val = _strings;
    for (const k of keys) {
        if (val && typeof val === 'object' && k in val) val = val[k];
        else return path; // fallback to key
    }
    if (typeof val !== 'string') return path;
    // Replace {placeholders}
    for (const [k, v] of Object.entries(replacements)) {
        val = val.replace(`{${k}}`, v);
    }
    return val;
}

/** Get an SVG icon by name */
function icon(name) {
    return ICONS[name] || '';
}

/** Load language and apply to all [data-i18n] elements */
async function setLanguage(lang) {
    try {
        const res = await fetch(`/lang/${lang}.json`);
        _strings = await res.json();
        _currentLang = lang;
        localStorage.setItem('app_lang', lang);

        // Apply dir & lang
        document.documentElement.lang = _strings.lang || lang;
        document.documentElement.dir = _strings.dir || 'ltr';
        document.body.classList.toggle('rtl', _strings.dir === 'rtl');

        // Update all data-i18n elements
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const attr = el.getAttribute('data-i18n-attr');
            if (attr === 'placeholder') {
                el.placeholder = t(key);
            } else if (attr === 'title') {
                el.title = t(key);
            } else {
                // Preserve leading icon if element has data-i18n-icon
                const iconName = el.getAttribute('data-i18n-icon');
                el.innerHTML = iconName ? `${icon(iconName)} ${t(key)}` : t(key);
            }
        });

        // Update dynamic content
        if (typeof renderFiltered === 'function') renderFiltered();
        if (typeof checkStatus === 'function') await checkStatus();

        // Update toggle button labels
        const langBtn = document.querySelector('[data-action="toggle-lang"]');
        if (langBtn) {
            langBtn.innerHTML = `${icon('globe')} ${_currentLang === 'en' ? 'العربية' : 'English'}`;
        }

        // Re-sync theme button label with new language
        const themeBtn = document.querySelector('[data-action="toggle-theme"]');
        if (themeBtn) {
            const isDark = _currentTheme === 'dark';
            themeBtn.innerHTML = `${isDark ? icon('sun') : icon('moon')} ${isDark ? t('theme.light') : t('theme.dark')}`;
        }

    } catch (e) {
        console.error('Failed to load language:', lang, e);
    }
}

/** Toggle between ar/en */
function toggleLanguage() {
    setLanguage(_currentLang === 'en' ? 'ar' : 'en');
}

/** Set theme (dark/light) */
function setTheme(theme) {
    _currentTheme = theme;
    localStorage.setItem('app_theme', theme);
    document.documentElement.setAttribute('data-theme', theme);

    // Update theme toggle button label
    const btn = document.querySelector('[data-action="toggle-theme"]');
    if (btn) {
        const isDark = theme === 'dark';
        btn.innerHTML = `${isDark ? icon('sun') : icon('moon')} ${isDark ? t('theme.light') : t('theme.dark')}`;
    }
}

/** Toggle dark/light */
function toggleTheme() {
    setTheme(_currentTheme === 'dark' ? 'light' : 'dark');
}

/** Initialize i18n + theme on page load */
async function initI18n() {
    // Apply theme immediately (before language load)
    setTheme(_currentTheme);
    await setLanguage(_currentLang);
}
