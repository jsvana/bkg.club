const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const path = require("path");
const IMG = path.join(__dirname, "img");

// ---------- palette ----------
const C = {
  bg: "141210", card: "211D19", card2: "2A2520", brass: "D4AF37", brassLt: "F0D27A",
  cream: "F2EBDD", muted: "B3A995", dim: "7D7466", warn: "E0553D", ok: "5FBF7A", ink: "141210",
};
const HEAD = "Cambria", BODY = "Calibri";
const W = 13.333, H = 7.5, M = 0.6;

async function icon(Name, color, px = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[Name], { color: "#" + color, size: px }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Brass Knuckle Gang";
pres.title = "2m CW on a $30 Handheld";

function base(notes) {
  const s = pres.addSlide();
  s.background = { color: C.bg };
  if (notes) s.addNotes(notes);
  return s;
}
function title(s, text, opts = {}) {
  s.addText(text, { x: M, y: 0.42, w: W - 2 * M, h: 0.9, fontFace: HEAD, fontSize: opts.size || 36, bold: true,
    color: C.brassLt, isTextBox: true, margin: 0, valign: "middle" });
  if (opts.sub) s.addText(opts.sub, { x: M, y: 1.3, w: W - 2 * M, h: 0.45, fontFace: BODY, fontSize: 16,
    color: C.muted, italic: true, isTextBox: true, margin: 0, valign: "top" });
}
function card(s, x, y, w, h, fill = C.card) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.12 });
}
function numCircle(s, n, x, y, d = 0.5) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: C.brass }, line: { color: C.brass } });
  s.addText(String(n), { x, y, w: d, h: d, fontFace: HEAD, fontSize: d >= 0.5 ? 16 : 13, bold: true, color: C.ink,
    align: "center", valign: "middle", isTextBox: true, margin: 0 });
}
function iconCircle(s, data, x, y, d = 0.62) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: C.brass }, line: { color: C.brass } });
  const p = d * 0.27;
  s.addImage({ data, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
}
function body(s, text, x, y, w, h, o = {}) {
  s.addText(text, { x, y, w, h, fontFace: BODY, fontSize: o.size || 15, color: o.color || C.cream, isTextBox: true,
    margin: 0, valign: o.valign || "top", align: o.align || "left", bold: !!o.bold, italic: !!o.italic, lineSpacingMultiple: 1.1 });
}
function bullets(s, items, x, y, w, h, o = {}) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: i < items.length - 1, paraSpaceAfter: o.gap || 6 } })),
    { x, y, w, h, fontFace: BODY, fontSize: o.size || 15, color: o.color || C.cream, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.05 });
}
function h3(s, text, x, y, w, o = {}) {
  s.addText(text, { x, y, w, h: 0.4, fontFace: HEAD, fontSize: o.size || 20, bold: true, color: o.color || C.brass, isTextBox: true, margin: 0, valign: "middle" });
}
function foot(s, text) {
  s.addText(text, { x: M, y: H - 0.5, w: W - 2 * M, h: 0.3, fontFace: BODY, fontSize: 10, color: C.dim, isTextBox: true, margin: 0, valign: "middle" });
}

