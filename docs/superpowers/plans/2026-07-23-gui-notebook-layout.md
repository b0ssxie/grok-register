# GUI Notebook Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the crowded single-page config form into a 4-tab `ttk.Notebook` and fix small control/layout defects, without changing config keys or registration logic.

**Architecture:** Only `GrokRegisterGUI.setup_ui` (and light theme styling) change. Four notebook tabs hold the same `self.*_var` widgets; buttons/status/log stay outside the notebook. `start_registration` keeps reading the same vars.

**Tech Stack:** Python 3.9+, stdlib `tkinter` / `ttk`, existing dark palette constants in `grok_register_ttk.py`.

**Spec:** `docs/superpowers/specs/2026-07-23-gui-notebook-layout-design.md`

## Global Constraints

- No new dependencies.
- No `app_config` schema changes.
- Keep every existing `self.*_var` name used by `start_registration`.
- Do not change `run_batch` / registration / CPA behavior.
- Chinese UI labels remain Chinese.
- Verify with: `python -m unittest discover -s tests` (must stay green).

## File map

| File | Role |
|------|------|
| `grok_register_ttk.py` | Only implementation file: theme + `setup_ui` layout |
| `tests/` | No new GUI tests required; run existing suite after changes |
| Spec (read-only) | Field → tab assignment |

### Var inventory (must all still exist after layout)

`email_provider_var`, `count_var`, `workers_var`, `nsfw_var`, `browser_headless_var`, `proxy_var`, `proxy_pool_enabled_var`, `proxy_pool_var`, `api_key_var`, `cloudflare_auth_mode_var`, `cloudflare_api_base_var`, `cloudflare_api_key_var`, `cloudflare_paths_var`, `cloudmail_api_base_var`, `cloudmail_domains_var`, `cloudmail_public_token_var`, `grok2api_local_auto_var`, `grok2api_pool_name_var`, `grok2api_local_file_var`, `grok2api_remote_auto_var`, `grok2api_remote_base_var`, `grok2api_remote_key_var`, `cpa_export_var`, `cpa_auth_dir_var`, `grok2api_grok_cli_var`, `grok2api_9router_db_var`

---

### Task 1: Window size + notebook theme

**Files:**
- Modify: `grok_register_ttk.py` (`GrokRegisterGUI.__init__` geometry/minsize; `setup_light_theme`)

- [ ] **Step 1: Shrink default window so log area is usable**

In `GrokRegisterGUI.__init__` change:

```python
self.root.geometry("1000x720")
self.root.minsize(880, 600)
```

(was `1120x900` / `960x700`)

- [ ] **Step 2: Style `ttk.Notebook` for dark UI**

In `setup_light_theme`, after existing `style.configure` calls, add:

```python
style.configure("TNotebook", background=UI_BG, borderwidth=0)
style.configure(
    "TNotebook.Tab",
    background=UI_BUTTON_BG,
    foreground=UI_FG,
    padding=[12, 4],
)
style.map(
    "TNotebook.Tab",
    background=[("selected", UI_PANEL_BG), ("active", UI_ACTIVE_BG)],
    foreground=[("selected", UI_FG), ("active", UI_FG)],
)
style.configure("Tab.TFrame", background=UI_PANEL_BG)
```

- [ ] **Step 3: Compile-check**

Run:

```bash
python -c "import py_compile; py_compile.compile('grok_register_ttk.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add grok_register_ttk.py
git commit -m "style: dark notebook tabs and smaller default GUI window"
```

---

### Task 2: Replace flat config grid with notebook skeleton + helpers

**Files:**
- Modify: `grok_register_ttk.py` (`setup_ui` only)

- [ ] **Step 1: Replace `config_frame` LabelFrame with notebook**

In `setup_ui`, delete the `config_frame = tk.LabelFrame(...)` block and its two `grid_columnconfigure` lines. Insert:

```python
notebook = ttk.Notebook(main_frame)
notebook.grid(row=0, column=0, sticky=tk.EW, pady=(0, 8))

def make_tab(title):
    frame = ttk.Frame(notebook, style="Tab.TFrame", padding=10)
    notebook.add(frame, text=title)
    # inner tk.Frame so existing tk widgets get panel bg
    inner = tk.Frame(frame, bg=UI_PANEL_BG)
    inner.pack(fill=tk.BOTH, expand=True)
    inner.grid_columnconfigure(1, weight=1, minsize=220)
    inner.grid_columnconfigure(3, weight=1, minsize=220)
    return inner

tab_basic = make_tab("基础")
tab_mail = make_tab("邮箱")
tab_pool = make_tab("入池")
tab_cpa = make_tab("CPA")
```

