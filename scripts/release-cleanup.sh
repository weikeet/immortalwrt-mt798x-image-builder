#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ] || [ -z "${1:-}" ]; then
  echo "Usage: $0 <device_prefix> [keep_count]" >&2
  exit 1
fi

DEVICE_PREFIX="$1"
KEEP_COUNT="${2:-5}"

if ! [[ "$KEEP_COUNT" =~ ^[0-9]+$ ]] || [ "$KEEP_COUNT" -lt 1 ]; then
  echo "ERROR: keep_count must be a positive integer, got: $KEEP_COUNT" >&2
  exit 1
fi

if [ -z "${GITHUB_REPOSITORY:-}" ]; then
  echo "ERROR: GITHUB_REPOSITORY is not set" >&2
  exit 1
fi

RELEASES_JSON="$(gh release list --repo "$GITHUB_REPOSITORY" --limit 100 --json tagName,createdAt)"

TAGS_TO_DELETE="$(RELEASES_JSON="$RELEASES_JSON" DEVICE_PREFIX="$DEVICE_PREFIX" KEEP_COUNT="$KEEP_COUNT" python3 - <<'PY'
import json
import os

releases = json.loads(os.environ["RELEASES_JSON"])
prefix = os.environ["DEVICE_PREFIX"] + "-"
keep = int(os.environ["KEEP_COUNT"])

matched = [r for r in releases if r.get("tagName", "").startswith(prefix)]
matched.sort(key=lambda r: r.get("createdAt", ""), reverse=True)

for item in matched[keep:]:
    print(item["tagName"])
PY
)"

if [ -z "$TAGS_TO_DELETE" ]; then
  echo "No old releases to delete for prefix '${DEVICE_PREFIX}-' (keep=${KEEP_COUNT})."
  exit 0
fi

while IFS= read -r tag; do
  [ -n "$tag" ] || continue
  echo "Deleting old release and tag: $tag"
  gh release delete "$tag" --repo "$GITHUB_REPOSITORY" --cleanup-tag --yes
done <<< "$TAGS_TO_DELETE"
