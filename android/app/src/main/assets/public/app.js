/* Smart Farming - Mobile VARI/ExG Scanner */

const video = document.getElementById('video');
const overlay = document.getElementById('overlay');
const proc = document.getElementById('processor');
const startBtn = document.getElementById('startBtn');
const switchBtn = document.getElementById('switchBtn');
const snapBtn = document.getElementById('snapBtn');
const statusSpan = document.getElementById('status');
const errorBanner = document.getElementById('errorBanner');
const opacityRange = document.getElementById('opacity');
const modeSelect = document.getElementById('mode');

// Navigation elements
const menuBtn = document.getElementById('menuBtn');
const drawer = document.getElementById('drawer');
const closeDrawer = document.getElementById('closeDrawer');
const backdrop = document.getElementById('backdrop');
const pageHome = document.getElementById('page-home');
const pageScanner = document.getElementById('page-scanner');
const pageAbout = document.getElementById('page-about');
const pageData = document.getElementById('page-data');
const pageLogin = document.getElementById('page-login');

// Data page elements
const dataList = document.getElementById('dataList');
const dataEmpty = document.getElementById('dataEmpty');
const clearData = document.getElementById('clearData');

// Login elements
const loginForm = document.getElementById('loginForm');
const loginEmail = document.getElementById('loginEmail');
const loginPassword = document.getElementById('loginPassword');
const loginStatus = document.getElementById('loginStatus');
const sessionBox = document.getElementById('sessionBox');
const userEmail = document.getElementById('userEmail');
const logoutBtn = document.getElementById('logoutBtn');
const signupBtn = document.getElementById('signupBtn');

// Bottom nav
const bottomNav = document.getElementById('bottomNav');
const navIndicator = document.getElementById('navIndicator');
// Home stats
const statSnapshots = document.getElementById('statSnapshots');
const statHealthy = document.getElementById('statHealthy');
const statBorderline = document.getElementById('statBorderline');
const statUnhealthy = document.getElementById('statUnhealthy');

// Firebase Auth (optional)
const fbCfg = (window.firebaseConfig || {});

// Sign up (Create account)
signupBtn?.addEventListener('click', async () => {
  const email = (loginEmail.value || '').trim();
  const pwd = (loginPassword.value || '').trim();
  if (!email || !pwd) { loginStatus.textContent = 'Enter email and password.'; return; }
  if (fbEnabled && auth) {
    loginStatus.textContent = 'Creating account...';
    try {
      await auth.createUserWithEmailAndPassword(email, pwd);
      loginStatus.textContent = 'Account created and signed in.';
      renderSession();
    } catch (err) {
      loginStatus.textContent = err && err.message ? err.message : 'Sign-up failed.';
    }
  } else {
    // Local fallback: simply store session
    localStorage.setItem('session', JSON.stringify({ email, ts: Date.now() }));
    loginStatus.textContent = 'Account created (local only).';
    renderSession();
  }
});

// Home dashboard stats
function updateHomeStats() {
  if (!statSnapshots) return;
  const list = JSON.parse(localStorage.getItem('snapshots') || '[]');
  const total = list.length;
  let h=0,b=0,u=0;
  for (const it of list) {
    if (it.status === 'Healthy') h++;
    else if (it.status === 'Borderline') b++;
    else u++;
  }
  statSnapshots.textContent = String(total);
  statHealthy.textContent = String(h);
  statBorderline.textContent = String(b);
  statUnhealthy.textContent = String(u);
}
const fbEnabled = !!(window.firebase && fbCfg && fbCfg.apiKey && !/REPLACE_ME/i.test(String(fbCfg.apiKey)));
let auth = null;
if (fbEnabled) {
  try {
    // Initialize only once
    if (!firebase.apps || !firebase.apps.length) {
      firebase.initializeApp(fbCfg);
    }
    auth = firebase.auth();
    auth.onAuthStateChanged((user) => {
      renderSession(user);
    });
  } catch (e) {
    console.warn('Firebase init failed, falling back to local session.', e);
  }
}

let currentDeviceId = null;
let devices = [];
let stream = null;
let animId = null;
let currentPage = 'home';

async function listCameras() {
  try {
    const all = await navigator.mediaDevices.enumerateDevices();
    devices = all.filter(d => d.kind === 'videoinput');
  } catch (e) {
    console.error('enumerateDevices failed', e);
  }
}

