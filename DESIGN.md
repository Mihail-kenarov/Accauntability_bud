---
name: Accountability Bud
description: A conversational life coach that grounds daily planning in real calendar, habit, and memory data
colors:
  morning-mist: "oklch(98.2% 0.006 145)"
  pale-page: "oklch(99.1% 0.004 145)"
  weathered-page: "oklch(95.8% 0.012 145)"
  sage-rule: "oklch(89.5% 0.014 145)"
  forest-ink: "oklch(25% 0.025 150)"
  sage-dusk: "oklch(52% 0.025 150)"
  pale-whisper: "oklch(70% 0.026 150)"
  counselors-sage: "oklch(54% 0.105 150)"
  sage-blush: "oklch(93.5% 0.035 150)"
  pale-amber: "oklch(94.5% 0.035 85)"
typography:
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", system-ui, sans-serif"
    fontSize: "1.1rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "normal"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", system-ui, sans-serif"
    fontSize: "1.06rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "normal"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", system-ui, sans-serif"
    fontSize: "0.94rem"
    fontWeight: 400
    lineHeight: 1.58
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", system-ui, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "normal"
rounded:
  sm: "5px"
  md: "7px"
  base: "8px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  button-default:
    backgroundColor: "{colors.pale-page}"
    textColor: "{colors.forest-ink}"
    rounded: "{rounded.base}"
    padding: "0.5rem 0.75rem"
  button-default-hover:
    backgroundColor: "{colors.sage-blush}"
    textColor: "{colors.forest-ink}"
    rounded: "{rounded.base}"
    padding: "0.5rem 0.75rem"
  button-primary:
    backgroundColor: "{colors.counselors-sage}"
    textColor: "{colors.pale-page}"
    rounded: "{rounded.base}"
    padding: "0.7rem 1rem"
  button-sidebar:
    backgroundColor: "transparent"
    textColor: "{colors.forest-ink}"
    rounded: "{rounded.base}"
    padding: "0.62rem 0.7rem"
  button-sidebar-hover:
    backgroundColor: "{colors.pale-page}"
    textColor: "{colors.forest-ink}"
    rounded: "{rounded.base}"
    padding: "0.62rem 0.7rem"
  nav-active:
    backgroundColor: "{colors.sage-blush}"
    textColor: "{colors.forest-ink}"
    rounded: "{rounded.base}"
    padding: "0.62rem 0.7rem"
---

# Design System: Accountability Bud

## 1. Overview

**Creative North Star: "The Quiet Ledger"**

Accountability Bud is a private record of an honest life. Its visual language borrows from the ledger book and the personal planner: unhurried, factual, and organized around evidence rather than encouragement. The interface does not celebrate. It does not gamify. It shows the user what is true — their calendar, their habits, their patterns — and creates the conditions for grounded decisions. Every surface should feel like a trusted tool the user reaches for every morning without thinking twice.

The palette is a single sage-green note played quietly across an almost-white ground. There is one accent color — Counselor's Sage — and it appears only where something is interactive or confirmed. Typography is system-native, variable-weight, and sized small: this interface trusts that the user will lean in, not scroll past. Layout is column-and-rail: a conversational center flanked by live context on the right, navigation on the left. Nothing decorates. Everything informs.

This system explicitly rejects: the generic chatbot with its rounded chat bubbles and blue-on-white, the corporate analytics dashboard with its gradient-filled KPI tiles, the habit tracker that awards badges and shoots confetti, the productivity tool that requires more management than the day it is supposed to help plan. If any element draws attention to itself, it is wrong.

**Key Characteristics:**
- Light theme, sage-tinted neutrals throughout; no pure whites or pure blacks
- Single accent used at ≤10% surface coverage; rarity is the point
- System UI typeface at variable weights; no web fonts, no display face
- Flat by default; depth implied through tone and border, never shadow stacking
- Column-and-rail layout; context is always visible without navigation

## 2. Colors: The Counselor's Palette

A sage-tinted neutral field with one deliberate voice.

### Primary

- **Counselor's Sage** (`oklch(54% 0.105 150)`): The single accent. Used on active states, focus rings, the submit button fill, metric progress fills, the current-time indicator, and checkbox checks. Everything else is neutral. If Counselor's Sage appears in more than two or three distinct locations on a screen, the design has lost discipline.

### Neutral

