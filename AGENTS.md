# Grok Register — AGENTS.md

## Entry points

```
python grok_register_ttk.py                        # GUI (needs Tkinter)
python grok_register_ttk.py cli                     # CLI (start after typing `start`)
python grok_register_ttk.py retry-pending <file>             # Pending recovery
python grok_register_ttk.py merge-accounts <f1> <f2> [-o f]  # Merge/dedup account files
```

## Setup

```
.venv\Scripts\Activate.ps1            # Windows
source .venv/bin/activate             # macOS/Linux
pip install -r requirements.txt
copy config.example.json config.json  # edit with real secrets
```

## Tests

```
python -m unittest discover -s tests
python tests/test_<name>.py
```

All tests use `unittest` + `unittest.mock.patch`. No pytest. `test_minimal_boundary_regressions.py` and `test_registration_flow.py` are the most informative for understanding patterns.

## Runtime quirks

- Python ≥3.14 auto-reexecs to 3.12/3.13 via `ensure_stable_python_runtime()` — don't fight it, it's intentional.
- `grok_register_ttk.py` is a compatibility adapter. It proxies function calls and mutable state to the real modules via `_CompatibilityModule`. When you need to import something, import from the real module, not from `grok_register_ttk`.
- Config validation is two-phase: `validate_config_structure` (types/enums) runs at GUI open; `validate_run_requirements` (provider-specific required fields) runs at start.
- Commands and error messages are in Chinese.
- Browser state is **thread-local** (`registration_browser._ns()` / `get_browser()` / `get_page()`). Do not reintroduce module-level `browser`/`page` globals — concurrent workers depend on TLS isolation.
- Proxy for Chromium is also thread-local (`browser_runtime._thread_proxy` + locked `cycle_proxy()`). Reading `config["proxy"]` mid-run is wrong under concurrency.
- `cpa_proxy` does **not** fall back to main `proxy`. Empty `cpa_proxy` means CPA OIDC HTTP + mint browser go direct.
- CPA browser is closed after every export (no shared reuse window left on `about:blank`).
- `cleanup_runtime_memory` only calls `shutdown_mint_browsers()` when reason contains `任务结束`, so parallel workers do not kill each other's CPA browsers mid-run.

## Architecture (short)

| Module | Responsibility |
|---|---|
| `registration_flow.py` | Pure orchestration via `run_batch(..., workers=N)`. Sequential if `workers<=1`, else `ThreadPoolExecutor`. No IO. |
| `registration_browser.py` | Per-thread browser lifecycle, page automation, SSO cookie wait |
| `browser_runtime.py` | HTTP (`curl_cffi`), proxy pool, headless options, CF/error-page detection |
| `mail_service.py` | DuckMail / YYDS / Cloudflare / Cloud Mail adapters |
| `app_config.py` | Config load/save/validate with atomic file writes |
| `account_outputs.py` | Account persistence, pending recovery, grok2api token pools, 9Router Grok CLI auto-add |
| `cpa_export.py` | CPA OIDC export entry, delegates to `cpa_xai` package |
| `cpa_xai/` | Self-contained CPA credential minting (uses `proxyutil.py` for auth proxy bridge) |

## Key dependencies

- **DrissionPage** (`>=4.1.1.2,<4.2`) — Chromium automation
- **curl_cffi** — HTTP requests with proxy fallback
- **filelock** — pending recovery and local token pool concurrency
- **cpa_xai.proxyutil** — local auth proxy bridge for authenticated proxies with Chromium

## Atomic writes

Config saves, token pool updates, and pending file rewrites all use: `tempfile.mkstemp` → write → `os.fsync` → `os.replace`. The `filelock` package guards concurrent access to token files and pending recovery.

## Config

`config.json` is gitignored. See `config.example.json` for the full schema.

- Email providers: `duckmail`, `yyds`, `cloudflare`, `cloudmail`
- grok2api pool names: `ssoBasic`, `ssoSuper`
- `proxy_pool_enabled` (default false): when true, round-robin `proxy_pool` (comma-separated URLs) via `cycle_proxy()`
- `browser_headless`: registration Chromium only; CPA uses separate `cpa_headless`
- `concurrent_workers` (1–8): parallel Chromium instances; default 1
- 9Router Grok CLI auto-add: `grok2api_auto_add_grok_cli` requires `cpa_export_enabled`; writes to `grok2api_9router_db_path` or `%APPDATA%/9router/db/data.sqlite`

## Concurrency notes

- Prefer workers=1 when debugging signup/CF issues.
- Direct IP + workers>1 often hits Cloudflare `Attention Required` — use proxy pool or lower concurrency.
- Headless increases CF challenge risk.

## Pending recovery

`*.pending.jsonl` files are created when an account registers successfully but the main output file write fails. Recover with `retry-pending`. Uses `filelock` on both pending and target files. Deduplicates by `(email, sso)`.

## CI / release

- `.github/workflows/build.yml`: PyInstaller one-file GUI on push to `main` and tags `v*`
- `main` push → updates prerelease tag `latest`
- `v*` tag → formal GitHub Release with `GrokRegister.exe`

## Python compat

Requires Python 3.9+. No `pyproject.toml`, no `tox`, no pre-commit hooks, no linter/formatter config.