function showError(msg) {
  errorBanner.textContent = msg;
  errorBanner.classList.remove('hidden');
  clearTimeout(showError._t);
  showError._t = setTimeout(() => errorBanner.classList.add('hidden'), 5000);
}

async function startCamera(deviceId = null) {
  try {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
    const constraints = {
      audio: false,
      video: deviceId ? { deviceId: { exact: deviceId } } : { facingMode: { ideal: 'environment' } }
    };
    stream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = stream;
    await video.play();
    const track = stream.getVideoTracks()[0];
    const settings = track.getSettings();
    currentDeviceId = settings.deviceId || deviceId || null;

    // Resize canvases to match video
    const w = settings.width || video.videoWidth || 640;
    const h = settings.height || video.videoHeight || 480;
    overlay.width = w; overlay.height = h;
    proc.width = w; proc.height = h;

    if (animId) cancelAnimationFrame(animId);
    loop();
  } catch (e) {
    console.error('startCamera error', e);
    if (e.name === 'NotAllowedError') {
      showError('Camera permission denied. Please allow camera access and tap Start.');
    } else if (e.name === 'NotFoundError') {
      showError('No camera found. Try Switch to cycle devices.');
    } else if (e.name === 'NotReadableError') {
      showError('Camera is in use by another app. Close it and try again.');
    } else {
      showError('Camera start failed. Check permissions and try again.');
    }
  }
}

function computeVARIExG(frameData, w, h) {
  const data = frameData.data;
  const variArr = new Float32Array(w * h);
  const exgArr = new Float32Array(w * h);

  let gSum = 0, rSum = 0, bSum = 0; // for quick stats

  for (let i = 0, p = 0; i < data.length; i += 4, p++) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];

    // ExG = 2G - R - B
    const exg = 2 * g - r - b;
    exgArr[p] = exg;

    // VARI = (G - R) / (G + R - B)
    const denom = (g + r - b);
    const vari = (g - r) / (denom + 1e-6);
    variArr[p] = Math.max(-1, Math.min(1, vari));

    gSum += g; rSum += r; bSum += b;
  }

  // Normalize ExG to 0..1
  let minExg = Infinity, maxExg = -Infinity;
  for (let i = 0; i < exgArr.length; i++) { if (exgArr[i] < minExg) minExg = exgArr[i]; if (exgArr[i] > maxExg) maxExg = exgArr[i]; }
  const exgNorm = new Float32Array(exgArr.length);
  const exgRange = (maxExg - minExg) || 1;
  for (let i = 0; i < exgArr.length; i++) exgNorm[i] = (exgArr[i] - minExg) / exgRange;

  // Normalize VARI -1..1 -> 0..1
  const variNorm = new Float32Array(variArr.length);
  for (let i = 0; i < variArr.length; i++) variNorm[i] = (variArr[i] + 1.0) / 2.0;

  return { variArr, variNorm, exgArr, exgNorm };
}

function classify(variNorm, exgNorm) {
  const n = variNorm.length;
  let sum = 0;
  for (let i = 0; i < n; i++) sum += 0.5 * variNorm[i] + 0.5 * exgNorm[i];
  const meanScore = sum / n;

  let status = 'Unhealthy';
  if (meanScore > 0.6) status = 'Healthy';
  else if (meanScore > 0.45) status = 'Borderline';

  return { status, score: meanScore };
}

function drawHUD(ctx, w, h, status, score, fps) {
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,0,0.35)';
  ctx.fillRect(0, 0, w, 72);

  const color = status === 'Healthy' ? '#21b14b' : (status === 'Borderline' ? '#ff9800' : '#e53935');
  ctx.fillStyle = '#fff';
  ctx.font = '16px system-ui, Arial';
  ctx.fillText(`Health: `, 12, 24);
  ctx.fillStyle = color;
  ctx.fillText(`${status}`, 78, 24);

  ctx.fillStyle = '#fff';
  ctx.fillText(`Score: ${score.toFixed(3)}`, 12, 44);
  ctx.fillText(`FPS: ${fps.toFixed(1)}`, 12, 64);

  ctx.restore();
}

let lastT = performance.now();
let fpsEMA = 0;

