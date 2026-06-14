# Fishtagged Tag Visualizer — how it works (walkthrough)

A plain-English tour of what I built and why, so I can talk through any part of it.

---

## The big picture

The old Search-a-Tag page broke when MapBox changed its interface. I rebuilt the
front end so it:

- **renders with MapLibre GL** — the open-source map engine that reads the *same*
  Mapbox vector-tile (`.pbf`) format, but needs **no API token**, so it runs live
  on GitHub Pages with nothing to pay for or expire;
- **serves the fish as our own vector tileset** (`tiles/{z}/{x}/{y}.pbf`) instead
  of dumping a big GeoJSON into the browser — the map only pulls the tiles on
  screen, which is the ingest direction Mr. Bailey asked for;
- has **three access levels** in one page;
- loads the **real fish photos** from our existing file proxy.

Three files do the data work, then one HTML file is the whole app:

```
SmallmouthFullDataset.geojson           ← the raw core export
   │  build_data.py   (clean it)
   ▼
data/fish.geojson                        ← cleaned, slimmed
   │  build_tiles.py  (tile it)
   ▼
tiles/{z}/{x}/{y}.pbf  +  fish_index.json  +  tiles_meta.json
   │
   ▼
index.html  ← MapLibre renders the tiles; fish_index.json drives search/popups/stats
```

---

## The three levels (what each one is)

| Level | Who | What it does |
|---|---|---|
| **1 — Search a tag** | anyone | A lookup. The map shows **no** fish until you search a number; then it draws that one fish, its **tag→recapture path**, and **how far it travelled**. A "busiest spots" bar chart gives the overview instead of a heatmap. No water data. |
| **2 — Account** | open | **Heatmaps only** (no exact points). All species. The water-data menu **remaps the heatmap** — temperature, river level, turbidity, oxygen, discharge — each as its own heatmap. Searching a tag still traces its path + miles. |
| **3 — Staff** | open | **Full access:** individual fish points and **exact locations**, all species, every toggle, a CSV export, and the tile-feed status. |

Two rules baked in from the feedback:
- **Menus stay grey** (Mr. Bailey: keep them generic while testing). Colour is
  used only on the *data* — the temperature ramp, the heat, the rust journey line.
- The **recapture line + miles travelled appear on all three levels**.

---

## `index.html` — section by section

It's one file: styles, then the two screens (landing + app), then the script.

### Styles (top `<style>` block)
- A small set of CSS variables sets the palette to match **fishtagged.org**:
  white background, sage green `--green:#6f8c78` for the brand/buttons, navy text,
  and a rust `--rust:#b4622d` reserved for the data (retagged fish + journey lines).
- Fonts are Helvetica/Arial/Verdana — plain, readable, on-brand (not trendy).
- Component styles: `.brandbar`/`.hero`/`.lvl` (landing), `.bar` (top bar),
  `.pane` (the 320 px left control panel), `.seg`/`.pick`/`.rows` (the grey
  menus), `.legend` (now *inside* the panel), `.side` (the bar chart), `.card`
  (the popup), `#lightbox` (full-size photo), `.veil` (loading spinner).

### Landing (`#gate`)
- A branded header (the FISHTAGGED wordmark with a green map-pin, and About /
  River Data / Report-a-Catch links to fishtagged.org), a hero line, and the
  three level buttons. Clicking a button calls `enter('l1'|'l2'|'l3')`.

### App (`#app`)
- `#map` (the MapLibre canvas), the top `.bar`, the left `.pane` (filled in per
  level), the `.side` bar chart, and the loading `.veil`.

### Script — the important functions

- **`loadIndex()`** — fetches `fish_index.json` once into three globals:
  `META` (bounds/zoom/counts), `TAGS` (every tag with its full capture history),
  `BYNUM` (tag-number → which tag groups have it).

- **`findTag(n)`** — a typed number can belong to more than one colour tag, so it
  returns the richest match (most recaptures, then most catches).

- **`addLayers()`** — adds the map layers (re-added whenever the basemap reloads):
  - `fish` **vector source** → `tiles/{z}/{x}/{y}.pbf`, source-layer `fish`;
  - `heat` (heatmap) and `dots` (individual points);
  - `jglow`/`jline` (the rust journey line), `jdot` (the catch points along it),
    `halo`/`hit` (the ring on the searched fish).

