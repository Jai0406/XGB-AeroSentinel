import subprocess
import sys
import time
import urllib.request
import urllib.error

def wait_for_backend(url="http://localhost:8000/health", timeout=60):
    print(f"Waiting for Meteorological Engine to spin up (timeout: {timeout}s)...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req) as response:
                if response.getcode() == 200:
                    print("Backend Engine is online!")
                    return True
        except urllib.error.URLError:
            time.sleep(1)
    return False

def main():
    print("Starting FastAPI backend (XGB Sentinel)...")
    # Make sure your FastAPI file is named main.py (or change "main:app" below)
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    if not wait_for_backend():
        print("Error: Backend failed to start within the timeout.")
        backend.terminate()
        sys.exit(1)

    print("Starting Streamlit Dashboard...")
    frontend = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\nShutting down Sentinel System...")
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()