#!/data/data/com.termux/files/usr/bin/bash
# Render the make.fun TikTok ad end to end:
#   1. frames + motion from make_ad.py -> build/clip.mp4
#   2. brand badge (press pack, as it is) over the whole clip from frame 0
#   3. referral end card (press pack) over the last 2.5 s, referral code typed in
#   4. final ad.mp4 (1080x1920, 30 fps, H.264)
set -euo pipefail
cd "$(dirname "$0")"

unset LD_LIBRARY_PATH
export LD_PRELOAD="/data/data/com.termux/files/usr/lib/libtermux-exec-ld-preload.so:/data/data/com.termux/files/usr/lib/libpython3.14.so"

PY="$HOME/airdrop-agent/.venv/bin/python"
mkdir -p build

CODE="01t19cz4"
BADGE="assets/makefun-badge-9x16.png"
CARD="assets/card9x16.webm"
FONT="assets/JetBrainsMono-Bold.ttf"

echo "== 1/3 frames -> build/clip.mp4"
"$PY" make_ad.py

D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 build/clip.mp4)
T=$(awk "BEGIN{print $D-2.5}")          # card comes in 2.5 s before the clip ends
LAST=$(awk "BEGIN{print $D-2.5}")       # badge ends exactly where the end card comes in

echo "== 2/3 badge + card overlay (clip ${D}s, card in at ${T}s)"
ffmpeg -hide_banner -loglevel error -y \
  -i build/clip.mp4 \
  -loop 1 -i "$BADGE" \
  -c:v libvpx-vp9 -i "$CARD" \
  -filter_complex "\
[0:v]scale=1080:1920,setsar=1,fps=30[clip];\
[1:v]format=rgba[badge];\
[clip][badge]overlay=x=0:y=0:shortest=1:enable='lt(t,$LAST)'[bg];\
[bg]split[soft_in][hard];\
[soft_in]gblur=sigma=28,eq=saturation=0.35,format=yuva420p,fade=t=in:st=$T:d=0.8:alpha=1[soft];\
[hard][soft]overlay[wash0];\
[2:v]format=yuva420p,setpts=PTS-STARTPTS+$T/TB[card];\
[wash0][card]overlay=eof_action=pass,\
drawbox=x=208:y=1230:w=9:h=82:color=white:t=fill:enable='gte(t,$T+1.433)',\
drawtext=fontfile=$FONT:text=$CODE:fontsize=62:fontcolor=0x191419:x=210:y=1271-(ascent-descent)/2:enable='gte(t,$T+1.433)'[v]" \
  -map "[v]" -an -t "$D" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart \
  build/ad_silent.mp4

echo "== 3/3 sound bed + mux -> build/ad.mp4"
# A quiet synth pad under the whole clip: two low sines, a slow swell, faded at both ends.
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "aevalsrc=(0.055*sin(2*PI*110*t)+0.045*sin(2*PI*164.81*t)+0.035*sin(2*PI*220*t))*(0.55+0.45*sin(2*PI*0.25*t)):s=44100:d=$D" \
  -f lavfi -i "anoisesrc=color=pink:amplitude=0.012:d=$D:s=44100" \
  -filter_complex "[0:a]lowpass=f=900,volume=0.9[a0];[1:a]lowpass=f=2400,volume=0.55[a1];[a0][a1]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.7,afade=t=in:st=0:d=1.2,afade=t=out:st=$(awk "BEGIN{print $D-2.6}"):d=2.6,aresample=44100[a]" \
  -map "[a]" -c:a aac -b:a 128k -ac 2 build/bed.m4a

ffmpeg -hide_banner -loglevel error -y -i build/ad_silent.mp4 -i build/bed.m4a \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 128k -shortest -movflags +faststart build/ad.mp4

echo "== done"
ffprobe -hide_banner -v error -show_entries format=duration,size -show_entries stream=width,height,r_frame_rate,codec_name -of default=nw=1 build/ad.mp4
ls -l build/ad.mp4