function loop() {
  const w = overlay.width, h = overlay.height;
  const ctxO = overlay.getContext('2d');
  const ctxP = proc.getContext('2d');

  ctxP.drawImage(video, 0, 0, w, h);
  const frame = ctxP.getImageData(0, 0, w, h);

  const { variNorm, exgNorm } = computeVARIExG(frame, w, h);

  // false color heat visualization per mode
  const mode = modeSelect.value;
  const heat = new Uint8ClampedArray(w * h * 4);
  const alpha = Math.max(0, Math.min(1, parseFloat(opacityRange.value || '0.3')));
  for (let p = 0, i = 0; p < variNorm.length; p++, i += 4) {
    const v = mode === 'vari' ? variNorm[p] : (mode === 'exg' ? exgNorm[p] : 0.5 * variNorm[p] + 0.5 * exgNorm[p]);
    // map 0..1 to greenish heat
    const r = Math.max(0, 255 * (v - 0.5) * 2);
    const g = 255 * v;
    const b = Math.max(0, 255 * (0.5 - v) * 2);
    heat[i] = r; heat[i + 1] = g; heat[i + 2] = b; heat[i + 3] = Math.floor(alpha * 255);
  }

  // Draw video first
  ctxO.clearRect(0, 0, w, h);
  ctxO.drawImage(video, 0, 0, w, h);

  // Blend heatmap
  const heatImg = new ImageData(heat, w, h);
  ctxO.putImageData(heatImg, 0, 0);

  // Classification
  const { status, score } = classify(variNorm, exgNorm);

  // FPS calc
  const now = performance.now();
  const fps = 1000 / Math.max(1, (now - lastT));
  fpsEMA = fpsEMA ? fpsEMA * 0.9 + fps * 0.1 : fps;
  lastT = now;

  drawHUD(ctxO, w, h, status, score, fpsEMA);
  statusSpan.textContent = `Status: ${status}`;
  statusSpan.className = `status badge ${status}`;

  // Stash latest status to use when saving snapshot
  loop._lastStatus = { status, score, ts: Date.now() };

  // Update home stats periodically while scanning (lightweight)
  if (!loop._statsTick || (performance.now() - loop._statsTick) > 1500) {
    updateHomeStats();
    loop._statsTick = performance.now();
  }

  animId = requestAnimationFrame(loop);
}

startBtn.addEventListener('click', async () => {
  await listCameras();
  await startCamera(currentDeviceId);
});

switchBtn.addEventListener('click', async () => {
  await listCameras();
  if (!devices.length) return;
  const idx = devices.findIndex(d => d.deviceId === currentDeviceId);
  const next = devices[(idx + 1) % devices.length];
  await startCamera(next.deviceId);
});

snapBtn.addEventListener('click', () => {
  try {
    const a = document.createElement('a');
    a.download = `crop_snapshot_${Date.now()}.png`;
    a.href = overlay.toDataURL('image/png');
    a.click();

    // Also save to localStorage list (Data page)
    const entry = {
      id: Date.now(),
      png: overlay.toDataURL('image/png'),
      status: (loop._lastStatus?.status) || 'Unknown',
      score: (loop._lastStatus?.score) || 0,
      time: new Date().toISOString()
    };
    const list = JSON.parse(localStorage.getItem('snapshots') || '[]');
    list.unshift(entry);
    localStorage.setItem('snapshots', JSON.stringify(list.slice(0, 50)));
    if (currentPage === 'data') renderDataList();
    updateHomeStats();
  } catch (e) {
    console.error('snapshot failed', e);
  }
});

// Auto-start if permissions already granted
(async () => {
  try {
    if (navigator.permissions && navigator.permissions.query) {
      const perm = await navigator.permissions.query({ name: 'camera' });
      if (perm.state === 'granted') {
        await startCamera();
      }
    }
  } catch (_) {
    // permissions API may not be available; ignore
  }
})();

// Drawer controls
function openDrawer() {
  drawer.classList.add('open');
  backdrop.classList.remove('hidden');
}
function hideDrawer() {
  drawer.classList.remove('open');
  backdrop.classList.add('hidden');
}
menuBtn?.addEventListener('click', openDrawer);
closeDrawer?.addEventListener('click', hideDrawer);
backdrop?.addEventListener('click', hideDrawer);

