#!/usr/bin/env bash

# Clear container startup boilerplate
clear

# ── Dynamically extract BRIDGE_PORT from .env (no hardcoded ports) ──
BRIDGE_PORT=""
if [ -f .env ]; then
  BRIDGE_PORT="$(grep -E '^BRIDGE_PORT=' .env | cut -d '=' -f2 | tr -d ' "\r')"
fi
BRIDGE_PORT="${BRIDGE_PORT:-${PORT:-8088}}"

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

# Ensure nighty.log exists
touch nighty.log

# Stream bot logs into the Pterodactyl console in real-time
tail -n 0 -F nighty.log &
TAIL_PID=$!

# Handle graceful container termination
trap "kill $TAIL_PID 2>/dev/null; exit 0" SIGINT SIGTERM EXIT

# Start backend runner
bash scripts/run.sh once 2> >(grep -v "_XSERVTransmkdir" >&2)
