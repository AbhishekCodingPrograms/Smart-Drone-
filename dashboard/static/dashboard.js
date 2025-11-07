// Smart Farming Drones - Dashboard JavaScript

// Global variables
let updateInterval;
let isMissionRunning = false;
let missionStartTime = null;
let missionTimerInterval = null;
let currentMissionId = null;
let leafletMap = null;
let leafletLayer = null;
let trackLine = null;

// Initialize dashboard when DOM is ready
$(document).ready(function() {
    initializeDashboard();
    startDataUpdates();
});

function initializeDashboard() {
    // Mission control buttons
    $('#startMission').click(startMission);
    $('#stopMission').click(stopMission);
    $('#generateReport').click(generateReport);
    $('#themeToggle').click(toggleTheme);

    // Initial data load
    updateDashboardData();
    applySavedTheme();
    initLeaflet();
}

function initLeaflet() {
    try {
        leafletMap = L.map('leafletMap').setView([28.6139, 77.2090], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap'
        }).addTo(leafletMap);
        leafletLayer = L.layerGroup().addTo(leafletMap);
    } catch(e) {
        console.log('Leaflet initialization skipped');
    }
}

function startDataUpdates() {
    updateInterval = setInterval(updateDashboardData, 5000); // Update every 5 seconds
}

function updateDashboardData() {
    // Update drone status
    $.get('/api/drone_status')
        .done(function(data) {
            updateStatusMetrics(data);
        })
        .fail(function() {
            $('#connectionStatus').removeClass('status-online').addClass('status-offline');
        });

    // Update field data
    $.get('/api/field_data')
        .done(function(data) {
            updateFieldMap(data);
            updateKpisWithFieldData(data);
        });

    // Update mission stats
    $.get('/api/mission_stats')
        .done(function(data) {
            updateMissionStats(data);
        });

    // Update alerts
    $.get('/api/alerts')
        .done(function(data) {
            updateAlerts(data);
            updateKpiAlerts(data);
        });

    // Update last update time
    $('#lastUpdate').text('Updated: ' + new Date().toLocaleTimeString());
    $('#connectionStatus').removeClass('status-offline').addClass('status-online');
}

function updateStatusMetrics(data) {
    $('#batteryLevel').text(data.battery_level ? data.battery_level.toFixed(1) + '%' : '--%');
    $('#sprayLevel').text(data.spray_level ? data.spray_level.toFixed(1) + 'L' : '--L');
    
    // Update progress bars
    if (typeof data.battery_level === 'number') {
        const battery = Math.max(0, Math.min(100, data.battery_level));
        $('#batteryBar').css('width', battery + '%');
        $('#batteryBar').removeClass('danger warning');
        if (data.battery_level < 20) {
            $('#batteryBar').addClass('danger');
        } else if (data.battery_level < 50) {
            $('#batteryBar').addClass('warning');
        }
    }
    
    if (typeof data.spray_level === 'number') {
        const sprayPercent = (data.spray_level / 10) * 100; // 10L capacity baseline
        $('#sprayBar').css('width', Math.max(0, Math.min(100, sprayPercent)) + '%');
    }
    
    if (data.is_flying) {
        $('#missionStatus').removeClass('status-ready').addClass('status-flying').text('Flying');
        $('#startMission').prop('disabled', true);
        $('#stopMission').prop('disabled', false);
        isMissionRunning = true;
        if (!missionStartTime) {
            missionStartTime = new Date();
            startMissionTimer();
        }
    } else {
        $('#missionStatus').removeClass('status-flying').addClass('status-ready').text('Ready');
        $('#startMission').prop('disabled', false);
        $('#stopMission').prop('disabled', true);
        isMissionRunning = false;
        stopMissionTimer();
    }
}

function updateMissionStats(data) {
    $('#zonesScanned').text(data.zones_scanned || '--');
    $('#successRate').text(data.success_rate ? data.success_rate.toFixed(1) + '%' : '--%');
}

