/**
 * extensions.js — Extension picker categories, chip toggling, and selection management.
 */

let selectedExts = new Set();

/* ── Extension Categories ────────────────────────────────── */
const EXT_CATEGORIES = [
    { id: 'code', icon: '💻', label: 'Code / Programming', exts: ['.py', '.js', '.ts', '.jsx', '.tsx', '.c', '.cpp', '.h', '.cs', '.java', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.lua', '.sh', '.bat', '.ps1'] },
    { id: 'web', icon: '🌐', label: 'Web / Markup', exts: ['.html', '.htm', '.css', '.scss', '.sass', '.less', '.svg', '.xml', '.xsl', '.vue', '.svelte', '.astro'] },
    { id: 'data', icon: '📊', label: 'Data / Config', exts: ['.json', '.yaml', '.yml', '.toml', '.ini', '.env', '.csv', '.tsv', '.sql', '.graphql', '.proto'] },
    { id: 'docs', icon: '📝', label: 'Documents / Text', exts: ['.txt', '.md', '.rst', '.log', '.rtf', '.tex', '.org', '.pdf', '.doc', '.docx', '.odt'] },
    { id: 'img', icon: '🖼️', label: 'Images', exts: ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.ico', '.tiff', '.psd', '.ai', '.eps', '.raw'] },
    { id: 'audio', icon: '🎵', label: 'Audio', exts: ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'] },
    { id: 'video', icon: '🎬', label: 'Video', exts: ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'] },
    { id: 'arch', icon: '📦', label: 'Archives', exts: ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'] },
];

function buildExtPicker() {
    const picker = document.getElementById('extPicker');
    picker.innerHTML = EXT_CATEGORIES.map(cat => `
        <div class="ext-category" data-cat="${cat.id}">
            <div class="ext-category-header" onclick="toggleExtCategory('${cat.id}', event)">
                <div class="cat-check"></div>
                <span class="cat-icon">${cat.icon}</span>
                <span class="cat-label">${cat.label}</span>
                <span class="cat-count">${cat.exts.length}</span>
                <span class="cat-arrow">▼</span>
            </div>
            <div class="ext-items">
                ${cat.exts.map(ext => `<div class="ext-chip" data-ext="${ext}" onclick="toggleExtChip(this, event)">${ext}</div>`).join('')}
            </div>
        </div>
    `).join('');
}

function toggleExtCategory(catId, event) {
    event.stopPropagation();
    const catEl = document.querySelector(`.ext-category[data-cat="${catId}"]`);
    const header = catEl.querySelector('.ext-category-header');

    const rect = header.getBoundingClientRect();
    const clickX = event.clientX - rect.left;

    if (clickX <= 36) {
        const cat = EXT_CATEGORIES.find(c => c.id === catId);
        const allSelected = cat.exts.every(e => selectedExts.has(e));
        cat.exts.forEach(e => {
            if (allSelected) selectedExts.delete(e);
            else selectedExts.add(e);
        });
        syncExtUI();
    } else {
        catEl.classList.toggle('open');
    }
}

function toggleExtChip(chip, event) {
    event.stopPropagation();
    const ext = chip.dataset.ext;
    if (selectedExts.has(ext)) selectedExts.delete(ext);
    else selectedExts.add(ext);
    syncExtUI();
}

function syncExtUI() {
    document.querySelectorAll('.ext-chip').forEach(chip => {
        chip.classList.toggle('active', selectedExts.has(chip.dataset.ext));
    });

    EXT_CATEGORIES.forEach(cat => {
        const header = document.querySelector(`.ext-category[data-cat="${cat.id}"] .ext-category-header`);
        const selectedCount = cat.exts.filter(e => selectedExts.has(e)).length;
        header.classList.remove('checked', 'partial');
        if (selectedCount === cat.exts.length) header.classList.add('checked');
        else if (selectedCount > 0) header.classList.add('partial');

        const countEl = header.querySelector('.cat-count');
        countEl.textContent = selectedCount > 0 ? `${selectedCount}/${cat.exts.length}` : `${cat.exts.length}`;
    });

    // Build removable chips in summary
    const summary = document.getElementById('extSummary');
    const arr = [...selectedExts].sort();
    if (arr.length === 0) {
        summary.innerHTML = '';
    } else {
        const allCatExts = new Set(EXT_CATEGORIES.flatMap(c => c.exts));
        const customExts = arr.filter(e => !allCatExts.has(e));
        const categoryExts = arr.filter(e => allCatExts.has(e));

        let html = `<div class="ext-summary-header">${t ? t('modal.selected') : 'Selected'}: ${arr.length}</div>`;
        html += '<div class="ext-summary-chips">';
        categoryExts.forEach(ext => {
            html += `<span class="ext-summary-chip" data-ext="${ext}" onclick="removeExt(this)">${ext} <span class="ext-remove">×</span></span>`;
        });
        customExts.forEach(ext => {
            html += `<span class="ext-summary-chip custom" data-ext="${ext}" onclick="removeExt(this)">${ext} <span class="ext-remove">×</span></span>`;
        });
        html += '</div>';
        summary.innerHTML = html;
    }
}

function addManualExts() {
    const input = document.getElementById('extManualInput');
    const val = input.value.trim();
    if (!val) return;
    val.split(',').map(e => e.trim()).filter(Boolean).forEach(ext => {
        if (!ext.startsWith('.')) ext = '.' + ext;
        selectedExts.add(ext);
    });
    input.value = '';
    syncExtUI();
}

function removeExt(chipEl) {
    const ext = chipEl.dataset.ext;
    selectedExts.delete(ext);
    syncExtUI();
}

function getSelectedExtensions() {
    return [...selectedExts].sort();
}

function setSelectedExtensions(exts) {
    selectedExts.clear();
    (exts || []).forEach(e => selectedExts.add(e));
    syncExtUI();
}
