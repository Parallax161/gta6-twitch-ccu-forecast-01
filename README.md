# gta6-twitch-ccu-forecast-01

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/parallax161/gta6-twitch-ccu-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/parallax161/gta6-twitch-ccu-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Forecasts how many people watch Grand Theft Auto VI live on Twitch in each hour of its release day (19 November 2026, UTC), after the first hour. `main.py` (Python 3.13, standard library only, deterministic) reads each `*.in` case and writes `<id>.out` with five quantiles (5%, 25%, 50%, 75%, 95%) for hours 2–24.

## Run it

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Approach

1. **Learned hourly profile.** From the case's own `comparables` it takes console launches that unlocked at midnight local (rolling), the same shape as GTA VI. For each hour 2–24 it takes ln(viewers_h / viewers_1) across those launches. The pattern is a dip to about 0.8× hour 1 in the first hours, then growth to about 2–3× by the US evening.
2. **Level handling.** Each hour's log-ratio is ridge-regressed on how hot hour 1 is: ln(hour 1 / highest hourly count of the prior 48 h). A launch whose hour 1 is already near its pre-launch peak grows less afterwards.
3. **Spread.** The quantiles are lognormal around that median. The sigma is the regression's residual std across launches, smoothed over neighbouring hours, ×1.1 as a margin, with a floor of 0.25. Spread therefore widens where launches disagree (the late, regional hours).

## Scores

The kit holds no local answers for the practice cases (p00–p03 are scored on the server). So it was scored leave-one-out over the 13 complete comparable launches: each launch was forecast from the others only, and the loss is the mean pinball loss on the log scale, as in the rules.

| Version | LOO loss |
|---|---|
| Persistence (house formula) | 0.379 |
| v1: median profile + std spread | 0.251 |
| v2: + level regression on hour 1 vs prior peak | 0.230 |
| v3 (final): + spread smoothed across hours | 0.230 |

The final beats persistence on 12 of the 13 launches. The exception is The Last of Us Part II (0.346 vs 0.247), which had leaked content days before release. The rules put persistence at about 0.387 on the practice.

---

<sub>Entered on [make.fun](https://make.fun/?ref=dxyyk152&utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
