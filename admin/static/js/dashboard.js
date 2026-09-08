let currentModalIp = null;
let statusInterval = null;
let currentModalTab = 'fingerprint';

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('stat-sessions')) {
        refreshDashboard();
        setInterval(refreshDashboard, 3000);
    }
    
    if (document.getElementById('device-container')) {
        loadDevices();
    }
});

// Sekme Değiştirme Fonksiyonu (Sayfa İçi)
function switchTab(tabName) {
    const tabOverview = document.getElementById('tab-overview');
    const tabDevices = document.getElementById('tab-devices');

    if (tabOverview && tabDevices) {
        tabOverview.style.display = 'none';
        tabDevices.style.display = 'none';

        if (tabName === 'overview') {
            tabOverview.style.display = 'block';
        } else if (tabName === 'devices') {
            tabDevices.style.display = 'block';
            loadDevices();
        }
    }
}

function refreshDashboard() {
    fetch('/admin/api/system/status')
        .then(res => res.json())
        .then(data => {
            const elSessions = document.getElementById('stat-sessions');
            const elBans = document.getElementById('stat-bans');
            const elSpeed = document.getElementById('stat-speed');

            if (elSessions) elSessions.innerText = data.active_sessions.length;
            if (elBans) elBans.innerText = data.bans.length;
            if (elSpeed) elSpeed.innerText = data.general_speed_limit > 0 ? `${data.general_speed_limit} KB/s` : 'Sınırsız';

            const tblSessions = document.getElementById('tbl-sessions');
            if (tblSessions) {
                let sessionRows = '';
                if (data.active_sessions && data.active_sessions.length > 0) {
                    data.active_sessions.forEach(ip => {
                        sessionRows += `<tr>
                            <td>${ip}</td>
                            <td><button class="btn-danger" style="background-color: #ef4444; color: #fff; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;" onclick="kickSession('${ip}')">Oturumu Kapat</button></td>
                        </tr>`;
                    });
                } else {
                    sessionRows = '<tr><td colspan="2">Aktif oturum açan cihaz yok.</td></tr>';
                }
                tblSessions.innerHTML = sessionRows;
            }

            const tblBans = document.getElementById('tbl-bans');
            if (tblBans) {
                let banRows = '';
                if (data.bans && data.bans.length > 0) {
                    data.bans.forEach(ban => {
                        banRows += `<tr>
                            <td>${ban.ip}</td>
                            <td><code>${ban.target}</code></td>
                            <td><button class="btn-danger" style="background-color: #ef4444; color: #fff; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;" onclick="removeBan('${ban.ip}', '${ban.target}')">Kaldır</button></td>
                        </tr>`;
                    });
                } else {
                    banRows = '<tr><td colspan="3">Aktif yasaklı hedef yok.</td></tr>';
                }
                tblBans.innerHTML = banRows;
            }

            const tblSpeeds = document.getElementById('tbl-speeds');
            if (tblSpeeds) {
                let speedRows = '';
                const specialSpeeds = data.special_speeds || [];
                        
                if (Array.isArray(specialSpeeds) && specialSpeeds.length > 0) {
                    specialSpeeds.forEach(item => {
                        speedRows += `<tr>
                            <td>${item.ip}</td>
                            <td><strong style="color: #fff;">${item.limit_kb} KB/s (${item.limit_mb} MB/s)</strong></td>
                            <td><button style="background-color: #ef4444; color: #fff; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;" onclick="removeSpeedLimit('${item.ip}')">Sıfırla</button></td>
                        </tr>`;
                    });
                } else {
                    speedRows = '<tr><td colspan="3">Özel hız kısıtlaması tanımlı cihaz yok.</td></tr>';
                }
                tblSpeeds.innerHTML = speedRows;
            }

            const liveTerminal = document.getElementById('live-terminal');
            if (liveTerminal) {
                let logLines = '';
                if (data.live_logs && data.live_logs.length > 0) {
                    data.live_logs.forEach(log => {
                        let color = log.durum === 'YASAKLANDI' || log.durum === 'ENGELLENDİ' ? '#ef4444' : '#22c55e';
                        logLines += `<div style="margin-bottom: 4px;">
                            <span style="color: #64748b;">[${log.zaman}]</span> 
                            <strong style="color: #38bdf8;">[🔍 TRAFİK TESPİTİ]</strong> 
                            <span style="color: #f8fafc;">${log.ip}</span> ➡️ 
                            <span style="color: #f59e0b;">${log.hedef}</span> 
                            <span style="color: ${color}; float: right;">[${log.durum}]</span>
                        </div>`;
                    });
                }
                liveTerminal.innerHTML = logLines || '<div style="color: #64748b;">Dinleniyor... İstek bekleniyor.</div>';
            }
        });
}
function loadDevices() {
    fetch('/admin/api/devices')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('device-container');
            if (!container) return;

            if (!data.devices || data.devices.length === 0) {
                container.innerHTML = '<div style="color: #94a3b8; grid-column: 1/-1;">Ağda kayıtlı/aktif cihaz bulunamadı.</div>';
                return;
            }

            let cardsHtml = '';
            data.devices.forEach(dev => {
                cardsHtml += `
                    <div class="device-card" onclick="openDeviceModal('${dev.ip}', 'fingerprint')">
                        <div>
                            <div class="device-header">
                                <span class="device-icon">${dev.icon}</span>
                                <span class="device-status" title="Çevrimiçi"></span>
                            </div>
                            <div class="device-title">${dev.hostname}</div>
                            <div class="device-ip">${dev.ip}</div>
                        </div>
                        <div>
                            <span class="device-badge">${dev.device_type}</span>
                        </div>
                    </div>
                `;
            });
            container.innerHTML = cardsHtml;

            checkUrlAndOpenModal(data.devices);
        });
}