- **Morning Mist** (`oklch(98.2% 0.006 145)`): Main app surface. The ground every other surface rests on. Slightly warmer and more sage than white.
- **Pale Page** (`oklch(99.1% 0.004 145)`): Panel and card background. Lighter than Morning Mist — a deliberate inversion that lifts panels without a shadow. Also used as the input field background.
- **Weathered Page** (`oklch(95.8% 0.012 145)`): Elevated panel. Table headers, inline code backgrounds, the panel-strong layer in the metric strip. Slightly deeper with more sage presence.
- **Sage Rule** (`oklch(89.5% 0.014 145)`): All borders and dividers. Used at full opacity for separators, mixed with transparency for calendar grid lines.
- **Forest Ink** (`oklch(25% 0.025 150)`): Primary text. Near-black with a faint sage lean. Never pure black.
- **Sage Dusk** (`oklch(52% 0.025 150)`): Secondary text — labels, metadata, sidebar copy, cal-hour markers. The standard voice for anything that supports rather than leads.
- **Pale Whisper** (`oklch(70% 0.026 150)`): Tertiary text and decorative signals — dashed empty-state borders, the dot preceding plan items. Used sparingly.
- **Sage Blush** (`oklch(93.5% 0.035 150)`): Accent-soft wash. Hover backgrounds for default buttons, active nav highlight, avatar fills, calendar event backgrounds. The accent's quiet shadow.
- **Pale Amber** (`oklch(94.5% 0.035 85)`): Warning state background only. Hue shifts to 85 (yellow-amber) while holding the same saturation character as the rest of the palette — it reads as alert without jarring.

### Named Rules

**The One Voice Rule.** Counselor's Sage marks interactivity and truth; it does not decorate. It must appear on ≤10% of any screen. If you are reaching for the accent to add visual interest, you are solving the wrong problem.

**The Sage-Tinted Neutrals Rule.** Every neutral in this system carries hue 145–150 at chroma 0.004–0.035. Pure grays are prohibited: they read clinical and detached. The sage cast makes every surface feel like part of the same living document, not a GUI skin.

## 3. Typography

**Body Font:** System UI (`-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif`)

No display typeface. No web fonts. The system font is the design choice — it signals that this tool belongs to the user's desktop rather than performing a branded experience. On modern platforms, the system font supports variable weight interpolation, which the design exploits in the 400–760 range.

**Character:** Utility-forward and quietly refined. Text is sized small (the smallest captions hit 0.66rem) and line-height is generous in reading contexts. The design trusts proximity and weight contrast to build hierarchy, not size theatrics.

### Hierarchy

- **Headline** (weight 600, 1.1rem, line-height 1.25): Section-level headings within panels. Rare — reserved for view-panel titles and major content breaks.
- **Title** (weight 600, 1.06rem, line-height 1.25): Screen-level title shown in the app-title bar. One per screen.
- **Body** (weight 400, 0.94rem, line-height 1.58): Chat message copy — the primary reading surface. Max line length: 74ch (enforced via `max-width` on message rows).
- **Label** (weight 700, 0.85rem, line-height 1.2): Section titles in the rail and context stack. Uppercase is prohibited; weight carries the hierarchy.
- **Caption** (weight 400, 0.66–0.78rem, line-height 1.1–1.2, tabular-nums where numeric): Time labels, eyebrow text, metadata chips, cal-hour markers. All numeral-bearing captions use `font-variant-numeric: tabular-nums`.

### Named Rules

**The Variable Weight Rule.** Font weights range from 400 to 760. Use 400–500 for reading, 650–760 for emphasis. Never bold an entire paragraph. Never rely on weight alone without size contrast to establish hierarchy; size and weight must both move between levels.

**The No-Display Rule.** No display typeface, no serif pairing, no web font load. The system font is the brand. Loading a custom typeface on this app would make it feel like a product launch rather than a daily tool.

## 4. Elevation

This is a flat-by-default system. Surfaces are distinguished by tone and border, not by shadow stacking. The only shadows in the system are narrow and purposeful: a 1px tinted underline beneath calendar events (`0 1px 0 color-mix(in oklch, var(--accent) 18%, transparent)`) and a 3px focus ring on interactive inputs (`0 0 0 3px color-mix(in oklch, var(--accent-soft) 55%, transparent)`). Depth is expressed through the tonal ramp: Morning Mist → Pale Page → Weathered Page, each step ~2-3% lighter, with slightly more sage character. Panels feel lifted not because of shadows but because they are a lighter tone than the surface they rest on.

### Shadow Vocabulary

