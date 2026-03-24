import os
import sys
import time
import subprocess

try:
    import psutil
except Exception:
    psutil = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(BASE_DIR, 'control_panel.pid')
DETACHED_PROCESS = 0x00000008 if os.name == 'nt' else 0
CREATE_NEW_PROCESS_GROUP = getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)


def stop_process(pid):
    if not pid:
        return

    try:
        if psutil is not None:
            process = psutil.Process(pid)
            process.terminate()
            try:
                process.wait(timeout=3)
                return
            except Exception:
                process.kill()
                return
    except Exception:
        pass

    try:
        if os.name == 'nt':
            subprocess.run(
                ['taskkill', '/PID', str(pid), '/F'],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            os.kill(pid, 9)
    except Exception:
        pass


def resolve_runner():
    python_exe = sys.executable
    pythonw_candidate = python_exe.replace('python.exe', 'pythonw.exe')
    if pythonw_candidate != python_exe and os.path.exists(pythonw_candidate):
        return pythonw_candidate
    return python_exe


def start_control_panel():
    runner = resolve_runner()
    creation_flags = CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS if os.name == 'nt' else 0
    process = subprocess.Popen(
        [runner, 'config_editor.py'],
        cwd=BASE_DIR,
        creationflags=creation_flags,
        close_fds=True,
    )
    with open(PID_FILE, 'w', encoding='utf-8') as f:
        f.write(str(process.pid))


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ''
    target_pid = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None

    # Let the HTTP response finish before touching the current server.
    time.sleep(1.2)

    if action == 'stop':
        stop_process(target_pid)
        return

    if action == 'restart':
        stop_process(target_pid)
        time.sleep(0.8)
        start_control_panel()


if __name__ == '__main__':
    main()
