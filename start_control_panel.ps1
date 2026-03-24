$ErrorActionPreference = 'Stop'

$port = 5000
$cwd = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonFallback = 'C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe'

function Test-ControlPanel {
    try {
        $response = Invoke-WebRequest -UseBasicParsing ("http://127.0.0.1:{0}/" -f $port) -TimeoutSec 2
        return ($response.StatusCode -ge 200)
    } catch {
        return $false
    }
}

function Open-ControlPanelPage {
    try {
        Start-Process ("http://127.0.0.1:{0}/" -f $port) | Out-Null
    } catch {
        Write-Host '[INFO] Control panel is ready. Open http://127.0.0.1:5000/ manually if the browser did not launch.'
    }
}

function Resolve-PythonPath {
    $pythonPath = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1
    if (-not $pythonPath -or -not (Test-Path $pythonPath)) {
        $pythonPath = $pythonFallback
    }
    if (-not (Test-Path $pythonPath)) {
        throw 'Python not found. Please install Python 3.9-3.12 first.'
    }
    return $pythonPath
}

function Test-PythonVersion([string]$pythonPath) {
    $versionLine = (& $pythonPath -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')").Trim()
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to read Python version.'
    }

    $version = [Version]$versionLine
    if ($version.Major -ne 3 -or $version.Minor -lt 9 -or $version.Minor -gt 12) {
        throw ("Unsupported Python version: {0}. Please use Python 3.9-3.12." -f $versionLine)
    }

    Write-Host ("[INFO] Python version: {0}" -f $versionLine)
}

function Ensure-Pip([string]$pythonPath) {
    & $pythonPath -m pip --version *> $null
    if ($LASTEXITCODE -ne 0) {
        throw 'pip not found. Please install pip first.'
    }
}

function Test-ConsoleDependencies([string]$pythonPath) {
    $checkCode = @"
import importlib.util
import sys

modules = [
    'flask',
    'flask_cors',
    'comtypes',
    'PIL',
    'typing_extensions',
    'pyperclip',
    'win32api',
    'openai',
    'pyautogui',
    'werkzeug',
    'psutil',
    'filelock',
    'requests',
    'bs4',
    'lxml',
    'cv2',
]

missing = [name for name in modules if importlib.util.find_spec(name) is None]
print(', '.join(missing))
sys.exit(1 if missing else 0)
"@

    $missing = (& $pythonPath -c $checkCode 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -eq 0) {
        return $true
    }

    if (-not $missing) {
        $missing = 'unknown modules'
    }

    Write-Host ("[INFO] Missing dependencies: {0}" -f $missing)
    return $false
}

function Install-ConsoleDependencies([string]$pythonPath, [string]$workingDir) {
    $requirementsFile = Join-Path $workingDir 'requirements.txt'
    $libsDir = Join-Path $workingDir 'libs'

    if (-not (Test-Path $requirementsFile)) {
        throw ("requirements.txt not found: {0}" -f $requirementsFile)
    }

    Write-Host '[INFO] Installing missing dependencies for the control panel...'

    & $pythonPath -m pip install --upgrade pip --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to upgrade pip.'
    }

    $installArgs = @(
        '-m', 'pip', 'install',
        '-r', $requirementsFile,
        '--index-url', 'https://mirrors.aliyun.com/pypi/simple/',
        '--extra-index-url', 'https://pypi.tuna.tsinghua.edu.cn/simple',
        '--trusted-host', 'mirrors.aliyun.com',
        '--trusted-host', 'pypi.tuna.tsinghua.edu.cn'
    )

    if (Test-Path $libsDir) {
        $installArgs += @('-f', $libsDir)
    }

    & $pythonPath @installArgs
    if ($LASTEXITCODE -ne 0) {
        throw 'Dependency installation failed.'
    }
}

if (Test-ControlPanel) {
    Open-ControlPanelPage
    Write-Host '[INFO] Control panel is already running.'
    exit 0
}

$pythonPath = Resolve-PythonPath
Test-PythonVersion $pythonPath
Ensure-Pip $pythonPath

if (-not (Test-ConsoleDependencies $pythonPath)) {
    Install-ConsoleDependencies $pythonPath $cwd
    if (-not (Test-ConsoleDependencies $pythonPath)) {
        throw 'Dependencies are still incomplete after installation.'
    }
}

$runnerPath = $pythonPath -replace 'python\.exe$', 'pythonw.exe'
if (-not (Test-Path $runnerPath)) {
    $runnerPath = $pythonPath
}

$process = Start-Process -FilePath $runnerPath -ArgumentList 'config_editor.py' -WorkingDirectory $cwd -WindowStyle Hidden -PassThru
Set-Content -Path (Join-Path $cwd 'control_panel.pid') -Value $process.Id

Start-Sleep -Seconds 2

if (Test-ControlPanel) {
    Write-Host '[OK] Control panel started.'
    exit 0
}

throw 'Failed to start control panel.'
