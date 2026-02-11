/**
 * app.js — Init, status, entries, filtering, rendering, and utilities.
 */

let entries = [];
let deleteTarget = null;
let activeFilter = 'all';

/* ── Utils ────────────────────────────────────────────────── */
function toast(msg, type = 'success') {
    const c = document.getElementById('toasts');
    const el = document.createElement('div');
    el.className = `toast ${type}`; el.textContent = msg;
    c.appendChild(el); setTimeout(() => el.remove(), 3000);
}
function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

/* ── Init ────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
    await initI18n();
    await checkStatus();
    await loadEntries();
    buildExtPicker();
    startLogPolling();
});

/* ── Status ──────────────────────────────────────────────── */
async function checkStatus() {
    try {
        const res = await fetch('/api/status');
        const d = await res.json();
        const badge = document.getElementById('adminBadge');
        if (d.admin) {
            badge.textContent = '';
            badge.style.display = 'none';
        } else {
            badge.textContent = t('status.not_admin');
            badge.style.display = 'inline';
        }

        const toggle = document.getElementById('win11Toggle');
        const menuStatus = document.getElementById('classicMenuStatus');
        if (d.classic_menu) {
            if (toggle) toggle.classList.add('on');
            if (menuStatus) { menuStatus.textContent = t('status.enabled'); menuStatus.className = 'menu-status enabled'; }
        } else {
            if (toggle) toggle.classList.remove('on');
            if (menuStatus) { menuStatus.textContent = t('status.disabled'); menuStatus.className = 'menu-status disabled'; }
        }
    } catch (e) { }
}

/* ── Win11 Toggle ────────────────────────────────────────── */
async function toggleWin11() {
    try {
        const res = await fetch('/api/win11-menu', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'toggle', restart_explorer: true }),
        });
        const d = await res.json();
        if (d.error) { toast(d.error, 'error'); return; }
        const toggle = document.getElementById('win11Toggle');
        const menuStatus = document.getElementById('classicMenuStatus');
        if (d.classic_menu) {
            if (toggle) toggle.classList.add('on');
            toast(t('toast.classic_on'), 'success');
            if (menuStatus) { menuStatus.textContent = t('status.enabled'); menuStatus.className = 'menu-status enabled'; }
        } else {
            if (toggle) toggle.classList.remove('on');
            toast(t('toast.classic_off'), 'success');
            if (menuStatus) { menuStatus.textContent = t('status.disabled'); menuStatus.className = 'menu-status disabled'; }
        }
    } catch (e) { toast('Failed: ' + e.message, 'error'); }
}

/* ── Load ────────────────────────────────────────────────── */
async function loadEntries() {
    try {
        const res = await fetch('/api/entries');
        entries = await res.json();
        renderFiltered();
    } catch (e) { toast(t('toast.load_fail'), 'error'); }
}

/* ── Filter & Search ─────────────────────────────────────── */
function setFilter(el) {
    document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    activeFilter = el.dataset.filter;
    renderFiltered();
}

function renderFiltered() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    let filtered = entries;
    if (activeFilter !== 'all') {
        filtered = filtered.filter(e => e.scopes.includes(activeFilter));
    }
    if (query) {
        filtered = filtered.filter(e =>
            (e.display_name || '').toLowerCase().includes(query) ||
            (e.key_name || '').toLowerCase().includes(query) ||
            (e.command || '').toLowerCase().includes(query)
        );
    }
    render(filtered);
}

/* ── Render ───────────────────────────────────────────────── */
const SCOPE_META = {
    all_files: { label: () => t('scopes.all_files'), short: () => t('scopes.short_all'), dot: 'all_files' },
    directory: { label: () => t('scopes.directory'), short: () => t('scopes.short_dir'), dot: 'directory' },
    dir_background: { label: () => t('scopes.dir_background'), short: () => t('scopes.short_dirbg'), dot: 'dir_background' },
};

function render(list) {
    const container = document.getElementById('entriesContainer');
    const countEl = document.getElementById('entryCount');
    countEl.textContent = t('entries.count', { filtered: list.length, total: entries.length });

    if (list.length === 0) {
        container.innerHTML = `<div class="empty-state"><div class="icon">${icon('clipboard')}</div><p>${t('entries.empty')}</p></div>`;
        return;
    }

    if (activeFilter !== 'all') {
        container.innerHTML = `<div class="entries-list">${list.map(cardHTML).join('')}</div>`;
        return;
    }

    const groups = {};
    for (const e of list) {
        const primary = e.scopes[0] || 'all_files';
        if (!groups[primary]) groups[primary] = [];
        groups[primary].push(e);
    }

    let html = '';
    for (const [scope, items] of Object.entries(groups)) {
        const meta = SCOPE_META[scope] || { label: () => scope, short: () => scope, dot: scope };
        html += `
                <div class="scope-group collapsed" id="sg-${scope}">
                    <div class="scope-group-header" onclick="toggleScopeGroup('sg-${scope}')">
                        <div class="dot ${meta.dot}"></div>
                        <h3>${meta.label()}</h3>
                        <span class="count">${items.length}</span>
                        <span class="collapse-arrow">${icon('chevron_down')}</span>
                    </div>
                    <div class="entries-list">${items.map(cardHTML).join('')}</div>
                </div>`;
    }
    container.innerHTML = html;
}

function toggleScopeGroup(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const wasCollapsed = el.classList.contains('collapsed');
    // Close all groups first (accordion)
    document.querySelectorAll('.scope-group').forEach(g => g.classList.add('collapsed'));
    // Open clicked one if it was closed
    if (wasCollapsed) el.classList.remove('collapsed');
}

function cardHTML(e) {
    const scopeBadges = e.scopes.map(s => {
        const m = SCOPE_META[s] || { short: () => s, dot: s };
        return `<span class="scope-badge ${m.dot}">${m.short()}</span>`;
    }).join('');

    return `
            <div class="entry-card">
                <div class="entry-info">
                    <div class="entry-name">${esc(e.display_name || e.key_name)}</div>
                    <div class="entry-command">${esc(e.command || '')}</div>
                    <div class="entry-scopes">${scopeBadges}</div>
                </div>
                <div class="entry-actions">
                    <button class="btn btn-ghost btn-sm" onclick="openEditModal('${esc(e.key_name)}')">${icon('edit')} ${t('entries.edit')}</button>
                    <button class="btn btn-danger btn-sm" onclick="openConfirm('${esc(e.key_name)}')">${icon('x')}</button>
                </div>
            </div>`;
}
