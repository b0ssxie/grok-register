# Grok Register — AGENTS.md

## Entry points

```
python grok_register_ttk.py                        # GUI (needs Tkinter)
python grok_register_ttk.py cli                     # CLI (start after typing `start`)
python grok_register_ttk.py retry-pending <file>    # Pending recovery
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

## Architecture (short)

| Module | Responsibility |
|---|---|
| `registration_flow.py` | Pure orchestration via `run_batch(RegistrationCallbacks, RegistrationOperations)`. No IO. |
| `registration_browser.py` | Browser lifecycle, page automation, SSO cookie wait |
| `browser_runtime.py` | HTTP (`curl_cffi`), proxy handling, `ChromiumOptions` via DrissionPage |
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

`config.json` is gitignored. See `config.example.json` for the full schema. Email providers: `duckmail`, `yyds`, `cloudflare`, `cloudmail`. grok2api pool names: `ssoBasic`, `ssoSuper`. Proxy pool: comma-separated proxy URLs in `proxy_pool`, round-robin per account start. 9Router Grok CLI auto-add via `grok2api_auto_add_grok_cli` + `grok2api_9router_db_path`.

## Pending recovery

`*.pending.jsonl` files are created when an account registers successfully but the main output file write fails. Recover with `retry-pending`. Uses `filelock` on both pending and target files. Deduplicates by `(email, sso)`.

## Python compat

Requires Python 3.9+. No `pyproject.toml`, no `tox`, no CI workflows, no pre-commit hooks, no linter/formatter config.
