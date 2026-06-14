#!/usr/bin/env python3
"""
Turn data/fish.geojson into a real Mapbox Vector Tileset we can serve as plain
static files (tiles/{z}/{x}/{y}.pbf, source-layer "fish").

I wrote the MVT writer by hand instead of pulling in tippecanoe/GDAL so the whole
thing runs on a stock Python and there's nothing to install before a demo. Later
this is the part that gets replaced by a Mapbox-hosted tileset; the front end
just points its source url somewhere else.

Also writes:
  fish_index.json   every tag + its capture history (search box, popups, stats, bar chart)
  tiles_meta.json   bounds / zoom range for the map source

Run:  python3 build_tiles.py
"""
import json, math, os, shutil
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "data", "fish.geojson")
TILE_DIR = os.path.join(HERE, "tiles")

EXTENT = 4096
MINZOOM, MAXZOOM = 6, 12
LAYER = "fish"

# only the fields the map actually draws with travel inside the tiles.
# everything else lives in fish_index.json and is looked up by tag on click.
TILE_FIELDS = ("tag", "color", "sp", "rc", "tF", "lvl", "turb", "do", "cfs")


# --- minimal protobuf / MVT writer ---------------------------------------

def varint(v):
    out = bytearray()
    while True:
        b = v & 0x7f
        v >>= 7
        out.append(b | 0x80 if v else b)
        if not v:
            return bytes(out)

def tag(field, wire):
    return varint((field << 3) | wire)

def zigzag(n):
    return (n << 1) ^ (n >> 31)

def value(s):                                  # MVT Value, always string_value
    b = str(s).encode("utf-8")
    return tag(1, 2) + varint(len(b)) + b

def feature(fid, tags, geom):
    out = bytearray()
    out += tag(1, 0) + varint(fid)
    packed = b"".join(varint(t) for t in tags)
    out += tag(2, 2) + varint(len(packed)) + packed
    out += tag(3, 0) + varint(1)               # POINT
    g = b"".join(varint(x) for x in geom)
    out += tag(4, 2) + varint(len(g)) + g
    return bytes(out)

def layer(feats, keys, vals):
    out = bytearray()
    out += tag(15, 0) + varint(2)              # version
    name = LAYER.encode()
    out += tag(1, 2) + varint(len(name)) + name
    for f in feats:
        out += tag(2, 2) + varint(len(f)) + f
    for k in keys:
        kb = k.encode()
        out += tag(3, 2) + varint(len(kb)) + kb
    for v in vals:
        out += tag(4, 2) + varint(len(v)) + v
    out += tag(5, 0) + varint(EXTENT)
    return bytes(out)

def tile(layer_bytes):
    return tag(3, 2) + varint(len(layer_bytes)) + layer_bytes

def build_tile(items):                         # items: [(lx, ly, props)]
    keys, kidx, vals, vidx, feats = [], {}, [], {}, []
    for fid, (lx, ly, props) in enumerate(items, 1):
        tags = []
        for k in TILE_FIELDS:
            sv = props[k]
            if k not in kidx:
                kidx[k] = len(keys); keys.append(k)
            if sv not in vidx:
                vidx[sv] = len(vals); vals.append(sv)
            tags += [kidx[k], vidx[sv]]
        geom = [9, zigzag(lx), zigzag(ly)]     # MoveTo, one point
        feats.append(feature(fid, tags, geom))
    return tile(layer(feats, keys, [value(s) for s in vals]))


