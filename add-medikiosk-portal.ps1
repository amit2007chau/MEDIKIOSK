$ErrorActionPreference = 'Stop'

$Root = "C:\Users\ckris\OneDrive\Documents\ChatGPT\SIH"
Set-Location $Root

Write-Host "=== MediKiosk Unified Portal Installer ===" -ForegroundColor Cyan
Write-Host "This adds ONE new portal service. Existing apps are not edited." -ForegroundColor Gray

# Safety: do not proceed if port 8080 is already occupied.
$port8080 = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if ($port8080) {
    throw "Port 8080 is already in use. Stop the process using port 8080, then run this installer again. Existing MediKiosk services were not changed."
}

$portal = Join-Path $Root "portal"
New-Item -ItemType Directory -Force -Path $portal | Out-Null

$index = @'
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>MediKiosk | Choose your role</title>
  <style>
    :root { color-scheme: dark; --line:#263832; --text:#f1eee6; --muted:#a9b7b1; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; font-family:Inter,Segoe UI,Arial,sans-serif; background:linear-gradient(135deg,#071b17,#0c2721 55%,#071b17); color:var(--text); }
    .shell { width:min(1100px,92vw); margin:auto; min-height:100vh; display:flex; flex-direction:column; }
    header { padding:30px 0; display:flex; align-items:center; justify-content:space-between; }
    .brand { display:flex; gap:12px; align-items:center; font-weight:800; letter-spacing:.08em; }
    .logo { width:42px; height:42px; border-radius:12px; display:grid; place-items:center; background:#0f5e55; color:#7ce4d7; font-size:22px; }
    .secure { color:var(--muted); font-size:13px; }
    main { flex:1; display:grid; place-items:center; padding:30px 0 70px; }
    .hero { width:100%; text-align:center; }
    .eyebrow { color:#5fe0d1; font-size:12px; font-weight:800; letter-spacing:.18em; }
    h1 { margin:18px 0 12px; font-family:Georgia,serif; font-size:clamp(42px,6vw,72px); line-height:1.02; font-weight:500; }
    .sub { color:var(--muted); max-width:650px; margin:0 auto 42px; font-size:17px; line-height:1.6; }
    .roles { display:grid; grid-template-columns:repeat(3,1fr); gap:18px; text-align:left; }
    .role { display:block; text-decoration:none; color:inherit; background:rgba(16,24,22,.92); border:1px solid var(--line); border-radius:18px; padding:28px; min-height:225px; transition:.18s ease; }
    .role:hover { transform:translateY(-3px); border-color:#34766d; background:#121d1a; }
    .icon { width:48px; height:48px; display:grid; place-items:center; border-radius:13px; background:#123f38; color:#72dfd1; font-size:23px; margin-bottom:24px; }
    .role h2 { margin:0 0 8px; font-size:23px; }
    .role p { margin:0 0 22px; color:var(--muted); line-height:1.5; font-size:14px; }
    .action { color:#71e0d3; font-weight:700; font-size:14px; }
    footer { padding:20px 0 28px; display:flex; justify-content:space-between; color:#82938d; font-size:12px; border-top:1px solid rgba(255,255,255,.05); }
    @media(max-width:800px){ .roles{grid-template-columns:1fr;} h1{font-size:48px;} footer{gap:20px; flex-direction:column;} }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div class="brand"><div class="logo">♥</div><span>MEDIKIOSK</span></div>
      <div class="secure">🔒 Private &amp; secure</div>
    </header>
    <main>
      <section class="hero">
        <div class="eyebrow">CLINICAL INTAKE PLATFORM</div>
        <h1>Welcome to MediKiosk</h1>
        <p class="sub">Choose how you would like to continue. Each role opens the appropriate MediKiosk workspace.</p>
        <div class="roles">
          <a class="role" href="http://localhost:3000">
            <div class="icon">♙</div>
            <h2>Patient</h2>
            <p>Start your pre-consultation intake, consent, interview and document submission.</p>
            <span class="action">Start patient intake →</span>
          </a>
          <a class="role" href="http://localhost:3001">
            <div class="icon">✚</div>
            <h2>Doctor</h2>
            <p>Open the clinical dashboard and sign in with your doctor credentials.</p>
            <span class="action">Doctor login →</span>
          </a>
          <a class="role" href="http://localhost:3002">
            <div class="icon">◉</div>
            <h2>Staff</h2>
            <p>Open the triage queue and sign in with your staff credentials.</p>
            <span class="action">Staff login →</span>
          </a>
        </div>
      </section>
    </main>
    <footer>
      <span>Information is organized for clinical review.</span>
      <span>Clinical decisions remain with the treating clinician.</span>
    </footer>
  </div>
</body>
</html>
'@

Set-Content -Path (Join-Path $portal "index.html") -Value $index -Encoding UTF8

$compose = Join-Path $Root "docker-compose.yml"
if (-not (Test-Path $compose)) {
    throw "docker-compose.yml not found at $compose"
}

$backup = "$compose.before-portal.bak"
if (-not (Test-Path $backup)) {
    Copy-Item $compose $backup
    Write-Host "Backup created: $backup" -ForegroundColor DarkGreen
}

$text = Get-Content -Raw $compose

if ($text -match '(?m)^\s{2}portal:\s*$') {
    Write-Host "Portal service already exists; no compose change required." -ForegroundColor Yellow
}
else {
    $lines = $text -split "`r?`n"
    $servicesIndex = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^services:\s*$') {
            $servicesIndex = $i
            break
        }
    }

    if ($servicesIndex -lt 0) {
        throw "Could not find the top-level 'services:' section. No compose change was made."
    }

    $insertAt = $lines.Count
    for ($i = $servicesIndex + 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^[A-Za-z0-9_.-]+:\s*$') {
            $insertAt = $i
            break
        }
    }

    $serviceLines = @(
        "",
        "  portal:",
        "    image: nginx:alpine",
        "    ports:",
        '      - "127.0.0.1:8080:80"',
        "    volumes:",
        "      - ./portal:/usr/share/nginx/html:ro",
        "    restart: unless-stopped",
        ""
    )

    $newLines = @()
    if ($insertAt -gt 0) { $newLines += $lines[0..($insertAt-1)] }
    $newLines += $serviceLines
    if ($insertAt -lt $lines.Count) { $newLines += $lines[$insertAt..($lines.Count-1)] }

    Set-Content -Path $compose -Value ($newLines -join "`r`n") -Encoding UTF8
    Write-Host "Added only the new 'portal' service." -ForegroundColor Green
}

Write-Host "`nValidating Compose configuration..." -ForegroundColor Cyan
docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Compose validation failed. Restoring the original compose file from backup." -ForegroundColor Red
    Copy-Item $backup $compose -Force
    throw "docker compose config failed. The original compose file was restored."
}

Write-Host "docker compose config: PASS" -ForegroundColor Green
Write-Host "`nNext command:" -ForegroundColor Cyan
Write-Host "docker compose up -d portal"
Write-Host "`nThen open: http://localhost"
