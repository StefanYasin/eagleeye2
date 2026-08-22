#!/usr/bin/env bash
# try-eagleeye.sh — one-command launcher for eagleeye2 (WSL2)
# Usage:  bash try-eagleeye.sh <photo> <"Full Name"> [sites]
# Example: bash try-eagleeye.sh ~/Pictures/suspect.jpg "John Smith" instagram,threads,x,github,linkedin,youtube,telegram

set -euo pipefail

PHOTO="${1:-}"
NAME="${2:-}"
SITES="${3:-instagram,threads,x,tiktok,github,reddit,linkedin,youtube,telegram,steam,spotify,twitch}"

if [ -z "$PHOTO" ]; then
  echo "Usage: bash try-eagleeye.sh <photo> <\"Full Name\"> [sites]"
  echo "Example: bash try-eagleeye.sh ~/Pictures/face.jpg \"John Smith\""
  exit 1
fi

REPO="C:/Users/Stefan/AppData/Local/Temp/roadmap-work/eagleeye2"
WSL_PATH="/mnt/c/Users/Stefan/AppData/Local/Temp/roadmap-work/eagleeye2"
PURPOSE="${4:-research}"

# Convert Windows path to WSL path if needed
case "$PHOTO" in
  C:*|/c/*) WSL_PHOTO=$(echo "$PHOTO" | sed 's|^C:|/mnt/c|; s|^/c/|/mnt/c/|; s|\\|/|g') ;;
  *) WSL_PHOTO="$PHOTO" ;;
esac

echo "🔍 eagleeye2 — scanning $NAME"
echo "   photo: $WSL_PHOTO"
echo "   sites: $SITES"
echo "   purpose: $PURPOSE (ethics gate)"
echo ""

# Ensure WSL is up
wsl.exe -e bash -lc "true" >/dev/null 2>&1 || { echo "❌ WSL not available"; exit 1; }

wsl.exe -e bash -lc "cd $WSL_PATH && .venv-wsl/bin/python -m eagleeye2.cli scan --photo '$WSL_PHOTO' --name '$NAME' --sites '$SITES' --purpose '$PURPOSE' --out /tmp/ee_report.json" | tr -d '\0'

echo ""
echo "📄 Full JSON report: $REPO/scan_report.json"
