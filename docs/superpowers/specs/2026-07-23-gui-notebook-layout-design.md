# GUI Notebook Layout Design

Date: 2026-07-23  
Scope: polish Tk GUI layout and fix control crowding — no business logic changes.

## Problem

`GrokRegisterGUI.setup_ui()` packs all config fields into a single 4-column grid (~15 rows). After proxy pool, headless, concurrent workers, and 9Router fields were added, the config block crowds the log area and makes related settings hard to scan. Some checkboxes lack labels; proxy-pool enable + long entry share one cramped row; panel vs checkbox backgrounds are inconsistent.

## Goals

1. Reduce visual crowding by splitting config into a 4-tab `ttk.Notebook`.
2. Keep log/status/buttons always visible with a sensible default window size.
3. Fix small control/layout defects while touching the UI.
4. Preserve all existing config keys, vars, and `start_registration` save/load behavior.

## Non-goals

- New GUI frameworks or dependencies.
- Full theme redesign / light mode.
- Provider-conditional field visibility (show only active email provider).
- Runtime disable of notebook while job runs (optional later).

## Approach

**Chosen:** A — `ttk.Notebook` re-layout only, keep existing `tk` widgets and helpers.

Rejected:

- B — migrate most widgets to pure `ttk` (larger churn, less payoff).
- C — dynamic show/hide by email provider (better UX later, more logic now).

## Architecture

### Layout skeleton

```
main_frame
├── notebook (ttk.Notebook)     # row 0, sticky EW
│   ├── 基础
│   ├── 邮箱
│   ├── 入池
│   └── CPA
├── btn_frame                   # row 1  开始 / 停止 / 清空日志
├── status_frame                # row 2  状态 + 统计
└── log_frame                   # row 3  ScrolledText, weight=1
```

Window defaults (adjust if needed during impl):

- geometry: ~`1000x720` (or keep width, reduce height vs current `1120x900`)
- minsize: ~`880x600`

### Tab contents

| Tab | Fields |
|-----|--------|
| **基础** | `email_provider`, `register_count`, `concurrent_workers`, `enable_nsfw`, `browser_headless`, `proxy`, `proxy_pool_enabled`, `proxy_pool` |
| **邮箱** | DuckMail key; Cloudflare base / key / auth mode / paths; Cloud Mail base / domains / public token |
| **入池** | local auto-add, pool name, local token file; remote auto-add, remote base, remote app_key |
| **CPA** | `cpa_export_enabled`, `cpa_auth_dir`, `grok2api_auto_add_grok_cli`, `grok2api_9router_db_path` |

Always-visible chrome:

- Start / Stop / Clear log
- Status + counters (`成功 | 失败 | CPA | 待恢复 | 后处理警告`)
- Log view

### Implementation notes

File: `grok_register_ttk.py` only (primarily `GrokRegisterGUI.setup_ui`).

1. Replace single `config_frame` LabelFrame with `ttk.Notebook` + four frames.
2. Extract a small grid helper that takes `parent` (reuse `add_label` / `add_field` pattern).
3. Keep all `self.*_var` names; only change parent widgets and grid coordinates.
4. `start_registration` continues reading the same vars — no schema change.
5. Style notebook via existing `setup_light_theme` / `ttk.Style` (dark-friendly tab colors if easy).

### Control fixes (in scope)

| Issue | Fix |
|-------|-----|
| Unlabeled checkboxes (local/remote pool) | Set `text="启用"` (or equivalent short label) |
| Proxy pool enable + long URL on one crowded row | Enable on row with label; pool entry full-width row below |
| Checkbutton bg vs panel bg mismatch | Use `UI_PANEL_BG` inside tab panels |
| Dense padding | Slightly increase pady/padx inside tabs for readability |

### Data flow (unchanged)

```
load_config → vars from config.get
user ↓
user edits tabs
      ↓
start_registration reads vars → config → validate_run_requirements → save_config → run_batch
```

### Error handling

- No new validation rules.
- Invalid concurrent_workers / count still fail at existing validate/save path.

### Testing

- Unit tests: no GUI layout assertions; existing suite should stay green.
- Manual:
  1. Open GUI, switch all 4 tabs, confirm fields present.
  2. Change values on each tab, Start once (or save path), restart app, values reload.
  3. Log area remains usable at default size.
  4. Start/Stop still enable/disable correctly.

## Risks

- `ttk.Notebook` on Windows dark theme may look slightly different from pure `tk` frames — accept minor theme mismatch.
- Very long proxy_pool strings still need horizontal space; full-width row mitigates.

## Out of scope follow-ups

- Show only fields for selected email provider.
- Disable config tabs while registration is running.
- Dedicated settings dialog / scrollable single page.