def to_frac(lon, lat, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


# --- load the cleaned data and stitch capture histories ------------------

def when(s):
    for fmt in ("%m/%d/%Y %I:%M %p", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return datetime.min

def s(v):                                      # tile values are strings; keep them tidy
    return "" if v is None else str(v)

raw = json.load(open(SRC))["features"]

# group every capture of the same physical tag (colour + number)
fish = {}
for f in raw:
    p = f["properties"]
    if not p["tag"] or not p["color"]:
        continue
    p["_lng"], p["_lat"] = f["geometry"]["coordinates"]
    fish.setdefault((p["color"], p["tag"]), []).append(p)

tags = []
by_num = {}
for (color, num), caps in fish.items():
    caps.sort(key=lambda p: when(p["dt"]))
    rec = {
        "num": num, "color": color, "alpha": caps[0]["alpha"], "sp": caps[0]["sp"],
        "caps": [{
            "lng": p["_lng"], "lat": p["_lat"], "dt": p["dt"], "rc": p["rc"],
            "spot": p["spot"], "in": p["in"], "mm": p["mm"], "file": p["file"],
            "tF": p["tF"], "lvl": p["lvl"], "turb": p["turb"], "do": p["do"], "cfs": p["cfs"],
        } for p in caps],
    }
    by_num.setdefault(num, []).append(len(tags))
    tags.append(rec)

# captures that came in without a tag number/colour still happened — keep them as
# standalone catches so the counts and the bar chart match the dots on the map.
# they just aren't searchable (no number to look up).
for f in raw:
    p = f["properties"]
    if p["tag"] and p["color"]:
        continue
    tags.append({
        "num": p["tag"], "color": p["color"], "alpha": p["alpha"], "sp": p["sp"],
        "caps": [{
            "lng": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1],
            "dt": p["dt"], "rc": p["rc"], "spot": p["spot"], "in": p["in"], "mm": p["mm"],
            "file": p["file"], "tF": p["tF"], "lvl": p["lvl"], "turb": p["turb"],
            "do": p["do"], "cfs": p["cfs"],
        }],
    })

# the bar chart that sits next to the map: busiest tagging spots
spot_count = {}
for f in raw:
    sp = f["properties"]["spot"]
    if sp:
        spot_count[sp] = spot_count.get(sp, 0) + 1
top_spots = sorted(spot_count.items(), key=lambda kv: -kv[1])[:8]

species = {}
for f in raw:
    species[f["properties"]["sp"]] = species.get(f["properties"]["sp"], 0) + 1


# --- bucket every capture into tiles and write them ----------------------

if os.path.isdir(TILE_DIR):
    shutil.rmtree(TILE_DIR)

buckets = {}
for f in raw:
    p = f["properties"]
    lng, lat = f["geometry"]["coordinates"]
    props = {
        "tag": s(p["tag"]), "color": s(p["color"]), "sp": s(p["sp"]), "rc": s(p["rc"]),
        "tF": s(p["tF"]), "lvl": s(p["lvl"]), "turb": s(p["turb"]),
        "do": s(p["do"]), "cfs": s(p["cfs"]),
    }
    for z in range(MINZOOM, MAXZOOM + 1):
        xf, yf = to_frac(lng, lat, z)
        X, Y = int(xf), int(yf)
        lx = min(EXTENT, max(0, round((xf - X) * EXTENT)))
        ly = min(EXTENT, max(0, round((yf - Y) * EXTENT)))
        buckets.setdefault((z, X, Y), []).append((lx, ly, props))

for (z, X, Y), items in buckets.items():
    d = os.path.join(TILE_DIR, str(z), str(X))
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, f"{Y}.pbf"), "wb").write(build_tile(items))


# --- index + meta --------------------------------------------------------

lngs = [f["geometry"]["coordinates"][0] for f in raw]
lats = [f["geometry"]["coordinates"][1] for f in raw]
bounds = [min(lngs), min(lats), max(lngs), max(lats)]
recaps = sum(1 for f in raw if f["properties"]["rc"] == "Recaptured")

meta = {
    "minzoom": MINZOOM, "maxzoom": MAXZOOM, "bounds": bounds, "sourceLayer": LAYER,
    "count": len(raw), "recaptures": recaps, "journeys": sum(1 for t in tags if len(t["caps"]) > 1),
    "species": species, "topSpots": [{"spot": k, "n": v} for k, v in top_spots],
}

json.dump({"meta": meta, "tags": tags, "byNum": by_num},
          open(os.path.join(HERE, "fish_index.json"), "w"), separators=(",", ":"))
json.dump(meta, open(os.path.join(HERE, "tiles_meta.json"), "w"), indent=2)

print(f"captures   {len(raw):,}")
print(f"tags       {len(tags):,}  ({meta['journeys']} caught more than once)")
print(f"recaptures {recaps:,}")
print(f"tiles      {len(buckets):,}  (z{MINZOOM}-z{MAXZOOM})")
print(f"bounds     {[round(b,3) for b in bounds]}")
print(f"top spot   {top_spots[0][0]} ({top_spots[0][1]})")
print("done.")