function checkUrlAndOpenModal(devicesList) {
    const pathParts = window.location.pathname.split('/').filter(p => p);
    if (pathParts.length >= 3 && pathParts[1] === 'devices') {
        const urlIp = pathParts[2];
        const urlTab = pathParts[3] || 'fingerprint';
        
        const targetDev = devicesList.find(d => d.ip === urlIp);
        if (targetDev) {
            openDeviceModal(urlIp, urlTab, targetDev);
        }
    }
}

function openDeviceModal(ip, tabName = 'fingerprint', devObject = null) {
    currentModalIp = ip;
    currentModalTab = tabName;

    history.pushState(null, '', `/admin/devices/${ip}/${tabName}`);

    const modal = document.getElementById('device-modal');
    if (!modal) return;

    const populateModal = (dev) => {
        const setElText = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.innerText = val || '-';
        };

        setElText('modal-icon', dev.icon);
        setElText('modal-title', dev.hostname);
        setElText('modal-ip', dev.ip);
        setElText('modal-type', dev.device_type);
        setElText('modal-fp-hash', dev.fingerprint_hash);
        setElText('modal-first-seen', dev.first_seen);
        setElText('modal-ua', dev.user_agent);

        updateDeviceStatusView(dev);
    };

    if (devObject) {
        populateModal(devObject);
    } else {
        fetch('/admin/api/devices')
            .then(res => res.json())
            .then(data => {
                const dev = data.devices ? data.devices.find(d => d.ip === ip) : null;
                if (dev) populateModal(dev);
            });
    }

    switchModalTab(tabName);
    modal.style.display = 'flex';

    startStatusPolling();
}

function updateDeviceStatusView(dev) {
    if (!dev) return;

    const pingEl = document.getElementById('modal-status-ping');
    if (pingEl) {
        const pingVal = dev.ping !== undefined ? dev.ping : Math.floor(Math.random() * 15) + 2; // Örnek/API verisi
        pingEl.innerText = `${pingVal} ms`;
        pingEl.style.color = pingVal > 100 ? '#ef4444' : '#22c55e';
    }

    const speedEl = document.getElementById('modal-status-speed');
    const dirIconEl = document.getElementById('modal-status-dir-icon');
    const dirTextEl = document.getElementById('modal-status-dir-text');

    const downloadSpeed = dev.download_mbps || 0.0;
    const uploadSpeed = dev.upload_mbps || 0.0;
    const totalMbps = (downloadSpeed + uploadSpeed).toFixed(2);

    if (speedEl) speedEl.innerText = `${totalMbps} Mbps`;

    if (dirIconEl && dirTextEl) {
        if (downloadSpeed > uploadSpeed && downloadSpeed > 0.1) {
            dirIconEl.innerText = '⬇️';
            dirTextEl.innerText = `Download (${downloadSpeed.toFixed(2)} Mbps)`;
            dirTextEl.style.color = '#38bdf8';
        } else if (uploadSpeed > downloadSpeed && uploadSpeed > 0.1) {
            dirIconEl.innerText = '⬆️';
            dirTextEl.innerText = `Upload (${uploadSpeed.toFixed(2)} Mbps)`;
            dirTextEl.style.color = '#f59e0b';
        } else {
            dirIconEl.innerText = '💤';
            dirTextEl.innerText = 'Boşta / Düşük Trafik';
            dirTextEl.style.color = '#94a3b8';
        }
    }
}

