/**
 * Menubar — dropdown menus, about modal, log modal.
 */

// ── Dropdown menus ──────────────────────────────────────
(function () {
    const items = document.querySelectorAll('.menu-item');

    items.forEach(item => {
        const label = item.querySelector('.menu-label');

        label.addEventListener('click', (e) => {
            e.stopPropagation();
            const wasOpen = item.classList.contains('open');
            closeAllMenus();
            if (!wasOpen) item.classList.add('open');
        });

        // Hover-open when another menu is already open
        item.addEventListener('mouseenter', () => {
            const anyOpen = document.querySelector('.menu-item.open');
            if (anyOpen && anyOpen !== item) {
                closeAllMenus();
                item.classList.add('open');
            }
        });
    });

    // Close all menus on outside click
    document.addEventListener('click', () => closeAllMenus());

    // Close on dropdown button click
    document.querySelectorAll('.menu-dropdown button').forEach(btn => {
        btn.addEventListener('click', () => closeAllMenus());
    });
})();

function closeAllMenus() {
    document.querySelectorAll('.menu-item.open').forEach(m => m.classList.remove('open'));
}

// ── Log modal ───────────────────────────────────────────
function openLogModal() {
    document.getElementById('logModal').classList.add('active');
}

function closeLogModal() {
    document.getElementById('logModal').classList.remove('active');
}

// ── About modal ─────────────────────────────────────────
function openAboutModal() {
    document.getElementById('aboutModal').classList.add('active');
}

function closeAbout() {
    document.getElementById('aboutModal').classList.remove('active');
}