function updateFieldMap(data) {
    const mapContainer = $('#fieldMap');
    mapContainer.empty();

    if (!data || data.length === 0) {
        mapContainer.html('<div class="loading"><i class="fas fa-spinner fa-spin"></i> No field data available</div>');
        return;
    }

    // Create zone markers
    data.forEach(function(zone) {
        const marker = $('<div class="zone-marker"></div>');
        
        // Position marker (scaled to fit container)
        const x = (zone.x / 500) * 100; // Assuming 500m field width
        const y = (zone.y / 500) * 100; // Assuming 500m field height
        
        marker.css({
            left: x + '%',
            top: y + '%'
        });

        // Set color based on health status
        if (zone.health_status === 'Healthy') {
            marker.addClass('zone-healthy');
        } else if (zone.health_status === 'Diseased') {
            marker.addClass('zone-diseased');
        } else if (zone.health_status === 'Pest-affected') {
            marker.addClass('zone-pest');
        }

        // Add tooltip
        marker.attr('title', 
            `Zone: ${zone.zone_id}\n` +
            `Health: ${zone.health_status}\n` +
            `NDVI: ${zone.ndvi_value.toFixed(2)}\n` +
            `Moisture: ${zone.moisture_level.toFixed(1)}%`
        );

        mapContainer.append(marker);
    });

    // Update Leaflet overlay
    try {
        if (!leafletMap) return;
        leafletLayer.clearLayers();
        fetch('/api/missions').then(r=>r.json()).then(ms => {
            const missions = (ms && ms.missions) || [];
            const origin = missions.length ? missions[missions.length-1].origin : { lat:28.6139, lng:77.2090 };
            const bounds = [];
            data.forEach((z) => {
                const lat = origin.lat + (z.y - 250) / 111111.0;
                const lng = origin.lng + (z.x - 250) / (111111.0 * Math.cos(origin.lat*Math.PI/180));
                const color = z.health_status === 'Healthy' ? 'green' : (z.health_status === 'Diseased' ? 'red' : 'orange');
                const circle = L.circleMarker([lat,lng], { radius: 6, color, fillColor: color, fillOpacity: 0.9 });
                circle.bindTooltip(`Zone ${z.zone_id}<br>NDVI: ${z.ndvi_value.toFixed(2)}<br>Moisture: ${z.moisture_level.toFixed(1)}%`);
                circle.addTo(leafletLayer);
                bounds.push([lat,lng]);
            });
            if (bounds.length) leafletMap.fitBounds(bounds, { padding: [20,20] });
        });
    } catch(e) {
        console.log('Leaflet update skipped');
    }

    // Update Last Sprayed KPI
    try {
        const timestamps = data.map(z => z.last_sprayed).filter(Boolean).map(t => new Date(t).getTime());
        if (timestamps.length) {
            const lastTs = new Date(Math.max.apply(null, timestamps));
            $('#kpiLastSprayed').text(lastTs.toLocaleTimeString());
        } else {
            $('#kpiLastSprayed').text('—');
        }
    } catch(e) {
        $('#kpiLastSprayed').text('—');
    }
}

function updateAlerts(data) {
    const alertsContainer = $('#alertsContainer');
    
    if (!data || data.length === 0) {
        alertsContainer.html('<div class="text-muted text-center">No alerts</div>');
        return;
    }

    alertsContainer.empty();
    data.forEach(function(alert) {
        const alertClass = alert.type === 'critical' ? 'alert-critical' : 'alert-warning';
        const alertHtml = `
            <div class="alert-item ${alertClass}">
                <strong>${alert.type.toUpperCase()}</strong>
                <div>${alert.message}</div>
                <small class="text-muted">${new Date(alert.timestamp).toLocaleTimeString()}</small>
            </div>
        `;
        alertsContainer.append(alertHtml);
    });
}

function startMission() {
    // Register a mission with origin
    fetch('/api/missions', { 
        method:'POST', 
        headers:{'Content-Type':'application/json'}, 
        body: JSON.stringify({ 
            name: 'Autonomous Mission', 
            origin: { lat: 28.6139, lng: 77.2090 } 
        }) 
    })
    .then(r=>r.json())
    .then(res => { 
        currentMissionId = res && res.mission ? res.mission.id : null; 
    })
    .catch(()=>{});

    $.post('/api/start_mission')
        .done(function(response) {
            if (response.success) {
                showNotification('Mission started successfully!', 'success');
                missionStartTime = new Date();
                startMissionTimer();
                loadCharts();
                try { 
                    if (leafletMap && !trackLine) {
                        trackLine = L.polyline([], { color: 'blue' }).addTo(leafletMap); 
                    }
                } catch(e) {}
            } else {
                showNotification('Failed to start mission: ' + response.message, 'error');
            }
        })
        .fail(function() {
            showNotification('Error starting mission', 'error');
        });
}

function stopMission() {
    $.post('/api/stop_mission')
        .done(function(response) {
            if (response.success) {
                showNotification('Mission stopped successfully!', 'success');
                stopMissionTimer();
                loadCharts();
                trackLine = null;
            } else {
                showNotification('Failed to stop mission: ' + response.message, 'error');
            }
        })
        .fail(function() {
            showNotification('Error stopping mission', 'error');
        });
}

function generateReport() {
    $('#generateReport').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Generating...');
    
    $.post('/api/generate_report')
        .done(function(response) {
            if (response.success) {
                showReport(response);
                showNotification('Report generated successfully!', 'success');
            } else {
                showNotification('Failed to generate report: ' + response.message, 'error');
            }
        })
        .fail(function() {
            showNotification('Error generating report', 'error');
        })
        .always(function() {
            $('#generateReport').prop('disabled', false).html('<i class="fas fa-file-alt"></i> Generate Report');
        });
}

