#!/data/data/com.termux/files/usr/bin/bash
# Fetch the press-pack files and fonts the ad is built from. They are not kept in this
# repository: the ad takes make.fun's badge and end card straight from the press pack,
# as the bounty requires, and the typefaces are the two the press pack names.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p assets

BASE=https://make.fun/press
get() { echo "  $2"; curl -sS --max-time 90 -L -o "assets/$2" "$1"; }

echo "press pack (manifest: $BASE/manifest.json)"
get "$BASE/brand-badge/9x16/makefun-badge-9x16.png"             makefun-badge-9x16.png
get "$BASE/referral-card/9x16/makefun-card-9x16-transparent.webm" card9x16.webm
get "$BASE/referral-card/stills/2-logo.png"                     logo.png
get "$BASE/referral-card/stills/3-wordmark.png"                 wordmark.png

echo "typefaces (press type.txt: Inter Display Bold, JetBrains Mono Bold; both OFL)"
get "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf" Inter-VF.ttf
get "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Bold.ttf" JetBrainsMono-Bold.ttf

echo "done"
