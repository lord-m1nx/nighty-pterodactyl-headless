#!/usr/bin/env bash
# Pterodactyl entrypoint for Nighty Headless.
# The primary Pterodactyl allocation is exposed as SERVER_PORT; keep .env in
# sync so scripts/run.sh and bridge.py always use the port actually assigned
# to this server.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

clear 2>/dev/null || true

# Create the runtime environment file when the user has not created one yet.
if [ ! -f .env ]; then
  if [ ! -f .env.example ]; then
    echo "[start] FATAL: .env and .env.example are both missing." >&2
    exit 1
  fi
  cp .env.example .env
fi

# Pterodactyl already exports the server's primary allocation as SERVER_PORT.
# Keep PORT as a compatibility fallback for installations made with older eggs.
BRIDGE_PORT="${SERVER_PORT:-${PORT:-8088}}"
case "$BRIDGE_PORT" in
  ''|*[!0-9]*)
    echo "[start] FATAL: invalid bridge port: '$BRIDGE_PORT'" >&2
    exit 1
    ;;
esac
if [ "$BRIDGE_PORT" -lt 1 ] || [ "$BRIDGE_PORT" -gt 65535 ]; then
  echo "[start] FATAL: bridge port is outside the valid range: $BRIDGE_PORT" >&2
  exit 1
fi

# scripts/run.sh reloads .env, so persist the Pterodactyl allocation there
# rather than only exporting it in this wrapper process.
if grep -q '^BRIDGE_PORT=' .env; then
  sed -i "s/^BRIDGE_PORT=.*/BRIDGE_PORT=$BRIDGE_PORT/" .env
else
  printf '\nBRIDGE_PORT=%s\n' "$BRIDGE_PORT" >> .env
fi
export BRIDGE_PORT

# ── Centered Blue → Cyan Gradient ASCII Banner ──
echo -e "\033[1m"
echo -e "\033[38;2;26;95;255m   ███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗██╗   ██╗"
echo -e "\033[38;2;21;133;255m   ████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝╚██╗ ██╔╝"
echo -e "\033[38;2;15;168;255m   ██╔██╗ ██║██║██║  ███╗███████║   ██║    ╚████╔╝ "
echo -e "\033[38;2;10;202;255m   ██║╚██╗██║██║██║   ██║██╔══██║   ██║     ╚██╔╝  "
echo -e "\033[38;2;5;231;255m   ██║ ╚████║██║╚██████╔╝██║  ██║   ██║      ██║   "
echo -e "\033[38;2;0;255;255m   ╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝      ╚═╝   \033[0m"
echo ""
echo -e "   \033[38;2;0;180;255m─────────────────────────────────────────────────────────────\033[0m"
echo -e "   \033[38;2;100;210;255m✦ Status:\033[0m      \033[32m● Running 24/7 Headless\033[0m"
echo -e "   \033[38;2;100;210;255m✦ Web UI Port:\033[0m \033[36m${BRIDGE_PORT}\033[0m"
echo -e "   \033[38;2;100;210;255m✦ Access URL:\033[0m  \033[36mhttp://<server-ip>:${BRIDGE_PORT}/\033[0m"
echo -e "   \033[38;2;100;210;255m✦ Platform:\033[0m    \033[35mWine 11 (Headless Linux)\033[0m"
echo -e "   \033[38;2;0;180;255m─────────────────────────────────────────────────────────────\033[0m"
echo ""
echo -e "   \033[90m[Live Discord logs streaming below...]\033[0m"
echo ""

# Nighty's mirrored application log lives in diagnostics/nighty.log.
mkdir -p diagnostics
touch diagnostics/nighty.log
tail -n 0 -F diagnostics/nighty.log &
TAIL_PID=$!
RUNNER_PID=""

cleanup_tail() {
  kill "$TAIL_PID" 2>/dev/null || true
  wait "$TAIL_PID" 2>/dev/null || true
}

forward_signal() {
  local sig="$1"
  [ -n "$RUNNER_PID" ] && kill "-$sig" "$RUNNER_PID" 2>/dev/null || true
}

trap cleanup_tail EXIT
trap 'forward_signal INT' INT
trap 'forward_signal TERM' TERM

# Run the backend through the existing upstream orchestrator. Running it as a
# child lets this wrapper forward Pterodactyl stop signals and still clean up
# the log-tail process. Preserve the runner's real exit status.
bash scripts/run.sh once 2> >(grep -v "_XSERVTransmkdir" >&2) &
RUNNER_PID=$!
wait "$RUNNER_PID"
RUNNER_RC=$?
exit "$RUNNER_RC"