function showReport(response) {
    const reportSection = $('#reportSection');
    const reportContent = $('#reportContent');
    
    let reportHtml = '<h4>Key Insights:</h4><ul>';
    response.insights.forEach(function(insight) {
        reportHtml += `<li>${insight}</li>`;
    });
    reportHtml += '</ul>';
    
    reportHtml += '<h4>Recommendations:</h4><ul>';
    response.recommendations.forEach(function(rec) {
        reportHtml += `<li>${rec}</li>`;
    });
    reportHtml += '</ul>';
    
    reportHtml += `<div style="margin-top: 24px;">
        <a href="/api/download_report" class="btn btn-primary">
            <i class="fas fa-download"></i> Download Full Report
        </a>
    </div>`;
    
    reportContent.html(reportHtml);
    reportSection.show();
    
    // Scroll to report
    $('html, body').animate({
        scrollTop: reportSection.offset().top - 100
    }, 1000);
}

function showNotification(message, type) {
    const notificationClass = type === 'success' ? 'notification-success' : 'notification-error';
    const notification = $(`
        <div class="notification ${notificationClass}">
            ${message}
            <button class="notification-close">&times;</button>
        </div>
    `);
    
    $('body').append(notification);
    
    notification.find('.notification-close').click(function() {
        notification.remove();
    });
    
    // Auto remove after 5 seconds
    setTimeout(function() {
        notification.remove();
    }, 5000);
}

// KPI helpers
function updateKpisWithFieldData(data) {
    if (!Array.isArray(data) || !data.length) {
        $('#kpiAvgNdvi').text('--');
        $('#kpiDiseased').text('--');
        return;
    }
    try {
        const ndviVals = data.map(z => Number(z.ndvi_value)).filter(v => !isNaN(v));
        const avg = ndviVals.reduce((a,b)=>a+b,0) / Math.max(1, ndviVals.length);
        $('#kpiAvgNdvi').text(avg.toFixed(2));
    } catch(e) {
        $('#kpiAvgNdvi').text('--');
    }
    try {
        const diseased = data.filter(z => z.health_status === 'Diseased').length;
        $('#kpiDiseased').text(String(diseased));
    } catch(e) {
        $('#kpiDiseased').text('--');
    }
}

function updateKpiAlerts(alerts) {
    try {
        const count = Array.isArray(alerts) ? alerts.length : 0;
        $('#kpiAlerts').text(String(count));
    } catch(e) {
        $('#kpiAlerts').text('--');
    }
}

// Theme handling
function applySavedTheme() {
    try {
        const saved = localStorage.getItem('dashboard-theme') || 'dark';
        if (saved === 'light') {
            document.body.classList.add('light-theme');
        } else {
            document.body.classList.remove('light-theme');
        }
        updateThemeButton();
    } catch(e) {}
}

function toggleTheme() {
    document.body.classList.toggle('light-theme');
    const isLight = document.body.classList.contains('light-theme');
    try {
        localStorage.setItem('dashboard-theme', isLight ? 'light' : 'dark');
    } catch(e) {}
    updateThemeButton();
}

function updateThemeButton() {
    const isLight = document.body.classList.contains('light-theme');
    $('#themeToggle').html(isLight ? '<i class="fas fa-moon"></i> Dark' : '<i class="fas fa-sun"></i> Light');
}

// Load charts
function loadCharts() {
    // Health chart
    $.get('/api/health_chart')
        .done(function(data) {
            $('#healthChart').html(data);
        });

    // NDVI chart
    $.get('/api/ndvi_chart')
        .done(function(data) {
            $('#ndviChart').html(data);
        });

    // Moisture chart
    $.get('/api/moisture_chart')
        .done(function(data) {
            $('#moistureChart').html(data);
        });
}

// Load charts every 30 seconds
setInterval(loadCharts, 30000);
loadCharts(); // Initial load

// Mission timer helpers
function startMissionTimer() {
    updateMissionTimer();
    if (missionTimerInterval) clearInterval(missionTimerInterval);
    missionTimerInterval = setInterval(updateMissionTimer, 1000);
}

function stopMissionTimer() {
    if (missionTimerInterval) clearInterval(missionTimerInterval);
    missionTimerInterval = null;
    missionStartTime = null;
    $('#missionTimer').text('Elapsed: 00:00');
}

function updateMissionTimer() {
    if (!missionStartTime) return;
    const now = new Date();
    const seconds = Math.floor((now - missionStartTime) / 1000);
    const mm = String(Math.floor(seconds / 60)).padStart(2, '0');
    const ss = String(seconds % 60).padStart(2, '0');
    $('#missionTimer').text(`Elapsed: ${mm}:${ss}`);
}
