#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# nighty-linux-headless — installer (Pterodactyl Container Patched)
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

if [ -f "$(dirname "${BASH_SOURCE[0]}")/Nighty.exe" ] || [ -f "$(dirname "${BASH_SOURCE[0]}")/.env.example" ]; then
  HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

PREFLIGHT="$HERE/scripts/preflight.py"
cd "$HERE"

if [ -t 1 ]; then B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; C=$'\033[36m'; R=$'\033[31m'; N=$'\033[0m'; else B=; G=; Y=; C=; R=; N=; fi
ok()   { printf '  %s✓%s %s\n' "$G" "$N" "$*"; }
add()  { printf '  %s+%s %s\n' "$Y" "$N" "$*"; }
info() { printf '%s==>%s %s\n' "$C" "$N" "$*"; }
warn() { printf '  %s!%s %s\n' "$Y" "$N" "$*"; }
die()  { printf '%sERROR:%s %s\n' "$R" "$N" "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1; }

printf '\n%snighty-linux-headless installer (container mode)%s\n\n' "$B" "$N"

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) IS_X86=1; info "Architecture: $ARCH — Native Wine." ;;
  *)            IS_X86=0; info "Architecture: $ARCH — Box64 Emulation." ;;
esac

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  if need sudo; then SUDO="sudo"; else warn "Running inside container as non-root. Using pre-installed packages."; fi
fi

set_kv() {
  if grep -qE "^$2=" "$1" 2>/dev/null; then
    local esc; esc="$(printf '%s' "$3" | sed -e 's/[\/&|]/\\&/g')"
    sed -i "s|^$2=.*|$2=$esc|" "$1"
  else
    printf '%s=%s\n' "$2" "$3" >> "$1"
  fi
}

# Ensure .env
if [ ! -f .env ]; then
  cp .env.example .env
  add "created .env"
else
  ok ".env exists"
fi
set -a; [ -f ./.env ] && . ./.env; set +a

info "Checking base tools…"
need tar && ok "tar present" || warn "tar check skipped"
need python3 && ok "Python 3 present" || warn "Python 3 missing"
need Xvfb && ok "Xvfb present" || warn "Xvfb missing"

# Setup uv for Python 3.8
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
if need uv; then
  ok "uv present"
else
  add "uv missing — installing..."
  if need curl; then curl -LsSf https://astral.sh/uv/install.sh | sh
  else wget -qO- https://astral.sh/uv/install.sh | sh; fi
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  need uv && ok "uv installed" || warn "uv installation attempted"
fi

WINE_BIN_RESOLVED=""
NIGHTY_HOME="${NIGHTY_HOME:-$HOME/.local/share/nighty}"
mkdir -p "$NIGHTY_HOME" 2>/dev/null || true

bin="$(command -v wine64 || command -v wine || true)"
if [ -n "$bin" ]; then
  ok "Wine present: $bin"
  WINE_BIN_RESOLVED="$bin"
else
  die "Wine not found. Make sure your Egg uses ghcr.io/parkervcp/yolks:wine_latest."
fi

set_kv .env NIGHTY_HOME "$NIGHTY_HOME"
set_kv .env WINEPREFIX  "$NIGHTY_HOME/prefix"
set_kv .env WINE_BIN "$WINE_BIN_RESOLVED"

SRC="${NIGHTY_EXE:-$HERE/Nighty.exe}"
OUT="${NIGHTY_STUB:-$HERE/Nighty_stub.exe}"
case "$SRC" in /*) : ;; ./*) SRC="$HERE/${SRC#./}" ;; esac
case "$OUT" in /*) : ;; ./*) OUT="$HERE/${OUT#./}" ;; esac

if [ ! -f "$SRC" ]; then
  die "Nighty.exe missing from root folder. Upload your licensed Nighty.exe."
fi

info "Ensuring Python 3.8 for stub repacking…"
uv python install 3.8 >/dev/null 2>&1 || true
PY38="$(uv python find 3.8 2>/dev/null || command -v python3)"
ok "Python for repack: $PY38"

info "Repacking $(basename "$SRC") → $(basename "$OUT")…"
NIGHTY_EXE="$SRC" NIGHTY_STUB="$OUT" "$PY38" scripts/repack.py "$SRC" "$OUT" || die "Repack failed."
ok "Repack completed: $OUT"

printf '\n%sContainer setup complete.%s\n\n' "$G" "$N"
