#!/usr/bin/env bash
set -e

# ==============================================================================
# Nighty Headless Pterodactyl Startup Orchestrator
# Compatible with Python 3.14 runtime & Wine 10/11 WoW64
# ==============================================================================

export HOME="/home/container"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:$PATH"
export WINEPREFIX="${WINEPREFIX:-/home/container/.local/share/nighty/prefix}"
export WINEARCH="win64"
export WINEDEBUG="-all"
export DISPLAY="${DISPLAY:-:99}"

SERVER_PORT="${SERVER_PORT:-8088}"
WEB_USERNAME="${WEB_USERNAME:-admin}"
WEB_PASSWORD="${WEB_PASSWORD:-nighty123}"

cd /home/container

echo "=================================================================="
echo "    Nighty Headless (Pterodactyl Edition) - Python 3.14 Ready    "
echo "=================================================================="

# 1. Verify binary presence
if [ ! -f "Nighty.exe" ] && [ ! -f "Nighty_stub.exe" ]; then
    echo "[-] ERROR: Nighty.exe not found in /home/container!"
    echo "[!] Please upload your legal 'Nighty.exe' to the server root via SFTP and restart."
    exit 1
fi

# 2. Ensure Astral uv is available (for rootless Python 3.14 toolchains)
if ! command -v uv &>/dev/null; then
    echo "[+] Installing user-space uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# Ensure Python 3.14 is pulled into the isolated uv cache
echo "[+] Ensuring Python 3.14 runtime is installed via uv..."
uv python install 3.14 || true

# 3. Initialize Wineprefix in Windows 10 mode (Python 3.14 requirement)
if [ ! -d "$WINEPREFIX" ]; then
    echo "[+] Initializing 64-bit Wine prefix for Windows 10..."
    wineboot -i
    wine reg add 'HKCU\Software\Wine' /v Version /t REG_SZ /d 'win10' /f >/dev/null 2>&1 || true
fi

# 4. Check if repacking into headless stub is required
REPACK_NEEDED=0
if [ ! -f "Nighty_stub.exe" ]; then
    REPACK_NEEDED=1
elif [ -f "Nighty.exe" ] && [ "Nighty.exe" -nt "Nighty_stub.exe" ]; then
    echo "[!] Detected a newer Nighty.exe. Re-patching stub..."
    REPACK_NEEDED=1
fi

if [ "$REPACK_NEEDED" = "1" ]; then
    echo "[+] Generating Nighty_stub.exe using Python 3.14 repacker..."
    if [ -f "scripts/repack.py" ]; then
        uv run --python 3.14 python3 scripts/repack.py
    elif [ -f "scripts/install.sh" ]; then
        # Run upstream repack skipping system-wide sudo commands
        bash scripts/install.sh --no-wine-install || bash scripts/install.sh || true
    fi

    # Fallback guard
    if [ ! -f "Nighty_stub.exe" ] && [ -f "Nighty.exe" ]; then
        echo "[!] Stub generation bypassed; fallback to direct binary."
        cp Nighty.exe Nighty_stub.exe
    fi
fi

# 5. Inject Pterodactyl's dynamic SERVER_PORT into .env
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        touch .env
    fi
fi

# Strip any existing port bindings and write Pterodactyl allocation
sed -i '/^PORT=/d' .env
sed -i '/^BRIDGE_PORT=/d' .env
sed -i '/^TARGET_PORT=/d' .env
sed -i '/^HOST=/d' .env

echo "HOST=0.0.0.0" >> .env
echo "PORT=${SERVER_PORT}" >> .env
echo "BRIDGE_PORT=${SERVER_PORT}" >> .env
echo "TARGET_PORT=8090" >> .env

# Set Web UI credentials if configured
if [ -n "$WEB_USERNAME" ]; then
    sed -i '/^NIGHTY_USER=/d' .env
    sed -i '/^WEB_USERNAME=/d' .env
    echo "NIGHTY_USER=${WEB_USERNAME}" >> .env
    echo "WEB_USERNAME=${WEB_USERNAME}" >> .env
fi

if [ -n "$WEB_PASSWORD" ]; then
    sed -i '/^NIGHTY_PASS=/d' .env
    sed -i '/^WEB_PASSWORD=/d' .env
    echo "NIGHTY_PASS=${WEB_PASSWORD}" >> .env
    echo "WEB_PASSWORD=${WEB_PASSWORD}" >> .env
fi

echo "[✓] Environment configured: Bridge Proxy listening on 0.0.0.0:${SERVER_PORT}"

# 6. Launch upstream orchestrator in non-interactive terminal mode ('once')
echo "[✓] Launching Nighty Headless Stack..."
exec bash scripts/run.sh once