- **Interaction underline** (`0 1px 0 color-mix(in oklch, var(--accent) 18%, transparent)`): Calendar event blocks only. A hair of tinted lift — enough to distinguish event from grid without breaking flatness.
- **Focus ring** (`0 0 0 3px color-mix(in oklch, var(--accent-soft) 55%, transparent)`): Text inputs and form fields on focus. Communicates keyboard state without visual noise.

### Named Rules

**The Flat-By-Default Rule.** Surfaces are flat at rest. Shadows appear only as a response to interactive state — focus or event-block distinction. If you are adding a `box-shadow` outside of these two cases, you are solving a hierarchy problem with the wrong tool.

## 5. Components

### Buttons

Components that whisper. The default button is a bordered panel tile that fades into the surface until it is needed.

- **Shape:** Gently rounded (8px); matches every other container in the system.
- **Default:** Pale Page background, Sage Rule border (1px), Forest Ink text. No fill drama at rest.
- **Default Hover:** Sage Blush background, border shifts to a mix of Counselor's Sage (45%) and Sage Rule; element lifts 1px via `translateY(-1px)`. Transition: 180ms `cubic-bezier(.22,1,.36,1)` (ease-out-quart equivalent).
- **Default Active:** `translateY(0)` — snaps back on press.
- **Primary (Submit/Send):** Counselor's Sage fill, Pale Page text, Counselor's Sage border. This is the only filled button in the system. Reserved for the single committed action in a context (send message, save plan). Never used for navigation or secondary actions.
- **Sidebar:** Transparent background, no border at rest. Hover adds Pale Page fill and Sage Rule border. Full width, left-aligned text.

### Chips / Trace Tags

Used to show grounding sources: which calendar events, memories, or habit data the agent referenced in its response.

- **Style:** Pill-shaped (9999px), Pale Page background, Sage Rule border (1px), Sage Dusk text, 0.72rem caption.
- **State:** Animate in via `chipIn` (200ms, `cubic-bezier(.22,1,.36,1)`, 3px slide from below). Static once placed — no hover state needed.
- **Purpose:** These are not actions; they are receipts. They should read as secondary context, never as interactive affordances.

### Calendar Timeline

The day-timeline is a signature component: a 24-row grid with an hours column and an event layer.

- **Container:** 8px radius, Sage Rule border (1px), mixed panel-surface background (`color-mix(in oklch, var(--panel) 76%, var(--surface))`). Full day height (~45.6rem unscaled, fluid in context panels).
- **Event Blocks:** 7px radius, Sage Blush–panel mix background (68%/32%), Counselor's Sage border at 28% (mixed with Sage Rule). Padded at 0.42rem × 0.52rem. Title in Forest Ink at 0.78rem weight 650; time in Sage Dusk at 0.66rem tabular-nums.
- **Current Time Indicator:** 1px full-width Counselor's Sage line with a 0.42rem dot at the left edge. The only element that uses the accent at 100% opacity on a structural element.
- **Hours Column:** Sage Dusk captions, right-aligned, tabular-nums. Dividers at 72% Sage Rule opacity.
- **Empty State:** Dashed border (72% Pale Whisper mix), centered Sage Dusk copy. Communicates "nothing scheduled" without drama.

### Message Rows

Chat messages are the primary reading surface. Layout and prose receive the most design attention.

