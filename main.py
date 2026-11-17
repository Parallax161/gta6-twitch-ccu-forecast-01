"""GTA VI launch-day Twitch viewers: learned hourly profile (ratio to hour 1) with an empirical spread.

Python 3.13, standard library only, deterministic.
"""

import json
import math
import os
import statistics
from datetime import datetime, timedelta
from pathlib import Path

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]

# Console launches that unlocked at midnight local (rolling), the shape GTA VI shares.
ANALOGUES = {
    "Marvel's Wolverine", "God of War Ragnarök", "Red Dead Redemption 2", "Marvel's Spider-Man 2",
    "Ghost of Yōtei", "Monster Hunter Wilds", "The Legend of Zelda: Tears of the Kingdom",
    "FINAL FANTASY VII REBIRTH", "The Last of Us Part II", "Ghost of Tsushima", "Stellar Blade", "Saros",
    "Resident Evil Requiem", "Call of Duty: Black Ops 6", "Call of Duty: Modern Warfare III",
    "Call of Duty: Black Ops 7", "Call of Duty: Modern Warfare 4",
}

HOURS = list(range(2, 25))
RIDGE = 2.0
SIGMA_FLOOR = 0.25
SIGMA_MULT = 1.1


def day_ratios(comp):
    """ln(viewers_h / viewers_1) for h = 2..24 of the comparable's release day, or None if incomplete."""
    by = {r["from"]: r["viewers"] for r in comp["hourly"]}
    prefix = comp["day_start"][:11]
    row = [by.get(f"{prefix}{h:02d}:00:00Z") for h in range(24)]
    if any(v is None or v <= 0 for v in row):
        return None
    return [math.log(v / row[0]) for v in row[1:]]


def parse(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def peak_feature(rows, day_start, p1):
    """ln(hour 1 / the highest whole-hour count of the 48 h before the day), or None without history."""
    t0 = parse(day_start)
    lo = t0 - timedelta(hours=48)
    vals = [r["viewers"] for r in rows if lo <= parse(r["from"]) < t0 and r["viewers"] and r["viewers"] > 0]
    if not vals:
        return None
    return math.log(max(p1, 1) / max(vals))


def training(comps):
    """(ratios to hour 1, level feature) for every analogue with a full day."""
    out = []
    for c in comps:
        if c["name"] not in ANALOGUES:
            continue
        r = day_ratios(c)
        if not r:
            continue
        by = {x["from"]: x["viewers"] for x in c["hourly"]}
        p1 = by[c["day_start"][:11] + "00:00:00Z"]
        out.append((r, peak_feature(c["hourly"], c["day_start"], p1)))
    return out


def forecast_from(p1, comps, hist_rows, day_start):
    data = training(comps)
    x0 = peak_feature(hist_rows, day_start, p1) if hist_rows else None
    use_x = x0 is not None
    if use_x:
        data_x = [(r, x) for r, x in data if x is not None]
        use_x = len(data_x) >= 6
    if use_x:
        data = data_x
        xs = [x for _, x in data]
        mx = sum(xs) / len(xs)
        sxx = sum((x - mx) ** 2 for x in xs) + RIDGE
    mus, sds = [], []
    for i in range(len(HOURS)):
        ys = [r[i] for r, _ in data]
        my = sum(ys) / len(ys)
        if use_x:
            b = sum((x - mx) * (y - my) for (r, x), y in zip(data, ys)) / sxx
            res = [y - my - b * (x - mx) for (r, x), y in zip(data, ys)]
            mu = my + b * (x0 - mx)
        else:
            res = [y - statistics.median(ys) for y in ys]
            mu = statistics.median(ys)
        mus.append(mu)
        sds.append(statistics.pstdev(res))
    # Smooth the spread over neighbouring hours: 23 noisy estimates from a dozen launches.
    n = len(sds)
    smooth = [statistics.fmean(sds[max(0, i - 1):i + 2]) for i in range(n)]
    out = []
    for i, h in enumerate(HOURS):
        s = max(SIGMA_FLOOR, smooth[i] * SIGMA_MULT)
        q = [p1 * math.exp(mus[i] + z * s) for z in Z]
        out.append({"hour": h, "q": [round(max(v, 0.01), 2) for v in q]})
    return {"hours": out}


def forecast_case(case):
    p1 = max(1, case["known"][0]["viewers"])
    return forecast_from(p1, case["comparables"], case["history_hourly"], case["day_start"])


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast_case(case), separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