Keep `main_frame.grid_rowconfigure(3, weight=1)` so log still expands.

- [ ] **Step 2: Parent-scoped grid helpers**

Replace the old nested `add_label` / `add_field` that hardcode `config_frame` with:

```python
def add_label(parent, row, column, text):
    tk_label(parent, text=text, bg=UI_PANEL_BG).grid(
        row=row, column=column, sticky=tk.W, padx=(0, 6), pady=4,
    )

def add_field(parent, widget, row, column, columnspan=1, sticky=tk.EW):
    widget.grid(
        row=row, column=column, columnspan=columnspan,
        sticky=sticky, padx=(0, 12), pady=4,
    )
```

All later field creation must pass `parent` as first arg to these helpers.

- [ ] **Step 3: Temporarily keep one field so file still runs (optional smoke)**

If mid-edit the file is incomplete, finish Task 3 in the same working session before running the app. Do not leave `setup_ui` without creating all vars that `start_registration` reads.

- [ ] **Step 4: Commit skeleton only if tabs + helpers are in place and all fields already reparented (prefer combine with Task 3 if atomic)**

If committing skeleton alone is incomplete (missing vars → AttributeError on Start), **do not commit yet** — continue Task 3 in the same commit.

---

### Task 3: Populate four tabs (all fields)

**Files:**
- Modify: `grok_register_ttk.py` (`setup_ui` field construction)

**Interfaces:**
- Produces: all vars listed in inventory, attached to correct tab parents
- Consumes: `add_label(parent, ...)`, `add_field(parent, ...)`

- [ ] **Step 1: Build 基础 tab**

On `tab_basic`:

| Row | Col0–1 | Col2–3 |
|-----|--------|--------|
| 0 | 邮箱服务商 + OptionMenu | 数量/并发 Spinboxes (same count_frame pattern as now) |
| 1 | 注册选项 + NSFW + 无头 Checkbuttons | 代理 Entry |
| 2 | 代理池 + 启用 Checkbutton (`text="启用"`) | (empty or spacer) |
| 3 | 代理池列表 label | Entry `columnspan=3` width~72 |

Keep var names: `email_provider_var`, `count_var`, `workers_var`, `nsfw_var`, `browser_headless_var`, `proxy_var`, `proxy_pool_enabled_var`, `proxy_pool_var`.

For checkboxes inside tabs, prefer:

```python
tk_checkbutton(parent, text="...", variable=..., bg=UI_PANEL_BG, activebackground=UI_PANEL_BG)
```

If `tk_checkbutton` always forces `bg=UI_BG`, either pass override if supported or set after create:

```python
cb = tk_checkbutton(...)
cb.configure(bg=UI_PANEL_BG, activebackground=UI_PANEL_BG)
```

Inspect `tk_checkbutton` — it uses `bg=UI_BG` fixed. **Fix helper** so optional `bg` works:

```python
def tk_checkbutton(parent, text="", variable=None, **kwargs):
    bg = kwargs.pop("bg", UI_BG)
    return tk.Checkbutton(
        parent,
        text=text,
        variable=variable,
        bg=bg,
        fg=kwargs.pop("fg", UI_FG),
        activebackground=kwargs.pop("activebackground", bg),
        activeforeground=kwargs.pop("activeforeground", UI_FG),
        selectcolor="#3d7be0",
        **kwargs,
    )
```

- [ ] **Step 2: Build 邮箱 tab**

On `tab_mail`:

| Row | Content |
|-----|---------|
| 0 | DuckMail API Key (span 3) |
| 1 | Cloudflare 鉴权模式 \| CF 路径 |
| 2 | Cloudflare API Base (span 3) |
| 3 | Cloudflare API Key (span 3 or half) |
| 4 | Cloud Mail API Base \| Cloud Mail 域名 |
| 5 | Cloud Mail Public Token (span 3) |

Vars: `api_key_var`, `cloudflare_auth_mode_var`, `cloudflare_paths_var`, `cloudflare_api_base_var`, `cloudflare_api_key_var`, `cloudmail_api_base_var`, `cloudmail_domains_var`, `cloudmail_public_token_var`.

Keep the same default path join for `cloudflare_paths_var`.

- [ ] **Step 3: Build 入池 tab**

On `tab_pool`:

| Row | Content |
|-----|---------|
| 0 | grok2api 本地入池 + Checkbutton `text="启用"` \| 池名 OptionMenu |
| 1 | 本地 token.json Entry span 3 |
| 2 | grok2api 远端入池 + Checkbutton `text="启用"` |
| 3 | 远端 Base span 3 |
| 4 | 远端 app_key span 3 |