function switchModalTab(tabName) {
    currentModalTab = tabName;

    if (currentModalIp) {
        history.pushState(null, '', `/admin/devices/${currentModalIp}/${tabName}`);
    }

    document.querySelectorAll('.modal-nav-item').forEach(el => el.classList.remove('active'));
    const activeNav = document.getElementById(`tab-link-${tabName}`);
    if (activeNav) activeNav.classList.add('active');

    document.querySelectorAll('.modal-tab-pane').forEach(el => el.classList.remove('active'));
    const activePane = document.getElementById(`modal-tab-${tabName}`);
    if (activePane) activePane.classList.add('active');

    if (tabName === 'status') {
        startStatusPolling();
    } else {
        stopStatusPolling();
    }
}

function startStatusPolling() {
    stopStatusPolling();
    if (currentModalIp && currentModalTab === 'status') {
        statusInterval = setInterval(() => {
            fetch('/admin/api/devices')
                .then(res => res.json())
                .then(data => {
                    const dev = data.devices ? data.devices.find(d => d.ip === currentModalIp) : null;
                    if (dev) updateDeviceStatusView(dev);
                });
        }, 2000);
    }
}

function stopStatusPolling() {
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
}

function closeModal() {
    stopStatusPolling();
    const modal = document.getElementById('device-modal');
    if (modal) modal.style.display = 'none';

    currentModalIp = null;
    history.pushState(null, '', '/admin/devices');
}

window.onpopstate = function() {
    const pathParts = window.location.pathname.split('/').filter(p => p);
    if (pathParts.length < 3) {
        const modal = document.getElementById('device-modal');
        if (modal) modal.style.display = 'none';
    } else {
        const urlIp = pathParts[2];
        const urlTab = pathParts[3] || 'fingerprint';
        openDeviceModal(urlIp, urlTab);
    }
};

function kickSession(ip) {
    if (!confirm(`${ip} cihazının oturumunu kapatmak istediğinize emin misiniz?`)) return;

    fetch('/admin/api/sessions/logout', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ip: ip})
    })
    .then(res => res.json())
    .then(data => {
        refreshDashboard();
    });
}

function addBan() {
    const ip = document.getElementById('ban-ip').value;
    const regex = document.getElementById('ban-regex').value;

    if (!regex) {
        alert('Lütfen en az bir Domain veya Regex kuralı girin.');
        return;
    }

    fetch('/admin/api/bans/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ip: ip, regex: regex})
    }).then(() => {
        document.getElementById('ban-ip').value = '';
        document.getElementById('ban-regex').value = '';
        refreshDashboard();
    });
}

function removeBan(ip, regex) {
    fetch('/admin/api/bans/remove', {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ip: ip, regex: regex})
    }).then(() => refreshDashboard());
}

function setSpeedLimit() {
    const ip = document.getElementById('speed-ip').value;
    const limit = document.getElementById('speed-limit').value;

    if (!ip) {
        alert('Lütfen geçerli bir IP adresi girin.');
        return;
    }

    fetch('/admin/api/speed/ip', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ip: ip, limit_kb: parseInt(limit) || 0})
    }).then(() => {
        document.getElementById('speed-ip').value = '';
        document.getElementById('speed-limit').value = '';
        refreshDashboard();
    });
}

function removeSpeedLimit(ip) {
    fetch('/admin/api/speed/ip', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ip: ip, limit_kb: 0})
    }).then(() => refreshDashboard());
}

function setEveryoneSpeed() {
    const limit = document.getElementById('everyone-speed-limit').value;

    fetch('/admin/api/speed/everyone', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({limit_kb: parseInt(limit) || 0})
    }).then(() => refreshDashboard());
}

function triggerHotReload() {
    fetch('/admin/api/system/reload', {method: 'POST'})
        .then(res => res.json())
        .then(data => alert(data.message));
}