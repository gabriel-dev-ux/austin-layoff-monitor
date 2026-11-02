# WARN Texas / Austin Layoff Monitor

Restored for `gabriel-dev-ux` from the local `gabrielkutnews/austin-layoff-monitor` checkout, preserving its Git history, configuration, tests and last saved deduplication state.

The existing scope is **Travis, Williamson, Hays, Bastrop and Caldwell counties**. The monitor combines official Texas Workforce Commission WARN workbooks with five Google News RSS searches for local layoffs, major Austin employers and UT Austin. It sends Slack DMs using rules in `config.json`.

## Existing rules

- Every new official WARN notice in the five counties qualifies.
- Explicit local layoffs at priority employers qualify; other local employers qualify at 50 affected jobs or a facility closure.
- Companywide priority-employer cuts qualify at 500 jobs or 5% of staff, labeled with Austin impact unknown.
- Configurable publisher and employer lists suppress rumors, historical stories and excluded public employers. UT Austin remains an exception.
- Event clustering suppresses repeat coverage and allows material updates, such as a newly reported local impact.

## Recovery changes

The restored deployment keeps five-minute polling, the hourly backstop, state commits and self-chaining. Activation is gated by the `MONITOR_ENABLED` repository variable. Dry runs no longer read Slack credentials or write state. Workbook schema changes and unavailable sources fail source validation visibly. The new silent baseline mode prevents the weeks-old local checkpoint from causing a backlog of historical alerts after restoration.

## Hosting validation, November 2, 2026

All 29 tests pass. The official TWC workbook and all five news feeds work from the local Mac, and a fresh silent baseline has been saved. GitHub-hosted Ubuntu and Intel macOS runners receive an empty response for the TWC workbook, so the hosted source check correctly fails. News feeds remain reachable. Do not treat a published workflow or a successful local baseline as proof that official WARN polling works on GitHub. Keep activation paused until source access is resolved or choose a runtime with verified TWC access.

## Run and test

Standard-library Python; no third-party packages or paid APIs.

```sh
python3 -m unittest discover -v
python3 layoff_monitor.py --dry-run --check-sources
python3 layoff_monitor.py --seed-only
python3 layoff_monitor.py
```

Use `LAYOFF_STATE_FILE` to override the checkpoint path. `--show-suppressed` prints the reason a news item was rejected. A dry run sends no Slack messages and leaves the checkpoint unchanged.

## GitHub Actions setup

The **WARN Texas / Austin Layoffs** workflow offers `check`, `baseline` and `monitor` manual modes. Default mode is `check`, which runs tests and reads live feeds without sending alerts or modifying state.

1. Save encrypted repository secrets `SLACK_BOT_TOKEN` and `SLACK_USER_IDS` for the intended Slack bot and recipients. The new repository cannot inherit the old repository's secrets.
2. Run `baseline` to silently save current sources, without replaying old notices.
3. Set repository variable `MONITOR_ENABLED` to `true` and dispatch `monitor`.

Live polling runs every five minutes, state is committed every 30 minutes, and each 340-minute run starts its successor. The hourly backstop avoids disrupting an active run. Missing Slack configuration fails before entering the loop.

To stop, set `MONITOR_ENABLED` to `false` and cancel the active monitor run. Never commit tokens or `.env` files.