- **AI message:** Avatar (1.82rem, 8px radius, Sage Blush fill, Counselor's Sage text, weight 760) + body copy at 0.94rem, 1.58 line-height, max 74ch. No bubble, no background — the text is the message.
- **User message:** Right-aligned. Pale Page background bubble, Sage Rule border (1px), 8px radius. Max 58ch. Avatar uses Weathered Page fill, Sage Dusk text.
- **Animate in:** `slideFade` — 240ms `cubic-bezier(.22,1,.36,1)`, 6px slide from below with opacity.
- **Internal elements:** `code` uses Weathered Page background at 5px radius; tables use Forest Ink at 0.82rem with Sage Rule borders and Weathered Page header cells.

### Metric Strip

Four-column grid of compact data cards. Used on the habits/overview view.

- **Shape:** 8px radius, Sage Rule border (1px), `color-mix(in oklch, var(--panel) 82%, transparent)` background.
- **Content structure:** Sage Dusk label at 0.72rem → Forest Ink value at 1rem weight 720 → thin progress bar (0.18rem height, Weathered Page track, Counselor's Sage fill).
- **The Flat Metric Rule:** These are compact signal cards, not KPI tiles. No large numbers, no gradient fills, no icons. The progress bar is 3px tall. The design is calm — it reports, it does not perform.

### Inputs / Fields

The primary input is the chat form. Secondary inputs appear in plan-entry and habit-logging surfaces.

- **Style:** Pale Page background, Sage Rule border (1px), 8px radius. Minimum height 2.8rem. Box-shadow: none at rest.
- **Focus:** Border shifts to Counselor's Sage mixed at 55% with Sage Rule; focus ring is `0 0 0 3px color-mix(in oklch, var(--accent-soft) 55%, transparent)`. The only moment Counselor's Sage appears on a structural element that is not the send button or the current-time indicator.
- **Send button (paired):** Counselor's Sage fill, Pale Page text, weight 680. Sits flush with the input in a form row. One context, one primary action.

### Navigation (Sidebar)

- **Default:** Transparent background, Forest Ink text, 8px radius, full width. No border at rest.
- **Hover:** Pale Page fill, Sage Rule border.
- **Active state (`.nav-active`):** Sage Blush fill, Sage-mixed border (42% Counselor's Sage + 58% Sage Rule), Forest Ink text, weight 650. The active indicator is background fill — never a side stripe, never an underline on its own.

## 6. Do's and Don'ts

Concrete guardrails. Every anti-reference in PRODUCT.md is enforced here by name.

### Do:

- **Do** tint every neutral toward hue 145–150. Even the lightest background (`oklch(99.1% 0.004 145)`) carries trace chroma. Pure grays (`oklch(X% 0)`) are forbidden.
- **Do** use Counselor's Sage on at most 2–3 distinct UI locations per screen: the active state, the primary action, and the current-time indicator. On most screens, it appears in fewer than 3 places.
- **Do** animate state transitions at 180–240ms with `cubic-bezier(.22,1,.36,1)` (ease-out-quart). Fast enough to feel immediate; shaped to avoid mechanical linearity.
- **Do** use `font-variant-numeric: tabular-nums` on all numeric captions: cal-hour labels, metric values, and time stamps. Numerals must not shift column width.
- **Do** keep body copy at ≤74ch and chat message containers at ≤58ch. Line length is a reading comfort decision, not a layout decision.
- **Do** express hierarchy through weight contrast (400 → 720) before resorting to size. Two levels of hierarchy can share a font size if their weights differ by ≥200 units.
- **Do** use `color-mix(in oklch, ...)` for tinted borders and overlays. This keeps color relationships stable if the accent or neutral tokens are ever updated.
- **Do** respect `prefers-reduced-motion`: wrap `slideFade` and `chipIn` keyframe animations in a `@media (prefers-reduced-motion: no-preference)` block.

### Don't:

- **Don't** make this look or feel like a generic chatbot. No rounded message bubbles with brand-blue fills. No typing indicators with pulsing dots. No bot avatar with a smiley.
- **Don't** make this look or feel like a corporate analytics dashboard. No full-width gradient KPI tiles. No big-number-plus-supporting-stats hero metrics. No dark sidebar with icon-only navigation.
- **Don't** make this look or feel like a childish habit tracker or an over-gamified streak app. No confetti. No trophy badges. No celebratory overlays. Streaks are displayed as honest numeric signals in the metric strip — nothing more.
- **Don't** use a dark color scheme. The physical scene is a student at their laptop in ordinary daylight. The palette is a light tool for a light context.
- **Don't** use loud motivational graphics, pull-quote callouts, or large decorative illustrations. This is not a landing page; it is a daily work surface.
- **Don't** use heavy gradients. The single gradient in the system is the app background (`linear-gradient(180deg, var(--surface), oklch(96.8% 0.008 145))`), and it shifts by less than 2% lightness over the full viewport height. No radial gradients. No multi-stop color gradients.
- **Don't** use `border-left` greater than 1px as a colored stripe on cards, alerts, or list items. Active states use background fill. Alert states use a background-tinted surface. Side stripes are prohibited.
- **Don't** use `background-clip: text` with a gradient. Emphasis is weight and size, not decoration.
- **Don't** use glassmorphism (`backdrop-filter: blur`) outside a deliberate, justified, singular use case. The system is flat; frosted glass is its opposite.
- **Don't** add modal dialogs as the first solution to a disclosure problem. Plan and habit data expand inline. Confirmation flows use inline affordances.
- **Don't** stack identical cards in a grid with icon + heading + text repeated. Every list and grid in this system carries distinguishable data (time, habit name, plan item) — never generic content blocks.
- **Don't** add dashboard clutter that makes the user manage the tool instead of their day. Every panel must justify its presence every session. If it does not help the user understand the day or act on it, remove it.
