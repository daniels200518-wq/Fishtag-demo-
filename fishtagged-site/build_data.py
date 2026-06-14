#!/usr/bin/env python3
"""
build_data.py — turn a raw Fishtagged core GeoJSON into the app's data file.

WHEN OLIVIA / JUSTIN SEND AN UPDATED CORE FILE:
    python3 build_data.py  /path/to/NewCoreDataset.geojson

It writes  data/fish.geojson  — cleaned, slimmed, and renamed to the short
property keys the app expects. Then commit + push and the live site updates.

What it does:
  • drops records whose coordinates fall outside the Mid-Atlantic box (data typos)
  • normalises ColorTag case (yellow -> Yellow) and the Recaptured field
  • keeps only the fields the app uses, with short keys (smaller download)
  • rounds coordinates to 5 decimals (~1 m) to shrink the file
"""
import json, sys, os

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/Downloads/SmallmouthFullDataset.geojson")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fish.geojson")

# Potomac / Mid-Atlantic sanity box — anything outside is a coordinate typo.
LNG_MIN, LNG_MAX, LAT_MIN, LAT_MAX = -79.5, -76.0, 38.0, 40.6


def num(v):
    try:
        s = str(v).strip()
        return float(s) if s != "" else None
    except (TypeError, ValueError):
        return None


def main():
    src = json.load(open(SRC))
    feats = src.get("features", [])
    out, dropped = [], 0

    for f in feats:
        c = f.get("geometry", {}).get("coordinates")
        if not c or len(c) < 2:
            dropped += 1
            continue
        lng, lat = c[0], c[1]
        if not (LNG_MIN < lng < LNG_MAX and LAT_MIN < lat < LAT_MAX):
            dropped += 1
            continue
        p = f.get("properties", {})
        recap = str(p.get("Recaptured", "")).strip()
        if recap not in ("Tagged", "Recaptured"):
            recap = "Tagged"            # stray numbers / blanks -> Tagged
        out.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lng, 5), round(lat, 5)]},
            "properties": {
                "tag":   str(p.get("NumberTag", "")).strip(),
                "color": str(p.get("ColorTag", "")).strip().title(),
                "alpha": str(p.get("Alpha", "")).strip(),
                "sp":    str(p.get("Species", "")).strip() or "Unknown",
                "rc":    recap,
                "dt":    str(p.get("TagDateTimeUTC", "")).strip(),
                "yr":    str(p.get("year", "")).strip(),
                "spot":  str(p.get("NamedSpot", "")).strip(),
                "in":    num(p.get("SizeInch")),
                "mm":    num(p.get("SizeMm")),
                "file":  str(p.get("FileName", "")).strip(),
                "note":  str(p.get("Notes", "")).strip(),
                "tF":    num(p.get("POR_WaterTemp_F")),
                "tC":    num(p.get("POR_WaterTemp_C")),
                "lvl":   num(p.get("POR_RiverLevel_ft")),
                "turb":  num(p.get("POR_Turbidity_FNU")),
                "do":    num(p.get("POR_DissolvedOxygen_MG/L")),
                "cfs":   num(p.get("POR_Discharge_CFS")),
            },
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"type": "FeatureCollection", "features": out},
              open(OUT, "w"), separators=(",", ":"))
    print(f"source : {SRC}")
    print(f"kept   : {len(out):,} captures   (dropped {dropped} bad coordinates)")
    print(f"written: {OUT}  ({round(os.path.getsize(OUT)/1024):,} KB)")


if __name__ == "__main__":
    main()