// SPA navigation
function showPage(name) {
  // Stop camera when leaving scanner
  if (currentPage === 'scanner' && name !== 'scanner') {
    try {
      if (animId) cancelAnimationFrame(animId);
      animId = null;
      if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
      overlay.getContext('2d').clearRect(0,0,overlay.width, overlay.height);
    } catch(_) {}
  }

  currentPage = name;
  pageHome.classList.toggle('hidden', name !== 'home');
  pageScanner.classList.toggle('hidden', name !== 'scanner');
  pageAbout.classList.toggle('hidden', name !== 'about');
  pageData.classList.toggle('hidden', name !== 'data');
  pageLogin.classList.toggle('hidden', name !== 'login');

  // Highlight bottom nav active tab
  document.querySelectorAll('.bottom-nav .tab').forEach(t => {
    const ln = t.getAttribute('data-link');
    t.classList.toggle('active', ln === name);
  });
  updateIndicator(name);

  // Auto-start camera when entering scanner if permission granted
  if (name === 'scanner') {
    (async () => {
      try {
        if (navigator.permissions && navigator.permissions.query) {
          const perm = await navigator.permissions.query({ name: 'camera' });
          if (perm.state === 'granted') {
            await listCameras();
            await startCamera(currentDeviceId);
          }
        }
      } catch(_) {}
    })();
  }
  if (name === 'data') {
    renderDataList();
  }
  if (name === 'login') {
    renderSession();
  }
  if (name === 'home') {
    updateHomeStats();
  }
  hideDrawer();
}

// Handle hash links and initial route
function routeFromHash() {
  const h = (location.hash || '#home').replace('#','');
  if (['home','scanner','about','data','login'].includes(h)) showPage(h); else showPage('home');
}
window.addEventListener('hashchange', routeFromHash);
document.querySelectorAll('.nav-link').forEach(a => a.addEventListener('click', (e) => {
  const target = e.currentTarget.getAttribute('data-link');
  if (target) showPage(target);
}));
routeFromHash();

// Animated indicator movement
function updateIndicator(name) {
  if (!navIndicator) return;
  const order = ['home','data','scanner','about','login'];
  const idx = Math.max(0, order.indexOf(name));
  const pct = idx * 20; // tabs are 5 columns
  navIndicator.style.transform = `translateX(${pct}%)`;
}

// Data page rendering and actions
function renderDataList() {
  const list = JSON.parse(localStorage.getItem('snapshots') || '[]');
  dataEmpty.classList.toggle('hidden', list.length > 0);
  dataList.innerHTML = '';
  list.forEach(item => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <img src="${item.png}" alt="snapshot" />
      <div class="meta">
        <div><strong>${item.status}</strong> • ${new Date(item.time).toLocaleString()}</div>
        <div>Score: ${Number(item.score).toFixed(3)}</div>
      </div>`;
    dataList.appendChild(card);
  });
}

clearData?.addEventListener('click', () => {
  localStorage.removeItem('snapshots');
  renderDataList();
  updateHomeStats();
});

// Mock login session (local only)
function renderSession(user) {
  if (fbEnabled && auth) {
    const u = user || auth.currentUser;
    if (u && u.email) {
      sessionBox.hidden = false;
      userEmail.textContent = u.email;
      loginForm.classList.add('hidden');
      loginStatus.textContent = '';
      return;
    }
    sessionBox.hidden = true;
    loginForm.classList.remove('hidden');
    return;
  }
  // Fallback local session
  const sess = JSON.parse(localStorage.getItem('session') || 'null');
  if (sess?.email) {
    sessionBox.hidden = false;
    userEmail.textContent = sess.email;
    loginForm.classList.add('hidden');
    loginStatus.textContent = '';
  } else {
    sessionBox.hidden = true;
    loginForm.classList.remove('hidden');
  }
}

loginForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = (loginEmail.value || '').trim();
  const pwd = (loginPassword.value || '').trim();
  if (!email || !pwd) { loginStatus.textContent = 'Enter email and password.'; return; }
  if (fbEnabled && auth) {
    loginStatus.textContent = 'Signing in...';
    try {
      await auth.signInWithEmailAndPassword(email, pwd);
      loginStatus.textContent = 'Signed in.';
      renderSession();
    } catch (err) {
      loginStatus.textContent = err && err.message ? err.message : 'Sign-in failed.';
    }
  } else {
    // Fallback local session
    localStorage.setItem('session', JSON.stringify({ email, ts: Date.now() }));
    loginStatus.textContent = 'Signed in (local only).';
    renderSession();
  }
});

logoutBtn?.addEventListener('click', async () => {
  if (fbEnabled && auth) {
    try { await auth.signOut(); } catch(_) {}
    renderSession();
  } else {
    localStorage.removeItem('session');
    renderSession();
  }
});
