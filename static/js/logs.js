/**
 * logs.js — Live log polling (3s interval) and backup browser modal.
 */

let _logPollTimer = null;
let _lastLogHash = '';

/* ── Live Polling ────────────────────────────────────────── */
function startLogPolling() {
    loadLogs();
    _logPollTimer = setInterval(loadLogs, 3000);
}

async function loadLogs() {
    try {
        const res = await fetch('/api/logs');
        const d = await res.json();

        // Skip DOM update if nothing changed (include metadata in hash)
        const hash = d.lines.join('\n') + '|' + d.total + '|' + d.backup_count;
        if (hash === _lastLogHash) return;
        _lastLogHash = hash;

        const container = document.getElementById('logLines');
        const totalEl = document.getElementById('logTotal');
        const infoEl = document.getElementById('logInfo');
        const backupsBtn = document.getElementById('backupsBtn');
        const backupInfo = document.getElementById('logBackupInfo');

        totalEl.textContent = `(${d.total})`;
        infoEl.textContent = d.total > 0 ? `Last ${d.lines.length} of ${d.total}` : t('log.live');

        if (d.lines.length === 0) {
            container.innerHTML = `<div class="empty">${t('log.empty')}</div>`;
        } else {
            container.innerHTML = d.lines.map(l => `<div class="log-line">${esc(l)}</div>`).join('');
            container.scrollTop = container.scrollHeight;
        }

        backupsBtn.style.display = d.backup_count > 0 ? 'inline-flex' : 'none';
        backupInfo.textContent = d.backup_count > 0 ? `${d.backup_count} backup${d.backup_count > 1 ? 's' : ''}` : '';
    } catch (e) { }
}

async function clearLogs() {
    try {
        const res = await fetch('/api/logs/clear', { method: 'POST' });
        const d = await res.json();
        if (d.success) { toast(t('toast.logs_cleared'), 'success'); _lastLogHash = ''; loadLogs(); }
        else toast(d.error || 'Failed', 'error');
    } catch (e) { toast('Clear failed', 'error'); }
}

/* ── Backup Browser ──────────────────────────────────────── */
function openBackupBrowser() {
    document.getElementById('backupModal').classList.add('active');
    loadBackups();
}
function closeBackupBrowser() {
    document.getElementById('backupModal').classList.remove('active');
}

async function loadBackups() {
    const list = document.getElementById('backupList');
    try {
        const res = await fetch('/api/logs/backups');
        const backups = await res.json();
        if (backups.length === 0) {
            list.innerHTML = `<div class="backup-empty">${t('log.empty')}</div>`;
            return;
        }
        list.innerHTML = backups.map(b => `
            <div class="backup-item" data-file="${esc(b.filename)}">
                <div class="backup-meta">
                    <span class="backup-date">${icon('folder')} ${esc(b.created)}</span>
                    <span class="backup-info">${b.lines} lines · ${(b.size / 1024).toFixed(1)} KB</span>
                </div>
                <div class="backup-actions">
                    <button class="btn btn-ghost btn-sm" onclick="restoreBackup('${esc(b.filename)}')" title="${t('backup.restore')}">${icon('refresh')} ${t('backup.restore')}</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteBackup('${esc(b.filename)}')" title="${t('backup.delete')}">${icon('x')}</button>
                </div>
            </div>
        `).join('');
    } catch (e) { list.innerHTML = '<div class="backup-empty">Failed to load backups</div>'; }
}

async function restoreBackup(filename) {
    try {
        const res = await fetch('/api/logs/restore', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename }),
        });
        const d = await res.json();
        if (d.success) {
            toast(t('toast.backup_restored'), 'success');
            _lastLogHash = '';
            loadLogs();
            loadBackups();
        } else toast(d.error || 'Failed', 'error');
    } catch (e) { toast('Restore failed', 'error'); }
}

async function deleteBackup(filename) {
    try {
        const res = await fetch(`/api/logs/backups/${encodeURIComponent(filename)}`, { method: 'DELETE' });
        const d = await res.json();
        if (d.success) {
            toast(t('toast.backup_deleted'), 'success');
            loadBackups();
            _lastLogHash = '';
            loadLogs();
        } else toast(d.error || 'Failed', 'error');
    } catch (e) { toast('Delete failed', 'error'); }
}