Vars: `grok2api_local_auto_var`, `grok2api_pool_name_var`, `grok2api_local_file_var`, `grok2api_remote_auto_var`, `grok2api_remote_base_var`, `grok2api_remote_key_var`.

- [ ] **Step 4: Build CPA tab**

On `tab_cpa`:

| Row | Content |
|-----|---------|
| 0 | OIDC/CPA Checkbutton full text as now |
| 1 | CPA 输出目录 Entry span 3 |
| 2 | 9Router Grok CLI Checkbutton |
| 3 | 9Router DB 路径 Entry span 3 |

Vars: `cpa_export_var`, `cpa_auth_dir_var`, `grok2api_grok_cli_var`, `grok2api_9router_db_var`.

- [ ] **Step 5: Leave btn_frame / status_frame / log_frame as they are**

Do not move Start/Stop/Clear, status, or log into tabs. Grid rows stay 1/2/3.

- [ ] **Step 6: Verify `start_registration` still references only existing attrs**

Grep:

```bash
# PowerShell
Select-String -Path grok_register_ttk.py -Pattern "self\.\w+_var"
```

Every `_var` used in `start_registration` must be assigned in `setup_ui`.

- [ ] **Step 7: Run unit tests**

```bash
.venv\Scripts\Activate.ps1
python -m unittest discover -s tests
```

Expected: `Ran 50 tests` (or current count) `OK`

- [ ] **Step 8: Commit**

```bash
git add grok_register_ttk.py
git commit -m "feat(ui): split config into 4 notebook tabs (基础/邮箱/入池/CPA)"
```

---

### Task 4: Control polish pass

**Files:**
- Modify: `grok_register_ttk.py` (helpers + any leftover layout)

- [ ] **Step 1: Confirm checkbox labels**

- Local/remote pool: `text="启用"`
- Proxy pool enable: `text="启用"`
- NSFW / headless / CPA / 9Router keep descriptive Chinese text

- [ ] **Step 2: Proxy pool layout**

Must be two rows on 基础:

```text
代理池:  [x] 启用
代理池列表: [___________________________]  (columnspan=3)
```

Not enable + long entry on the same cramped row.

- [ ] **Step 3: Optional Spinbox bg on tab panels**

count/workers spinboxes: parent frames use `bg=UI_PANEL_BG`.

- [ ] **Step 4: Re-run tests**

```bash
python -m unittest discover -s tests
```

Expected: OK

- [ ] **Step 5: Commit if anything changed**

```bash
git add grok_register_ttk.py
git commit -m "fix(ui): checkbox labels and proxy pool row layout"
```

---

### Task 5: Manual verification checklist

No code unless bugs found.

- [ ] **Step 1: Launch GUI**

```bash
.venv\Scripts\Activate.ps1
python grok_register_ttk.py
```

- [ ] **Step 2: Manual checks**

1. Four tabs visible: 基础 / 邮箱 / 入池 / CPA  
2. Each tab shows expected fields (see Task 3 tables)  
3. Log area visible without maximizing  
4. Change a value on each tab → 开始注册 (or trigger save path) → restart app → values reload  
5. 开始 enables 停止; 停止 works  
6. No unlabeled bare checkboxes on 入池  

- [ ] **Step 3: Fix any layout bug found, re-test, commit**

```bash
git add grok_register_ttk.py
git commit -m "fix(ui): notebook layout follow-up from manual check"
```

- [ ] **Step 4: Push when ready**

```bash
git push origin main
```

---

## Spec coverage (self-review)

| Spec requirement | Task |
|------------------|------|
| 4-tab Notebook 基础/邮箱/入池/CPA | Task 2–3 |
| Buttons/status/log outside tabs | Task 2–3 |
| Window ~1000x720 / minsize ~880x600 | Task 1 |
| Keep all vars / start_registration | Task 3 |
| Unlabeled checkbox fix | Task 3–4 |
| Proxy pool two-row layout | Task 3–4 |
| Panel bg for checks | Task 3 (`tk_checkbutton` bg) |
| Notebook dark styling | Task 1 |
| No schema / business logic change | Global constraints |
| unittest green | Task 3–4 |
| Manual checks | Task 5 |

**Placeholder scan:** none.  
**Type consistency:** var names match `start_registration` block at `grok_register_ttk.py` ~1016–1048.

## Out of scope (do not implement)

- Provider-conditional field visibility  
- Disable tabs while running  
- Full ttk migration of Entry/Button  
