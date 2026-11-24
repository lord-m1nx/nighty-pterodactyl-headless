#!/usr/bin/env bash
#
# add_account.sh — add another Discord account to a headless Nighty install.
#
# A headless box has no desktop window, so the "config window" is the Web UI.
# This script puts the bridge into add-account mode: it re-serves the setup
# wizard, retitled "Add account", even though the box is already onboarded. You
# complete the SAME flow as the first run — License -> account token -> bot token
# -> OAuth — in the browser. The bridge validates each step against Discord,
# enforces the OAuth gate, writes the new login straight into nighty.config, then
# restarts Nighty on the new account. Ctrl+C cancels and restores the panel.
#
# Lifecycle: safe-pause the live panel -> retitled config wizard -> identical
# validation + OAuth -> direct write to nighty.config -> restart on new account.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

# Host/port from the same .env the rest of the stack uses.
. "$ROOT/scripts/env_file.sh"
nighty_load_env_file "$ROOT/.env"
BRIDGE_PORT="${BRIDGE_PORT:-8088}"

# Resolve Nighty's appdata via the shared helper (needs the wine prefix env,
# which .env provides).
APPDATA="$(cd "$HERE" && python3 -c 'import enforce_config as e; print(e.find_appdata() or "")')"
if [ -z "$APPDATA" ] || [ ! -d "$APPDATA" ]; then
  echo "[add-account] Nighty appdata not found. Install Nighty and let it run once first." >&2
  exit 1
fi
MARKER="$APPDATA/.add_account"
CONFIG="$APPDATA/nighty.config"

cleanup() { rm -f "$MARKER" 2>/dev/null || true; }
trap 'echo; echo "[add-account] cancelled — the normal panel is restored."; cleanup; exit 130' INT TERM

accounts() {
  python3 - "$CONFIG" <<'PY' 2>/dev/null || echo "?"
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception:
    print("?"); raise SystemExit
L = d.get("logins") or {}
act = [u for u, i in L.items() if isinstance(i, dict) and i.get("active")]
print("%d account(s); active: %s" % (len(L), ", ".join(act) if act else "none"))
PY
}

echo "[add-account] Current: $(accounts)"

# 1) Safe-pause the live panel by entering add-account mode. The running backend
#    is left untouched until the new account is provisioned (which restarts it).
: > "$MARKER"
echo "[add-account] Add-account mode is ON (the live panel is paused)."

# 2) Point the user at the retitled config wizard.
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"; [ -n "$IP" ] || IP="<this-host-ip>"
cat <<EOF

  Open the Web UI and complete "Adding an additional account":

      http://$IP:$BRIDGE_PORT/

  Same steps as the first run: license, account token, bot token, then authorize
  the bot on Discord. Waiting for you to finish (Ctrl+C to cancel)…
EOF

# 3) Wait until the wizard provisions the account — the bridge clears the marker
#    on a successful /provision.
while [ -f "$MARKER" ]; do sleep 3; done

# 4) Confirm.
echo
echo "[add-account] Done — new account provisioned."
echo "[add-account] Now: $(accounts)"
echo "[add-account] Nighty is restarting on the new account (about 90 seconds)."
