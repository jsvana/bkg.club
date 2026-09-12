# Talk: 2m CW on a $30 Handheld

A club-meeting deck on modifying the Quansheng UV-K1 for 2m CW with the NR7Y
firmware, closing with a short pitch for the Brass Knuckle Gang.

- `quansheng-2m-cw.pptx` is the deck (19 slides, 16:9, speaker notes on every
  slide). Presenter: Justin, N9HO. First given at the CCARA monthly meeting, September 12, 2026.
- `build.js` regenerates it with [pptxgenjs](https://github.com/gitbrent/PptxGenJS):
  `npm install pptxgenjs react react-dom react-icons sharp && node build.js`.

## Sources and credits

- Rework photos and schematic in `img/` come from the
  [NR7Y CW Firmware Docs](https://briand.github.io/cw-firmware-docs/),
  licensed CC BY-NC-SA 4.0. The original K5 schematic was reverse-engineered
  by mentalDetector.
- Firmware: NR7Y's CW mod on F4HWN Fusion, which descends from egzumer and
  DualTachyon (Apache 2.0).
- Gang content comes from bkg.club (`clubs.html`, `safety.html`, `index.html`).