(async () => {
  const I = {
    radio: await icon("FaBroadcastTower", C.ink), key: await icon("FaKeyboard", C.ink), users: await icon("FaUsers", C.ink),
    tools: await icon("FaTools", C.ink), bolt: await icon("FaBolt", C.ink), micro: await icon("FaMicrochip", C.ink),
    wave: await icon("FaWaveSquare", C.ink), vol: await icon("FaVolumeUp", C.ink), save: await icon("FaSave", C.ink),
    eye: await icon("FaEye", C.ink), grad: await icon("FaGraduationCap", C.ink), filter: await icon("FaFilter", C.ink),
    exch: await icon("FaExchangeAlt", C.ink), warn: await icon("FaExclamationTriangle", C.ink), map: await icon("FaMapMarkerAlt", C.ink),
    money: await icon("FaDollarSign", C.ink), plug: await icon("FaPlug", C.ink), hand: await icon("FaHandRock", C.ink),
    usb: await icon("FaUsb", C.ink), flash: await icon("FaDownload", C.ink), check: await icon("FaCheck", C.ink),
    link: await icon("FaLink", C.ink), skull: await icon("FaSkullCrossbones", C.ink), fist: await icon("FaFistRaised", C.ink),
  };

  // ---------- 1. Title ----------
  {
    const s = base("Open with the radio in your hand. Hold it up. Tell them it cost thirty dollars, it does real CW, and the goal is that they go home wanting to build one. This is a pitch, not a build night: nobody is soldering tonight. It is about one goal: more operators sending Morse on 2 meters than there were last year. Everything else is a side effect.");
    s.addImage({ path: path.join(IMG, "k1_wires.jpg"), x: 8.45, y: 0.55, w: 4.24, h: 6.4 });
    s.addText("2m CW on a\n$30 Handheld", { x: M, y: 1.2, w: 7.5, h: 2.4, fontFace: HEAD, fontSize: 54, bold: true, color: C.brassLt, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 0.95 });
    body(s, "Modifying the Quansheng UV-K1 for real Morse code: the why, the how, the tools, and the parts.", M, 3.85, 7.3, 1.0, { size: 20, color: C.cream });
    body(s, "Justin · N9HO", M, 5.6, 7.3, 0.4, { size: 16, color: C.muted });
    body(s, "CCARA Monthly Meeting · September 12, 2026", M, 6.0, 7.3, 0.4, { size: 14, color: C.dim });
  }

  // ---------- 2. Tonight ----------
  {
    const s = base("Roadmap. This is an interest talk, not a workshop, so keep the rework steps brisk and visual. Spend most of the time on the middle three: the firmware, the mod, and getting on the air. The gang is the closer, keep it to a couple of minutes.");
    title(s, "Tonight");
    const items = [
      ["Why 2 meter CW", "The band is empty, and this mode is local by physics."],
      ["Why this radio", "Thirty dollars, everywhere, and fully open-source firmware."],
      ["The firmware", "What NR7Y's CW mod turns the radio into."],
      ["The mod", "Tools, parts, and the two-resistor, two-wire rework."],
      ["Flash, set up, get on the air", "uvtools2, the CW menu, and 144.025."],
      ["The Brass Knuckle Gang", "Who we are and how you get a number."],
    ];
    items.forEach(([t, d], i) => {
      const y = 1.75 + i * 0.86;
      numCircle(s, i + 1, M, y + 0.03);
      body(s, t, M + 0.7, y, 6.0, 0.4, { size: 19, bold: true, color: C.cream });
      body(s, d, M + 0.7, y + 0.4, 6.0, 0.4, { size: 14, color: C.muted });
    });
    card(s, 7.9, 1.75, 4.83, 5.1);
    const stats = [["$30", "the radio"], ["2", "resistors off"], ["2", "wires on"], ["1", "evening"]];
    stats.forEach(([n, l], i) => {
      const y = 1.95 + i * 1.22;
      s.addText(n, { x: 8.1, y, w: 2.0, h: 1.0, fontFace: HEAD, fontSize: 48, bold: true, color: C.brass, isTextBox: true, margin: 0, align: "right", valign: "middle" });
      body(s, l, 10.3, y, 2.3, 1.0, { size: 18, color: C.cream, valign: "middle" });
    });
  }

  // ---------- 3. Why 2m CW ----------
  {
    const s = base("Three reasons, and the second-order effects are the real pitch to a club. An active band is easier to defend than an empty one. Two meters with a handheld is local, so your contacts are people close enough to have breakfast with, and the recruiting mechanism is by physics community building. And nobody's hands shake over a thirty dollar radio, so people actually open one.");
    title(s, "Why 2 meter CW?", { sub: "One goal: more operators sending Morse on 144 MHz than last year. These are the side effects." });
    const cols = [
      [I.wave, "The band is empty", "Outside a few repeaters and a net or two, two meters goes days without a signal. The weak-signal end goes weeks.\n\nAn active band is far easier to defend than an empty one. Every contact is evidence, and it costs you an evening."],
      [I.map, "It is local, by physics", "With a handheld and a modest antenna, 2m CW reaches the hams around you, not strangers a thousand miles away.\n\nYou cannot grow this without meeting your neighbors: back to the club, talk friends into a radio, get on the air together."],
      [I.tools, "Nobody fears a $30 radio", "The barrier to tinkering is fear, not skill. Nobody's first soldering job belongs inside a $1,300 HF rig, so the iron stays in the drawer.\n\nWhen the worst case is ordering another one, people try things. People who try things build things."],
    ];
    const cw = (W - 2 * M - 0.6) / 3;
    cols.forEach(([ic, t, d], i) => {
      const x = M + i * (cw + 0.3);
      card(s, x, 2.0, cw, 4.1);
      iconCircle(s, ic, x + 0.3, 2.3, 0.7);
      h3(s, t, x + 0.3, 3.15, cw - 0.6);
      body(s, d, x + 0.3, 3.65, cw - 0.6, 2.3, { size: 14 });
    });
  }

  // ---------- 4. Why the Quansheng ----------
  {
    const s = base("The stock radio will not send CW at all. What makes it interesting is the open-source lineage: DualTachyon reverse engineered the original K5 and released the first open firmware, egzumer built the feature-rich custom firmware everyone knows, F4HWN and muzkr ported it to the newer K5 v3 and K1 hardware as Fusion, and NR7Y layered a real CW transceiver on top of that. All Apache 2.0. NR7Y is also a BKG member, which is a nice line to drop here.");
    title(s, "Why the Quansheng?", { sub: "Out of the box it will not send CW at all. What it has is a price tag and an open-source firmware family." });
    card(s, M, 2.0, 5.6, 4.75);
    iconCircle(s, I.money, M + 0.3, 2.3, 0.7);
    h3(s, "Cheap enough to open", M + 0.3, 3.15, 5.0);
    bullets(s, [
      "About $30 delivered. Less than the club spends on coffee.",
      "Sold everywhere, so a club build night could order five identical radios.",
      "Very easy to open: two screws and a pry at one edge.",
      "The MCU is fully documented by the community, so firmware authors can drive the hardware directly.",
      "If someone destroys one, the club is out $30 and up one member who has seen the inside of a radio.",
    ], M + 0.3, 3.65, 5.0, 3.0, { size: 14 });
    // lineage
    const lx = 6.9, lw = W - M - lx;
    h3(s, "The firmware lineage", lx, 2.0, lw);
    const steps = [
      ["DualTachyon", "First open-source firmware for the original UV-K5. Paved the way."],
      ["egzumer", "The feature-rich custom firmware for the v1 radios."],
      ["F4HWN \"Fusion\" (armel + muzkr)", "Port to the UV-K5 v3 and UV-K1 with the newer PY32F071 MCU."],
      ["NR7Y CW mod", "Real CW keying, iambic keyer, messages and practice mode layered on Fusion. Apache 2.0."],
    ];
    steps.forEach(([t, d], i) => {
      const y = 2.55 + i * 1.08;
      if (i < steps.length - 1) s.addShape(pres.ShapeType.line, { x: lx + 0.25, y: y + 0.5, w: 0, h: 0.6, line: { color: C.brass, width: 2 } });
      numCircle(s, i + 1, lx, y);
      body(s, t, lx + 0.7, y - 0.03, lw - 0.7, 0.4, { size: 16, bold: true });
      body(s, d, lx + 0.7, y + 0.33, lw - 0.7, 0.7, { size: 13, color: C.muted });
    });
  }

  // ---------- 5. Which radio ----------
  {
    const s = base("This is the slide that saves people money. There are three hardware families and two firmware families. The v3 and K1 share firmware. Buy the K1: it is one known target, and the older K5 shipped in several revisions that are hard to tell apart before you buy. Mention the mystery v2: label says V3, board says V1.8, different MCU, runs nothing we have. Check the label behind the battery.");
    title(s, "Which radio? Buy the K1.", { sub: "Three hardware families, two firmware families. Loading the wrong one means a reflash at best." });
    const cols = [
      ["UV-K5 v1 (original)", ["Also sold as K5, K5(8), K5(99), K6.", "All the colored and clear cases are v1.", "Board marked V1.x, DP32G030 MCU.", "Needs the separate v1 CW firmware."], C.card],
      ["UV-K5 v3", ["Looks identical to the v1 from outside.", "Label behind the battery says V3.", "Board marked V2.x, PY32F071 MCU.", "Same firmware as the K1."], C.card],
      ["UV-K1  (recommended)", ["One known target. Order five, get five identical radios.", "With or without the chin, same internals.", "PY32F071 MCU, same firmware as v3.", "Cleanest rework of the three."], C.card2],
    ];
    const cw = (W - 2 * M - 0.6) / 3;
    cols.forEach(([t, items, fill], i) => {
      const x = M + i * (cw + 0.3);
      card(s, x, 2.0, cw, 3.2, fill);
      h3(s, t, x + 0.3, 2.2, cw - 0.6, { size: 19, color: i === 2 ? C.brassLt : C.brass });
      bullets(s, items, x + 0.3, 2.75, cw - 0.6, 2.7, { size: 14 });
    });
    card(s, M, 5.5, W - 2 * M, 1.05, C.card2);
    iconCircle(s, I.warn, M + 0.25, 5.72, 0.6);
    body(s, "The mystery \"v2\": label says V3, board is silkscreened V1.8, and the MCU is different. It runs neither firmware. Rare, but it exists. Pull the battery and read the label before you order a cable.", M + 1.05, 5.65, W - 2 * M - 1.3, 0.8, { size: 14, valign: "middle" });
  }

  // ---------- 6. What the firmware gives you ----------
  {
    const s = base("Emphasize the first one: this is actual carrier keying with fast RX/TX switching, not a tone whistled into the FM microphone. Then the keyer modes, the message memories, and the practice oscillator, which needs no license because it makes no RF and will even blink the flashlight in time with your sending.");
    title(s, "What the CW firmware gives you");
    const feats = [
      [I.bolt, "True CW keying", "Carrier keyed on and off with fast RX/TX switching and full break-in. Not a tone into an FM mic."],
      [I.key, "Iambic keyer", "Modes A, B, Ultimatic and Bug. 10 to 45 WPM. Any paddle, straight key, or even PTT and the side button."],
      [I.vol, "Sidetone", "450 to 800 Hz in 50 Hz steps, volume off through 6. The tone you hear is the tone you send."],
      [I.save, "Message memories", "Four slots of 46 characters. Record by keying, then play or repeat. Map them to F1, F2 or M."],
      [I.eye, "Decoder on screen", "Decodes your sending and what it hears. About 19 characters scroll across the middle line."],
      [I.grad, "Code practice oscillator", "No RX, no TX, no license needed. Sidetone plus decode, and it can blink the flashlight LED."],
      [I.filter, "Filter width", "Cycle the IF bandwidth to narrow out a neighbor. Only active in CW mode."],
      [I.exch, "SSB cross-mode", "Shifts your CW up by the sidetone so an op on 144.200 USB hears a clean tone without retuning."],
    ];
    const cols = 4, cw = (W - 2 * M - 0.3 * (cols - 1)) / cols, ch = 2.45;
    feats.forEach(([ic, t, d], i) => {
      const x = M + (i % cols) * (cw + 0.3), y = 1.55 + Math.floor(i / cols) * (ch + 0.3);
      card(s, x, y, cw, ch);
      iconCircle(s, ic, x + 0.25, y + 0.25, 0.55);
      body(s, t, x + 0.95, y + 0.25, cw - 1.15, 0.55, { size: 15, bold: true, valign: "middle" });
      body(s, d, x + 0.25, y + 0.95, cw - 0.5, ch - 1.1, { size: 12.5, color: C.muted });
    });
  }

  // ---------- 7. Three ways to key it ----------
  {
    const s = base("You do not have to open the radio to try this. PTT and side button works on a stock radio the day you flash it. The USB-C cable is a passive custom cable, no electronics, but it is very sensitive to RF from your own transmitter and can lock into key-down. The rework is what the rest of the talk walks through: any off-the-shelf paddle plugs straight into the headset jack.");
    title(s, "Three ways to key it", { sub: "Pick by how much you want to open the radio. The rest of this talk walks through the third one." });
    const cols = [
      [I.hand, "PTT and side button", "No hardware at all", ["PTT is dah, Side 1 is dit. Iambic keyer still works.", "Also \"PTT HandKey\" for straight-key style.", "Try CW the day you flash. Clumsy for real QSOs."]],
      [I.usb, "USB-C to TRS cable", "Custom passive cable, radio stays closed", ["D+ to tip (dit), D- to ring (dah), ground to sleeve.", "No electronics. You will have to build it.", "Very sensitive to your own RF. Can lock into key-down, so keep it short, use medium power."]],
      [I.plug, "The rework", "Two resistors off, two wires on", ["Any off-the-shelf TRS paddle plugs straight into the 3.5 mm headset jack.", "Rock solid input, no special cable.", "Open the case and solder. External mic PTT and SWD debug stop working."]],
    ];
    const cw = (W - 2 * M - 0.6) / 3;
    cols.forEach(([ic, t, sub, items], i) => {
      const x = M + i * (cw + 0.3);
      card(s, x, 2.0, cw, 4.35, i === 2 ? C.card2 : C.card);
      iconCircle(s, ic, x + 0.3, 2.3, 0.7);
      h3(s, t, x + 0.3, 3.15, cw - 0.6);
      body(s, sub, x + 0.3, 3.55, cw - 0.6, 0.35, { size: 13, italic: true, color: C.muted });
      bullets(s, items, x + 0.3, 4.05, cw - 0.6, 2.2, { size: 14 });
    });
  }

  // ---------- 8. Tools and supplies ----------
  {
    const s = base("Nothing exotic. NR7Y's own note is that most standard pencil irons will remove the resistors without damaging neighbors, any tip shape works, and the two jumper wires have literally been stripped out of the USB cable that ships in the box. The plastic spudger matters: the display frame releases with a non-metallic tool. The laptop needs Chrome or Chromium because the flashing tool uses WebSerial.");
    title(s, "Tools and supplies", { sub: "Everything on this slide fits in a shoebox. Most of it is already in your junk drawer." });
    const half = (W - 2 * M - 0.3) / 2;
    card(s, M, 2.0, half, 3.3);
    iconCircle(s, I.tools, M + 0.3, 2.25, 0.6);
    h3(s, "Tools", M + 1.05, 2.35, half - 1.3);
    bullets(s, [
      "Pencil soldering iron. Conical, chisel or bevel tip all work.",
      "Solder, a little flux, fine tweezers.",
      "Thin flathead screwdriver or pry tool for the case.",
      "Plastic spudger for the display frame and ribbon latch.",
      "Magnifier, loupe, or just your phone camera zoomed in.",
      "Isopropyl alcohol and a swab for the pads and the display.",
    ], M + 0.3, 2.95, half - 0.6, 2.7, { size: 14, gap: 4 });
    card(s, M + half + 0.3, 2.0, half, 3.3);
    iconCircle(s, I.micro, M + half + 0.6, 2.25, 0.6);
    h3(s, "Parts", M + half + 1.35, 2.35, half - 1.3);
    bullets(s, [
      "Quansheng UV-K1 (see previous slide).",
      "Two wires, about 2 in and 3 in, 22 AWG or thinner. Strip them out of the USB cable in the box.",
      "A paddle or straight key with a 3.5 mm TRS plug.",
      "K5-style two-pin (Kenwood) programming cable.",
      "Laptop with Chrome or Chromium for the WebSerial flasher.",
      "The firmware file and CHIRP module from the Releases page.",
    ], M + half + 0.6, 2.95, half - 0.9, 2.7, { size: 14, gap: 4 });
    const costs = [["~$30", "radio"], ["~$10", "programming cable"], ["$0", "jumper wire"], ["~$40", "iron, if you need one"]];
    costs.forEach(([n, l], i) => {
      const cw = (W - 2 * M - 0.9) / 4, x = M + i * (cw + 0.3);
      card(s, x, 5.6, cw, 0.95, C.card2);
      s.addText(n, { x: x + 0.2, y: 5.6, w: 1.4, h: 0.95, fontFace: HEAD, fontSize: 24, bold: true, color: C.brass, isTextBox: true, margin: 0, valign: "middle" });
      body(s, l, x + 1.65, 5.6, cw - 1.8, 0.95, { size: 13, color: C.muted, valign: "middle" });
    });
  }

  // ---------- 9. The circuit ----------
  {
    const s = base("This is the whole trick. The firmware, when in CW mode, holds the serial TX line low so the sleeve of the headset jack becomes ground. Then it reads the PTT line as dit and PB11, the SWDIO programming pad, as dah. The two resistors that come off are the pull-up on the PTT line and the resistor in the mic ground path. Designators here are from the original K5 schematic; the K1 moved the parts but the circuit is the same. Side effects: an external mic can no longer trigger PTT, the headset port loses its 5 volts, SWD debugging is gone, and you unplug the paddle for FM so the internal mic comes back.");
    title(s, "What the mod actually does", { sub: "Four changes. The firmware does the rest." });
    s.addImage({ path: path.join(IMG, "rework_schematic.png"), x: M, y: 1.9, w: 6.4, h: 4.61 });
    foot(s, "Rework schematic from the NR7Y CW Firmware Docs (CC BY-NC-SA 4.0). Original schematic reverse-engineered by mentalDetector.");
    const rx = 7.4, rw = W - M - rx;
    const steps = [
      ["Remove R72", "the 1k pull-up on the PTT line"],
      ["Remove R70", "the 10 ohm resistor in the mic ground path"],
      ["Wire PB11 to jack pin 3", "the SWDIO pad becomes the ring: dah"],
      ["Wire PTT to jack pin 2", "the PTT line becomes the tip: dit"],
    ];
    steps.forEach(([t, d], i) => {
      const y = 1.9 + i * 0.78;
      numCircle(s, i + 1, rx, y + 0.05, 0.45);
      body(s, t, rx + 0.65, y, rw - 0.65, 0.35, { size: 16, bold: true });
      body(s, d, rx + 0.65, y + 0.33, rw - 0.65, 0.35, { size: 13, color: C.muted });
    });
    card(s, rx, 5.1, rw, 1.75, C.card2);
    body(s, "In CW mode the firmware pulls serial TX low so the sleeve acts as ground, then reads PTT as dit and PB11 as dah.\n\nDesignators are from the K5 v1 schematic. The K1 moved the parts; the circuit is identical. Costs: external mic PTT, +5 V on the headset port, and SWD debug. Unplug the paddle for FM.", rx + 0.25, 5.2, rw - 0.5, 1.6, { size: 12.5 });
  }

  // ---------- 10. Opening the K1 ----------
  {
    const s = base("Walk this slowly. The two mistakes people make are prying at the wrong edge and torquing the flex circuit between the board and the front half. Slide the inner metal down only until the volume stem clears, then deal with the ribbon: lift the socket door on the side opposite where the ribbon enters, and it slides out. The display frame releases at the lower-left corner with a plastic tool.");
    title(s, "Opening the K1", { sub: "Two screws, one pry, one ribbon, one display latch. No ring nuts, no front screws." });
    const steps = [
      ["Strip it", "Battery, volume knob and antenna off. Leave the ring nuts alone."],
      ["Two screws only", "The two behind the battery at the lower edge. The front screws and the ones by the battery release do not matter."],
      ["Pry the lower edge", "Between the plastic chassis and the inner metal back. Front of the radio facing down so the keypad stays put."],
      ["Slide, then stop", "The inner metal releases and slides down. Only until the volume stem clears the chassis. Do not pull it away yet."],
      ["Respect the flex circuit", "A thin ribbon links the board to the front half. Do not over-flex or twist it."],
      ["Unlatch the ribbon", "Pry the socket door on the side opposite the ribbon entry. It pivots up and the ribbon slides out. Halves are now separate."],
      ["Free the display", "Press in at the lower-left corner of the display frame with a plastic spudger, wiggle, and hinge it up over the top edge."],
    ];
    const cw = (W - 2 * M - 0.3) / 2;
    steps.forEach(([t, d], i) => {
      const col = i < 4 ? 0 : 1, row = i < 4 ? i : i - 4;
      const x = M + col * (cw + 0.3), y = 2.0 + row * 1.18;
      numCircle(s, i + 1, x, y + 0.03, 0.45);
      body(s, t, x + 0.65, y, cw - 0.65, 0.35, { size: 16, bold: true });
      body(s, d, x + 0.65, y + 0.35, cw - 0.65, 0.8, { size: 13, color: C.muted });
    });
    card(s, M + cw + 0.3, 5.55, cw, 1.3, C.card2);
    iconCircle(s, I.warn, M + cw + 0.55, 5.9, 0.6);
    body(s, "The ribbon is the fragile part. One of ours yanked it clean out of the board and now owns a radio that only blinks. Door first, then ribbon.", M + cw + 1.35, 5.7, cw - 1.6, 1.0, { size: 13, valign: "middle" });
  }

  // ---------- 11. Remove the resistors ----------
  {
    const s = base("Two tiny surface-mount resistors next to the headset jack, circled in the photo. Put a dab of solder on the tip to transfer heat, then heat one end and the other in turn until the part slides off, or lay a wide tip across both ends at once. Lift with tweezers; never pull. The failure mode is lifting the copper pad with the resistor, and one of our members did exactly that: went in for two resistors, came out with zero pads. NR7Y's line: the rework is technically reversible, except the resistors vanish the moment they leave the board.");
    title(s, "Step one: two resistors off", { sub: "The only step that needs a steady hand. Two tiny parts, one careful minute." });
    s.addImage({ path: path.join(IMG, "k1_resistors.jpg"), x: M, y: 1.9, w: 3.63, h: 4.8 });
    foot(s, "Photo: NR7Y CW Firmware Docs, UV-K1 rework page (CC BY-NC-SA 4.0). The full-resolution version is on the docs site.");
    const rx = 4.6, rw = W - M - rx;
    const steps = [
      ["Find them", "Two 0402-size resistors on the pads right beside the headset jack, circled in yellow. Confirm with the full-res photo on the docs page before heating anything."],
      ["Heat, do not pull", "Dab of solder on the tip. Heat one end, then the other, until the part slides. Or a wide tip across both ends at once. Lift with tweezers."],
      ["Check the pads", "Both pads still there, no bridges, no stray solder balls. Clean with alcohol. That is the whole step."],
    ];
    steps.forEach(([t, d], i) => {
      const y = 1.9 + i * 1.2;
      numCircle(s, i + 1, rx, y + 0.03, 0.45);
      body(s, t, rx + 0.65, y, rw - 0.65, 0.35, { size: 17, bold: true });
      body(s, d, rx + 0.65, y + 0.37, rw - 0.65, 0.8, { size: 13.5, color: C.muted });
    });
    card(s, rx, 5.55, rw, 1.15, C.card2);
    iconCircle(s, I.skull, rx + 0.25, 5.82, 0.6);
    body(s, "\"Technically reversible, although the two resistors will vanish the moment you desolder them.\" And if you lift a pad, the radio is a keychain. Low heat, patience, tweezers.", rx + 1.05, 5.65, rw - 1.3, 0.95, { size: 13, valign: "middle" });
  }

  // ---------- 12. Add the wires ----------
  {
    const s = base("Two wires, roughly two and three inches. Follow the photo: the blue wire runs from the solder blob on the left edge over to the pad near the resistor site by the jack, and the yellow wire runs from the headset jack pad down to gold pad number three of the four on the bottom edge, which is the SWDIO pad. Route the long one to the side of the button pads so it never sits under a key, and keep both flat so the display drops back over them. Stranded wire works but watch for stray strands at each end.");
    title(s, "Step two: two wires on", { sub: "About 2 in and 3 in of anything 22 AWG or thinner. Tin the ends first." });
    s.addImage({ path: path.join(IMG, "k1_wires.jpg"), x: M, y: 1.9, w: 3.16, h: 4.8 });
    foot(s, "Photo: NR7Y CW Firmware Docs, UV-K1 rework page (CC BY-NC-SA 4.0). Wire colors are the author's; use whatever you have.");
    const rx = 4.15, rw = W - M - rx;
    const steps = [
      ["Short wire (blue, ~2 in)", "From the solder blob on the left edge of the board over to the pad beside the resistor site next to the headset jack. This carries the PTT line to the jack tip: dit."],
      ["Long wire (yellow, ~3 in)", "From the headset-jack pad down to gold pad 3 of the four along the bottom edge. That pad is SWDIO, which becomes the jack ring: dah."],
      ["Route and flatten", "Run the long wire beside the button pads, never under a key. Keep both flat so the display frame seats over them. Snip strays; stranded wire loves to short."],
      ["Match the photo", "Before closing up, compare against the full-res photo on the docs page. Pad-for-pad. Then a quick continuity check from the jack to each pad."],
    ];
    steps.forEach(([t, d], i) => {
      const y = 1.9 + i * 1.22;
      numCircle(s, i + 1, rx, y + 0.03, 0.45);
      body(s, t, rx + 0.65, y, rw - 0.65, 0.35, { size: 16, bold: true });
      body(s, d, rx + 0.65, y + 0.37, rw - 0.65, 0.85, { size: 13, color: C.muted });
    });
  }

  // ---------- 13. Button it up ----------
  {
    const s = base("Reassembly in reverse, with two things worth saying out loud: clean the display glass now, because it goes behind the chassis window and you will never reach it again; and the ribbon goes into the socket with the door up, then the door latches down. Then the first power-on: it should boot normally on stock firmware. If it does, you did not break anything, and now we flash.");
    title(s, "Button it up", { sub: "Reverse order, with two things you cannot fix later." });
    const half = (W - 2 * M - 0.3) / 2;
    card(s, M, 2.0, half, 4.85);
    h3(s, "Reassembly", M + 0.3, 2.2, half - 0.6);
    const steps = [
      "Display back in: top-right latch first, then drop the lower-left corner into its hole. Press inward like you did to release it, not straight down on the glass.",
      "Clean the display now. Fingerprints and dust get sealed behind the chassis window.",
      "Socket door up, slide the ribbon's gold fingers in, hinge the door down to latch.",
      "Slide the top half of the board and metal back into the chassis, press the bottom in.",
      "Two screws. Knob, antenna, battery.",
    ];
    steps.forEach((t, i) => {
      const y = 2.7 + i * 0.78;
      numCircle(s, i + 1, M + 0.3, y + 0.02, 0.4);
      body(s, t, M + 0.9, y, half - 1.2, 0.75, { size: 13 });
    });
    card(s, M + half + 0.3, 2.0, half, 4.85, C.card2);
    iconCircle(s, I.check, M + half + 0.6, 2.2, 0.6);
    h3(s, "First power-on", M + half + 1.35, 2.3, half - 1.6);
    bullets(s, [
      "Power on with the stock firmware still loaded. It should boot and behave exactly as before.",
      "Internal mic and speaker still work with nothing plugged into the headset jack.",
      "Plug a paddle in. Nothing should happen yet. The firmware does not know about it.",
      "Boots normally? Then nothing is bridged and no ribbon is torn. Now we flash.",
      "Blank screen, no boot, or a flashing screen: open it back up and check the ribbon seat and the pads before anything else.",
    ], M + half + 0.6, 2.95, half - 0.9, 3.7, { size: 13.5, gap: 6 });
  }

  // ---------- 14. Flash it ----------
  {
    const s = base("Three musts from the docs: right firmware family for the radio, right tool for the radio, and back up the calibration data immediately after. Bootloader mode is power on while holding PTT: the flashlight LED lights and the screen stays dark. uvtools2 runs in the browser over WebSerial, so it has to be Chrome or Chromium. The LED flashes while it writes. Then dump the calibration with the same tool and name the file after the serial number. Grab the CHIRP module from the same release, CHIRP needs it.");
    title(s, "Flash it", { sub: "Right firmware, right tool, then back up the calibration before you do anything else." });
    const steps = [
      [I.eye, "Identify", "Label behind the battery. K1 or V3 use the k1-k5v3 firmware. Never the v1 file."],
      [I.flash, "Download", "Releases page: the .bin for the K1/K5v3 and the matching CHIRP module. No compiling."],
      [I.bolt, "Bootloader", "Hold PTT and power on. Flashlight LED on, screen blank and unlit. Plug in the programming cable."],
      [I.usb, "uvtools2", "Open it in Chrome or Chromium, connect the serial port, pick the file, flash. The LED blinks while it writes."],
      [I.save, "Back up", "Reboot to the new firmware, then dump the calibration data with uvtools2. Name the file after the serial number."],
    ];
    const n = steps.length, gap = 0.25, cw = (W - 2 * M - gap * (n - 1)) / n;
    steps.forEach(([ic, t, d], i) => {
      const x = M + i * (cw + gap), y = 2.0;
      card(s, x, y, cw, 3.4);
      iconCircle(s, ic, x + cw / 2 - 0.35, y + 0.3, 0.7);
      numCircle(s, i + 1, x + 0.2, y + 0.2, 0.36);
      body(s, t, x + 0.2, y + 1.15, cw - 0.4, 0.4, { size: 17, bold: true, align: "center" });
      body(s, d, x + 0.2, y + 1.65, cw - 0.4, 1.7, { size: 12.5, color: C.muted, align: "center" });
    });
    card(s, M, 5.7, W - 2 * M, 1.15, C.card2);
    iconCircle(s, I.warn, M + 0.25, 5.97, 0.6);
    body(s, "Wrong firmware family, or the wrong tool mode, is the most common way to end up with a dead radio, and a few bad flashes have needed aggressive recovery. Calibration is what makes the radio transmit on frequency at the right power; the tools try hard not to touch it, but a backup is the safety net.", M + 1.05, 5.78, W - 2 * M - 1.3, 1.0, { size: 13, valign: "middle" });
  }

  // ---------- 15. Set it up ----------
  {
    const s = base("Long press zero to cycle modulation until it says CW; squelch opens full time in CW, side button one closes it. The CW menu items are at the very end of the menu, so scroll up from the top. Key input to Port Iambic for a paddle, Port HandKey for a straight key; if dit and dah are swapped, pick Reversed instead of re-soldering. If you see CW KEY STUCK it means a paddle contact is shorted, the rework is not right, or the programming cable was still plugged in when it rebooted. And CHIRP will not connect while the radio is in CW with a port input, so switch modes to program memories.");
    title(s, "Set it up", { sub: "The CW entries are the last ones in the menu. Scroll up from the top and you land on them." });
    const half = (W - 2 * M - 0.3) / 2;
    const rows = [
      ["Long press 0", "Cycle modulation FM > AM > USB > CW. Squelch opens in CW; Side 1 closes it."],
      ["CWkin", "Port Iambic for a paddle. Port HandKey for a straight key. Reversed if dit and dah are swapped."],
      ["CWkmod", "Mode B is the default. A, Ultimatic and Bug are there if you have opinions."],
      ["CWwpm / CWfreq / CWvol", "18 WPM, 600 Hz, level 4 by default. Start slower than you think."],
      ["CWbkin", "ON. Sending keys the transmitter. OFF gives you sidetone only, which is how you practice."],
      ["CWmsg1", "Record new, key CQ CQ DE CALL, press M to save. Play or Repeat, or map it to F1."],
    ];
    rows.forEach(([k, v], i) => {
      const y = 2.0 + i * 0.8;
      s.addText(k, { x: M, y, w: 2.5, h: 0.7, fontFace: "Courier New", fontSize: 14, bold: true, color: C.brass, isTextBox: true, margin: 0, valign: "top" });
      body(s, v, M + 2.55, y, half - 2.55, 0.75, { size: 13 });
    });
    const rx = M + half + 0.3;
    card(s, rx, 2.0, half, 2.45, C.card2);
    iconCircle(s, I.warn, rx + 0.25, 2.25, 0.6);
    h3(s, "\"CW KEY STUCK\"", rx + 1.0, 2.35, half - 1.3, { size: 18 });
    bullets(s, [
      "A paddle contact is shorted, the rework is not quite right, or the programming cable was still in at reboot.",
      "Power off, fix the cause, power on. The firmware re-checks the port at every boot.",
      "Trying a Port mode without the rework gives the same message. That is the firmware protecting you.",
    ], rx + 0.3, 3.0, half - 0.6, 1.4, { size: 12.5, gap: 3 });
    card(s, rx, 4.7, half, 2.15);
    h3(s, "Shortcuts worth knowing", rx + 0.3, 4.85, half - 0.6, { size: 18 });
    bullets(s, [
      "F, then long press 5: code practice oscillator. No RF, blinks the flashlight if you want.",
      "Long press 7: toggle break-in. F, then long press 4: filter width.",
      "CHIRP will not connect while in CW with a Port input. Switch to FM to program memories.",
    ], rx + 0.3, 5.3, half - 0.6, 1.5, { size: 12.5, gap: 3 });
  }

  // ---------- 16. On the air ----------
  {
    const s = base("The grown-up paragraph. The gang calls on 144.025, at the CW and weak-signal end of two meters. That end is shared with EME, so the courtesies matter: listen first, send QRL, and move if somebody is working. Operate inside your privileges and your band plan. Then the honest version: this is a modified cheap radio, not a weak-signal station, and it behaves like one. That is the point. QRS is a feature, not an apology.");
    title(s, "On the air", { sub: "144.025 MHz, slow enough for the newest operator in the room." });
    card(s, M, 2.0, 4.3, 4.85, C.card2);
    s.addText("144.025", { x: M + 0.2, y: 2.3, w: 3.9, h: 1.1, fontFace: HEAD, fontSize: 44, bold: true, color: C.brass, isTextBox: true, margin: 0, align: "center", valign: "middle" });
    body(s, "MHz  ·  CW", M + 0.2, 3.35, 3.9, 0.4, { size: 16, color: C.muted, align: "center" });
    body(s, "The calling frequency, at the CW and weak-signal end of 2 meters. Shared with EME, so the courtesies are not optional.\n\nOutside the US, check your national band plan.", M + 0.35, 4.0, 3.6, 2.7, { size: 13.5 });
    const rx = M + 4.6, rw = W - M - rx;
    const items = [
      ["Listen first, then QRL?", "Bylaw III, and this is exactly what it was written for. Somebody working? Move."],
      ["Inside your privileges", "Your license, your band plan, your responsibility. We are a law-abiding, FCC-respecting gang."],
      ["Medium power, modest antenna", "It is a local mode. A whip works across town; a small beam works across the valley."],
      ["QRS is a feature", "5 WPM counts as much as 25. Put the club on the frequency and run it at the slowest operator's speed."],
      ["The honest version", "A modified cheap radio, not a weak-signal station, and it behaves like one. That is the point."],
    ];
    items.forEach(([t, d], i) => {
      const y = 2.0 + i * 0.97;
      numCircle(s, i + 1, rx, y + 0.03, 0.45);
      body(s, t, rx + 0.65, y, rw - 0.65, 0.35, { size: 16, bold: true });
      body(s, d, rx + 0.65, y + 0.36, rw - 0.65, 0.6, { size: 13, color: C.muted });
    });
  }

  // ---------- 17. Safety board ----------
  {
    const s = base("Lighten it up before the closer. The gang keeps a 'days since we broke a Quansheng' sign on the website with an incident log, names named. Three so far, and incident number one is you, so own it: that is the whole point of the board. Each one maps to a step you just saw: pry at the right edge, heat instead of pull, and door before ribbon. If you break one, you confess on Discord and an officer resets the sign.");
    title(s, "Days since we broke a Quansheng", { sub: "The gang keeps a safety board. Names are named. Every incident is a slide you just saw." });
    const inc = [
      ["#001", "22 Aug 2026", "N9HO", "Tore the screen clean off one on the floor of the Huntsville Hamfest. At the ARRL National Convention. In front of everybody.", "Pry at the lower edge, front face down, and stop when the volume stem clears."],
      ["#002", "1 Sep 2026", "K3JRZ", "Went in for two resistors, came out with zero pads. Murdered the whole neighborhood. The radio is now a keychain.", "Heat, do not pull. Dab of solder on the tip, lift with tweezers."],
      ["#003", "11 Sep 2026", "AA1N", "Ripped the display ribbon cable clean out of the board. Now enjoying the flashing screen of death.", "Socket door up first. Then, and only then, the ribbon slides out."],
    ];
    const cw = (W - 2 * M - 0.6) / 3;
    inc.forEach(([n, d, who, what, lesson], i) => {
      const x = M + i * (cw + 0.3);
      card(s, x, 2.0, cw, 4.85);
      s.addText(n, { x: x + 0.3, y: 2.2, w: 1.2, h: 0.5, fontFace: HEAD, fontSize: 24, bold: true, color: C.brass, isTextBox: true, margin: 0, valign: "middle" });
      body(s, d + "  ·  " + who, x + 1.5, 2.2, cw - 1.8, 0.5, { size: 13, color: C.muted, valign: "middle" });
      body(s, what, x + 0.3, 2.9, cw - 0.6, 1.9, { size: 14 });
      s.addShape(pres.ShapeType.roundRect, { x: x + 0.3, y: 4.95, w: cw - 0.6, h: 1.65, fill: { color: C.card2 }, line: { color: C.card2 }, rectRadius: 0.1 });
      body(s, "Lesson", x + 0.5, 5.05, cw - 1.0, 0.3, { size: 11, bold: true, color: C.brass });
      body(s, lesson, x + 0.5, 5.4, cw - 1.0, 1.15, { size: 13 });
    });
    foot(s, "Live sign and incident log: bkg.club/safety.html. Broke one? Confess on Discord and an officer resets the sign.");
  }

  // ---------- 18. BKG ----------
  {
    const s = base("Closer, two minutes. The Brass Knuckle Gang: pounding brass means sending Morse on a manual key. Founded 2025 in Northern Utah. As of today's site build there are 458 members across 42 states and 7 other countries, and the firmware author NR7Y is on the roster himself. A law-abiding, FCC-respecting gang, and we mean the second part as sincerely as the first. Three bylaws. To join you work an existing member on 2 meter CW, give them the UTC date and time, and you get a number. Membership is voluntary every time; confirm someone wants in before you submit them.");
    title(s, "The Brass Knuckle Gang", { sub: "A law-abiding, FCC-respecting gang for amateur radio operators. 2 meter CW or bust." });
    s.addImage({ path: path.join(IMG, "bkg-logo.jpg"), x: M, y: 2.0, w: 3.6, h: 3.6 });
    const facts = [["Founded", "2025, Northern Utah"], ["Territory", "144 MHz, worldwide"], ["Members", "458 and recruiting"], ["Reach", "42 states, 7 DX countries"], ["Mode", "CW only. Manual keys."]];
    facts.forEach(([k, v], i) => {
      body(s, k, M, 5.72 + i * 0.27, 1.2, 0.27, { size: 11, bold: true, color: C.brass });
      body(s, v, M + 1.2, 5.72 + i * 0.27, 2.6, 0.27, { size: 11, color: C.muted });
    });
    const rx = M + 4.0, half = (W - M - rx - 0.3) / 2;
    card(s, rx, 2.0, half, 4.85);
    iconCircle(s, I.fist, rx + 0.3, 2.25, 0.6);
    h3(s, "The three bylaws", rx + 1.05, 2.35, half - 1.3);
    const laws = [
      ["I. Never talk about BKG", "Except you should, all the time, to everyone. 2m CW needs more operators."],
      ["II. The proper Roger", "At least one thoughtful, proper R per QSO. Failure may result in excommunication."],
      ["III. The QRL? formality", "Always send QRL? before taking a frequency. It is a formality on 2m CW. We do it anyway."],
    ];
    laws.forEach(([t, d], i) => {
      const y = 3.05 + i * 1.2;
      body(s, t, rx + 0.3, y, half - 0.6, 0.35, { size: 15, bold: true });
      body(s, d, rx + 0.3, y + 0.35, half - 0.6, 0.85, { size: 13, color: C.muted });
    });
    const rx2 = rx + half + 0.3;
    card(s, rx2, 2.0, half, 4.85, C.card2);
    iconCircle(s, I.users, rx2 + 0.3, 2.25, 0.6);
    h3(s, "How to get a number", rx2 + 1.05, 2.35, half - 1.3, { size: 19 });
    const join = [
      ["Make the contact", "A 2m CW QSO with any member. Watch for us on POTA and SOTA."],
      ["Send the QSO", "UTC date, time and band to the member you worked. They submit it on bkg.club."],
      ["Get your number", "An officer assigns it. You land on the roster, the map, and your sponsor's downline."],
    ];
    join.forEach(([t, d], i) => {
      const y = 3.05 + i * 1.12;
      numCircle(s, i + 1, rx2 + 0.3, y + 0.02, 0.4);
      body(s, t, rx2 + 0.85, y, half - 1.15, 0.35, { size: 15, bold: true });
      body(s, d, rx2 + 0.85, y + 0.35, half - 1.15, 0.7, { size: 12.5, color: C.muted });
    });
    body(s, "Membership is voluntary, every time. Confirm they want in before you submit them.", rx2 + 0.3, 6.38, half - 0.6, 0.45, { size: 11.5, italic: true, color: C.brassLt });
  }

  // ---------- 19. Links ----------
  {
    const s = base("Leave this up during questions. The docs site has the full-resolution rework photos and the menu reference; the releases page has the firmware and the CHIRP module; uvtools2 is the flasher. bkg.club/clubs.html is the version of this talk you can read out loud at a board meeting.");
    title(s, "Links, credits, 73", { sub: "Leave this slide up. Everything tonight came from these." });
    const half = (W - 2 * M - 0.3) / 2;
    card(s, M, 2.0, half, 4.85);
    iconCircle(s, I.link, M + 0.3, 2.25, 0.6);
    h3(s, "The radio", M + 1.05, 2.35, half - 1.3);
    const l1 = [
      ["NR7Y CW firmware docs", "briand.github.io/cw-firmware-docs"],
      ["Firmware + CHIRP module (Releases)", "github.com/briand/uv-k1-k5v3-firmware-custom"],
      ["uvtools2 flasher and calibration backup", "armel.github.io/uvtools2"],
      ["F4HWN Fusion (upstream)", "github.com/armel/uv-k1-k5v3-firmware-custom"],
    ];
    l1.forEach(([t, u], i) => {
      const y = 3.0 + i * 0.85;
      body(s, t, M + 0.3, y, half - 0.6, 0.35, { size: 14, bold: true });
      s.addText(u, { x: M + 0.3, y: y + 0.35, w: half - 0.6, h: 0.35, fontFace: "Courier New", fontSize: 12, color: C.brass, isTextBox: true, margin: 0, valign: "top" });
    });
    const rx = M + half + 0.3;
    card(s, rx, 2.0, half, 4.85, C.card2);
    iconCircle(s, I.fist, rx + 0.3, 2.25, 0.6);
    h3(s, "The gang", rx + 1.05, 2.35, half - 1.3);
    const l2 = [
      ["Home, bylaws, roster, map", "bkg.club"],
      ["The pitch for clubs, spelled correctly", "bkg.club/clubs.html"],
      ["Recruit form, downline tree, nearby finder", "bkg.club/recruit.html  ·  /tree.html  ·  /nearby.html"],
      ["Ragchew with the gang", "discord.gg/wDs5dth22k"],
      ["BKG intro video (YouTube short)", "youtube.com/shorts/2ZWex-8fG6M"],
    ];
    l2.forEach(([t, u], i) => {
      const y = 3.0 + i * 0.74;
      body(s, t, rx + 0.3, y, half - 0.6, 0.35, { size: 14, bold: true });
      s.addText(u, { x: rx + 0.3, y: y + 0.35, w: half - 0.6, h: 0.35, fontFace: "Courier New", fontSize: 12, color: C.brass, isTextBox: true, margin: 0, valign: "top" });
    });
    foot(s, "Photos and schematic: NR7Y CW Firmware Docs, CC BY-NC-SA 4.0. Firmware: NR7Y, on F4HWN Fusion, egzumer and DualTachyon (Apache 2.0). Original K5 schematic by mentalDetector.");
  }

  await pres.writeFile({ fileName: path.join(__dirname, "quansheng-2m-cw.pptx") });
  console.log("written");
})().catch(e => { console.error(e); process.exit(1); });
