/**
 * modal.js — Add/Edit/Delete modals, file picker, and form submission.
 */

/* ── Add Modal ───────────────────────────────────────────── */
function openAddModal() {
    document.getElementById('modalTitle').textContent = t('modal.add_title');
    document.getElementById('modalSubmit').textContent = t('modal.add_btn');
    document.getElementById('editingKey').value = '';
    document.getElementById('exePath').value = '';
    document.getElementById('keyName').value = ''; document.getElementById('keyName').readOnly = false;
    document.getElementById('displayName').value = '';
    document.getElementById('iconPath').value = '';
    document.getElementById('extensionsGroup').style.display = 'none';
    document.querySelectorAll('.scope-option').forEach(el => el.classList.remove('active'));
    setSelectedExtensions([]);
    document.getElementById('entryModal').classList.add('active');
}

/* ── Edit Modal ──────────────────────────────────────────── */
async function openEditModal(keyName) {
    try {
        const res = await fetch(`/api/entry/${encodeURIComponent(keyName)}`);
        const data = await res.json();
        document.getElementById('modalTitle').textContent = `${t('modal.edit_title')}: ${data.display_name || keyName}`;
        document.getElementById('modalSubmit').textContent = t('modal.save_btn');
        document.getElementById('editingKey').value = keyName;

        let exe = '';
        const cmd = data.command || '';
        if (cmd.startsWith('"')) exe = cmd.split('"')[1]; else exe = cmd.split(' ')[0];

        document.getElementById('exePath').value = exe;
        document.getElementById('keyName').value = keyName; document.getElementById('keyName').readOnly = true;
        document.getElementById('displayName').value = data.display_name || '';
        document.getElementById('iconPath').value = data.icon || '';

        document.querySelectorAll('.scope-option').forEach(el => {
            el.classList.toggle('active', data.scopes && data.scopes.includes(el.dataset.scope));
        });
        document.getElementById('extensionsGroup').style.display =
            document.querySelector('[data-scope="extension"]').classList.contains('active') ? 'block' : 'none';
        setSelectedExtensions(data.extensions);
        document.getElementById('entryModal').classList.add('active');
    } catch (e) { toast('Failed to load entry', 'error'); }
}

function closeModal() { document.getElementById('entryModal').classList.remove('active'); }

/* ── Scope Toggle ────────────────────────────────────────── */
function toggleScope(el) {
    el.classList.toggle('active');
    document.getElementById('extensionsGroup').style.display =
        document.querySelector('[data-scope="extension"]').classList.contains('active') ? 'block' : 'none';
}

/* ── File Picker ─────────────────────────────────────────── */
async function pickFile() {
    try {
        const res = await fetch('/api/pick-file', { method: 'POST' });
        const d = await res.json();
        if (d.path) {
            document.getElementById('exePath').value = d.path;
            const fn = d.path.split(/[/\\]/).pop();
            const stem = fn.replace(/\.exe$/i, '').replace(/[_-]/g, ' ');
            const title = stem.replace(/\b\w/g, c => c.toUpperCase());
            if (!document.getElementById('keyName').readOnly) document.getElementById('keyName').value = title.replace(/\s/g, '');
            if (!document.getElementById('displayName').value) document.getElementById('displayName').value = `Open with ${title}`;
            if (!document.getElementById('iconPath').value) document.getElementById('iconPath').value = `${d.path},0`;
        }
    } catch (e) { toast('File picker failed', 'error'); }
}

/* ── Submit Entry ────────────────────────────────────────── */
async function submitEntry() {
    const editingKey = document.getElementById('editingKey').value;
    const scopes = [...document.querySelectorAll('.scope-option.active')].map(el => el.dataset.scope);
    const extensions = getSelectedExtensions();
    const payload = {
        key_name: document.getElementById('keyName').value.trim(),
        display_name: document.getElementById('displayName').value.trim(),
        exe_path: document.getElementById('exePath').value.trim(),
        icon: document.getElementById('iconPath').value.trim() || null,
        scopes, extensions,
    };
    if (!payload.key_name || !payload.exe_path || scopes.length === 0) {
        toast('Fill all fields and select at least one scope.', 'error'); return;
    }
    try {
        const url = editingKey ? `/api/entries/${encodeURIComponent(editingKey)}` : '/api/entries';
        const method = editingKey ? 'PUT' : 'POST';
        const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const d = await res.json();
        if (d.error) { toast(d.error, 'error'); } else { toast(editingKey ? t('toast.edit_ok') : t('toast.add_ok'), 'success'); closeModal(); loadEntries(); }
    } catch (e) { toast('Operation failed', 'error'); }
}

/* ── Delete Confirm ──────────────────────────────────────── */
function openConfirm(k) { deleteTarget = k; document.getElementById('confirmName').textContent = k; document.getElementById('confirmModal').classList.add('active'); }
function closeConfirm() { document.getElementById('confirmModal').classList.remove('active'); deleteTarget = null; }
async function confirmRemove() {
    if (!deleteTarget) return;
    try {
        const res = await fetch(`/api/entries/${encodeURIComponent(deleteTarget)}`, { method: 'DELETE' });
        const d = await res.json();
        if (d.error) toast(d.error, 'error'); else { toast(t('toast.remove_ok', { name: deleteTarget }), 'success'); loadEntries(); }
    } catch (e) { toast(t('toast.remove_fail'), 'error'); }
    closeConfirm();
}
