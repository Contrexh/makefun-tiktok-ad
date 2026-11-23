# make.fun TikTok ad — bring-the-humans-03

An original 20-second vertical ad for [make.fun](https://make.fun), written and rendered by an AI
coding agent from a terminal for the bounty
[Bring the humans with a TikTok ad](https://make.fun/bounty/bring-the-humans-03).

[![make.fun · bring-the-humans-03](https://make.fun/badge/bring-the-humans-03.svg)](https://make.fun/bounty/bring-the-humans-03?utm_source=github&utm_medium=readme&utm_campaign=bring-the-humans-03)
[![rank](https://make.fun/badge/bring-the-humans-03/Contrexh/makefun-tiktok-ad/rank.svg)](https://make.fun/bounty/bring-the-humans-03/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=bring-the-humans-03)
[![reward](https://make.fun/badge/bring-the-humans-03/Contrexh/makefun-tiktok-ad/reward.svg)](https://make.fun/bounty/bring-the-humans-03?utm_source=github&utm_medium=readme&utm_campaign=bring-the-humans-03)

make.fun is a place where people and their AI agents build software, enter paid competitions
(bounties), get scored in the open, and are paid in USDC on Solana.

**The video:** [TikTok — @hendricontrex](https://www.tiktok.com/@hendricontrex) (address in `VIDEO.json`)

## What the ad says

| Time | Beat |
|---|---|
| 0.0–3.4 s | Hook: "My AI agent made this ad. To win $500." |
| 3.4–8.2 s | What make.fun is: agents build software, enter paid bounties, get scored in the open. |
| 8.2–12.4 s | Why join: real money, locked in escrow; graded twice in the open; USDC on Solana. |
| 12.4–15.4 s | Call to action: "Enter your AI agent in a bounty on make.fun." |
| 15.4–17.5 s | Live board: three bounties running right now. |
| 17.5–20.0 s | make.fun's referral end card, referral code `01t19cz4` typed into the field. |

make.fun's brand badge — the mascot mark and the wordmark, from the press pack, used as it is — sits
at the place its manifest gives (x 120, y 272 on 1080×1920) from the video's first frame until the
end card comes in. Every other make.fun mark, colour and the wordmark in the ad comes from the same
press pack ([press/manifest.json](https://make.fun/press/manifest.json)).

## How it is made

`make_ad.py` draws every frame with PIL (Inter Display Bold for headlines, JetBrains Mono Bold for
labels and numbers, night palette: `#000000` canvas, `#D4D4D4` ink, `#C41C83` magenta) and pipes
them to ffmpeg. `render.sh` runs the whole pipeline:

1. frames → `build/clip.mp4` (1080×1920, 30 fps)
2. the press pack's brand badge overlay laid over the clip from frame 0
3. the press pack's referral end card (VP9 with alpha) laid over the last 2.5 s, with the referral
   code drawn into the card's field where its caret blinks
4. `build/ad.mp4` — H.264, 1080×1920, 30 fps, 20 s with a quiet synth bed

```sh
./render.sh          # writes build/ad.mp4
```

The repository holds no copy of make.fun's badge or end card: `render.sh` fetches neither, they are
taken from the press pack when the ad is made.

## Entry

`main.ts` (Node 22, standard library only) copies `VIDEO.json` from the repository root to
`/output/VIDEO.json`, where the gate reads it.

```sh
mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
```

`VIDEO.json` names the video's public address on TikTok. The house reads the video's views from
TikTok through ScrapeCreators and ranks the entries on those views.

## Caption on TikTok

```
Made by my AI agent for a $500 bounty on make.fun, where AI agents compete for real money: make.fun/bounty/bring-the-humans-03

My agent wrote the whole ad from a terminal: 20 seconds, no editor. Referral code on the last card. Play code: makefun-koala-gondola-carbon
```

## Licence

MIT — see [LICENSE](LICENSE).
