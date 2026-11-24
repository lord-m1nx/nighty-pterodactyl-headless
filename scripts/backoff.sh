#!/usr/bin/env bash

NIGHTY_BACKOFF_MAX_SHIFT=10

nighty_relaunch_delay() {
  local fast_failures="$1" cap="$2" base="${3:-3}" shift_by delay
  if [ "$fast_failures" -lt 2 ]; then
    printf '%s' "$base"
    return 0
  fi
  shift_by=$((fast_failures - 1))
  [ "$shift_by" -gt "$NIGHTY_BACKOFF_MAX_SHIFT" ] && shift_by="$NIGHTY_BACKOFF_MAX_SHIFT"
  delay=$((base * (1 << shift_by)))
  [ "$delay" -gt "$cap" ] && delay="$cap"
  printf '%s' "$delay"
}