- **`tileFilter()` / `applyFilter()`** — apply the species + recaptured filters to
  the tile layers.

- **`setView(v)`** — shows heat vs points. Level 1 never shows the population;
  Level 2 is heat-only; Level 3 toggles. It also forces the L3 heatmap back to
  plain density.

- **`setHydro(h)`** — the water-data menu. On **Level 2** it calls `paintHeat()`
  to re-weight and recolour the **heatmap** by the chosen variable. On **Level 3**
  it recolours the **points** (`colorBy(h)`).

- **`paintHeat()` / `heatColors()` / `colorBy()`** — build the MapLibre colour
  expressions from the `RAMP` table (one diverging ramp for temperature, one
  sequential ramp for the rest).

- **`legend()`** — updates the in-panel legend to match the current view/variable.

- **`filteredCaps()` / `stats()` / `bars()`** — read `TAGS` with the current
  filters to fill the summary numbers and redraw the "busiest spots" bar chart
  (recomputed live so it always matches the map). `stats()` also computes the
  **average miles moved** for recaptured fish.

- **`milesBetween()` / `pathMiles()` / `daysOut()`** — the distance maths
  (great-circle / haversine miles, and days between first and last catch).

- **`search(n, fly)`** — the heart of it. Finds the tag, rings its latest catch,
  draws the **A→B→C journey line** through its catches, fits/flies to it, writes
  the status line ("Moved 14.9 mi over 175 days"), and opens the popup. Used by
  the search box on every level **and** by clicking a point on Level 3.

- **`card(t, rc, at)`** — the popup. For a recaptured fish it leads with **miles
  moved + days out** and lists each catch with the **+miles between legs**; then
  the water rows (levels 2/3 only); then the **photo**, loaded by `loadPhoto()`.

- **`loadPhoto()` / `openShot()`** — point an `<img>` at the Fishtagged file proxy
  (`retrieve?img_id=<FileName>`); click it to open the full-size **lightbox**.

- **`panel()`** — returns the left-panel HTML for the current level (search box,
  the right controls per level, summary, legend). The grey controls are the same
  building blocks reused per level.

- **`enter(r)`** — switches into a level: sets defaults, renders the panel, makes
  the map the first time, and on Level 1 pre-draws tag 841 so the interactivity is
  obvious. The loading veil is dismissed on the map's `idle` event.

- Bottom of the script wires the landing buttons, the "Change level" / "Satellite"
  buttons, and small DOM helpers.

---

## The build scripts

### `build_data.py`
Cleans a raw core export into `data/fish.geojson`: drops the few impossible
coordinates, fixes tag-colour capitalisation, renames the long field names to
short keys, rounds coordinates. Run: `python3 build_data.py <raw.geojson>`.

### `build_tiles.py`
Turns `data/fish.geojson` into the vector tileset. I wrote the Mapbox-Vector-Tile
encoder by hand (the `varint`/`zigzag`/`feature`/`layer`/`tile` helpers) so there's
nothing to install — it runs on a plain Python. It also stitches each tag's catch
history and writes `fish_index.json` (used by search/popups/stats/chart) and
`tiles_meta.json` (bounds + zoom). Run: `python3 build_tiles.py`.

The production swap later is one line: point the `fish` source at a hosted
`mapbox://<tileset>` instead of the local `tiles/` folder.

---

## What changed from the previous version (the short list)

1. Re-rendered on **MapLibre + our own vector tiles** (no token, live on Pages).
2. **Level 1** is a tag index — no map of every fish; search shows one fish + its
   path + miles; a sorted bar chart carries the overview (no heatmap).
3. **Level 2** = heatmaps only, **all species**; the water menu remaps the heat.
4. **Level 3** = individual points + exact locations + CSV + tile feed.
5. **Recapture line + miles travelled on all three levels** (search anywhere; L3
   point-click too).
6. **Real fish photos** load from the file proxy, with a click-to-enlarge lightbox.
7. Rebranded to **fishtagged.org** (white / sage green / navy, the wordmark, nav).
8. **No login** on any level (removed for now).
9. Fixes: the "spinning line" (a CSS class collision), the stuck loader, the left
   panel widened to 320 px, and the legend moved inside the panel so it no longer
   blocks the corner.
