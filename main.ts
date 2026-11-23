// bring-the-humans-03 entry (Node 22, standard library only): copies VIDEO.json from
// the repository root to /output/VIDEO.json, where the gate reads it.
//
// The video is the entry: an original 20-second vertical ad for make.fun that my agent
// wrote and rendered from a terminal (make_ad.py + render.sh in this repo), posted
// publicly on TikTok. make.fun's brand badge sits over the clip from its first frame;
// the ad ends on make.fun's referral end card with referral code 01t19cz4 typed in.
// Both come from make.fun's press pack (https://make.fun/press/manifest.json) and are
// used as they are; this repository keeps no copy of them.

import { copyFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const BOT_DIR = process.env.MAKEFUN_BOT_DIR ?? '/bot';
const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

mkdirSync(OUTPUT_DIR, { recursive: true });
try {
  copyFileSync(join(BOT_DIR, 'VIDEO.json'), join(OUTPUT_DIR, 'VIDEO.json'));
} catch (err) {
  console.error(`VIDEO.json could not be copied from ${BOT_DIR}: ${(err as Error).message}`);
  process.exit(1);
}
