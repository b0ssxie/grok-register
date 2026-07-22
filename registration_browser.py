"""管理主注册浏览器生命周期并实现注册页面自动化操作。"""
import gc
import os
import random
import re
import secrets
import signal
import struct
import subprocess
import sys
import threading
import time
import types

from DrissionPage import Chromium
from DrissionPage.errors import PageDisconnectedError
from curl_cffi import requests

_tls = threading.local()
_STATE_NAMES = (
    "browser",
    "page",
    "browser_proxy_bridge",
    "browser_started_with_proxy",
    "cf_clearance",
)


def _ns():
    t = _tls
    if not hasattr(t, "browser"):
        t.browser = None
        t.page = None
        t.browser_proxy_bridge = None
        t.browser_started_with_proxy = False
        t.cf_clearance = ""
    return t


def get_browser():
    return _ns().browser


def get_page():
    return _ns().page


class _RegistrationBrowserModule(types.ModuleType):
    def __getattr__(self, name):
        if name in _STATE_NAMES:
            return getattr(_ns(), name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in _STATE_NAMES:
            setattr(_ns(), name, value)
            return
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _RegistrationBrowserModule
SIGNUP_URL = "https://accounts.x.ai/sign-up?redirect=grok-com"
_OWN_NAMES = {'is_cloudflare_block_response', 'response_preview', 'start_browser', 'enable_nsfw_for_token', 'stop_browser_proxy_bridge', 'set_tos_accepted', 'fill_email_and_submit', 'getTurnstileToken', 'set_birth_date', 'generate_random_birthdate', 'fill_profile_and_submit', 'click_email_signup_button', 'wait_for_sso_cookie', 'fill_code_and_submit', 'build_profile', 'cleanup_runtime_memory', 'open_signup_page', 'stop_browser', 'encode_grpc_nsfw_settings', 'restart_browser', 'has_profile_form', 'update_nsfw_settings', 'refresh_active_page', 'get_browser', 'get_page'}

def bind_runtime(namespace):
    for (name, value) in namespace.items():
        if name.startswith('__') or name in _OWN_NAMES or name in {'browser', 'page', 'browser_proxy_bridge', 'browser_started_with_proxy', 'cf_clearance'}:
            continue
        globals()[name] = value

def generate_random_birthdate():
    import datetime as dt
    today = dt.date.today()
    age = random.randint(20, 40)
    birth_year = today.year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    return f'{birth_year}-{birth_month:02d}-{birth_day:02d}T16:00:00.000Z'

def response_preview(res, limit=200):
    try:
        text = str(res.text or '')
    except Exception:
        text = ''
    text = re.sub('\\s+', ' ', text).strip()
    return text[:limit]

def is_cloudflare_block_response(res):
    try:
        headers = {str(k).lower(): str(v).lower() for (k, v) in dict(res.headers).items()}
        text = str(res.text or '').lower()
        server = headers.get('server', '')
        content_type = headers.get('content-type', '')
        return res.status_code in (403, 429, 503) and ('cloudflare' in server or 'cloudflare' in text or 'cf-error' in text or ('__cf_chl' in text) or ('text/html' in content_type))
    except Exception:
        return False

def set_birth_date(session, log_callback=None):
    url = 'https://grok.com/rest/auth/set-birth-date'
    new_headers = {'content-type': 'application/json', 'origin': 'https://grok.com', 'referer': 'https://grok.com/'}
    payload = {'birthDate': generate_random_birthdate()}
    try:
        res = session.post(url, json=payload, headers=new_headers, timeout=15)
        if log_callback:
            log_callback(f'[Debug] set_birth_date status: {res.status_code}, body: {response_preview(res)}')
        if 200 <= res.status_code < 300:
            return (True, 'ok')
        if is_cloudflare_block_response(res):
            return (False, f'set_birth_date 被 grok.com 的 Cloudflare 防护拦截，HTTP {res.status_code}')
        return (False, f'set_birth_date HTTP {res.status_code}: {response_preview(res)}')
    except Exception as e:
        if log_callback:
            log_callback(f'[set_birth_date] 异常: {e}')
        return (False, f'set_birth_date 异常: {e}')

def set_tos_accepted(session, log_callback=None):
    url = 'https://accounts.x.ai/auth_mgmt.AuthManagement/SetTosAcceptedVersion'
    payload = struct.pack('B', 2 << 3 | 0) + struct.pack('B', 1)
    data = b'\x00' + struct.pack('>I', len(payload)) + payload
    new_headers = {'content-type': 'application/grpc-web+proto', 'x-grpc-web': '1', 'x-user-agent': 'connect-es/2.1.1', 'origin': 'https://accounts.x.ai', 'referer': 'https://accounts.x.ai/accept-tos'}
    try:
        res = session.post(url, data=data, headers=new_headers, timeout=15)
        if log_callback:
            log_callback(f'[Debug] set_tos_accepted status: {res.status_code}')
        if 200 <= res.status_code < 300:
            return (True, 'ok')
        if is_cloudflare_block_response(res):
            return (False, f'set_tos_accepted 被 accounts.x.ai 的 Cloudflare 防护拦截，HTTP {res.status_code}')
        return (False, f'set_tos_accepted HTTP {res.status_code}: {response_preview(res)}')
    except Exception as e:
        if log_callback:
            log_callback(f'[set_tos_accepted] 异常: {e}')
        return (False, f'set_tos_accepted 异常: {e}')

def encode_grpc_nsfw_settings():
    field1_content = bytes([16, 1])
    field1 = bytes([10, len(field1_content)]) + field1_content
    nsfw_string = b'always_show_nsfw_content'
    field2_inner = bytes([10, len(nsfw_string)]) + nsfw_string
    field2 = bytes([18, len(field2_inner)]) + field2_inner
    payload = field1 + field2
    return b'\x00' + struct.pack('>I', len(payload)) + payload

def update_nsfw_settings(session, log_callback=None):
    url = 'https://grok.com/auth_mgmt.AuthManagement/UpdateUserFeatureControls'
    data = encode_grpc_nsfw_settings()
    new_headers = {'content-type': 'application/grpc-web+proto', 'x-grpc-web': '1', 'origin': 'https://grok.com', 'referer': 'https://grok.com/'}
    try:
        res = session.post(url, data=data, headers=new_headers, timeout=15)
        if log_callback:
            log_callback(f'[Debug] update_nsfw status: {res.status_code}, body: {response_preview(res)}')
        if 200 <= res.status_code < 300:
            return (True, 'ok')
        if is_cloudflare_block_response(res):
            return (False, f'update_nsfw_settings 被 grok.com 的 Cloudflare 防护拦截，HTTP {res.status_code}')
        return (False, f'update_nsfw_settings HTTP {res.status_code}: {response_preview(res)}')
    except Exception as e:
        if log_callback:
            log_callback(f'[update_nsfw] 异常: {e}')
        return (False, f'update_nsfw_settings 异常: {e}')

def enable_nsfw_for_token(token, cf_clearance='', log_callback=None):
    proxies = get_proxies()
    user_agent = get_user_agent()
    try:
        with requests.Session(impersonate='chrome120', proxies=proxies) as session:
            cookie_parts = [f'sso={token}', f'sso-rw={token}']
            if cf_clearance:
                cookie_parts.append(f'cf_clearance={cf_clearance}')
            session.headers.update({'user-agent': user_agent, 'cookie': '; '.join(cookie_parts)})
            (ok, message) = set_tos_accepted(session, log_callback)
            if not ok:
                return (False, message)
            (ok, message) = set_birth_date(session, log_callback)
            if not ok:
                return (False, message)
            (ok, message) = update_nsfw_settings(session, log_callback)
            if not ok:
                return (False, message)
            return (True, '成功开启 NSFW')
    except Exception as e:
        return (False, f'异常: {str(e)}')

def stop_browser_proxy_bridge():
    pass
    if _ns().browser_proxy_bridge is not None:
        try:
            _ns().browser_proxy_bridge.stop()
        except Exception:
            pass
    _ns().browser_proxy_bridge = None

def _kill_browser_process(pid):
    if not pid:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except (OSError, AttributeError):
        pass
    try:
        subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True, timeout=3)
    except Exception:
        pass

def start_browser(log_callback=None, use_proxy=True):
    pass
    stop_browser()
    last_exc = None
    if use_proxy:
        cycle_proxy()
    proxy_enabled = bool(use_proxy and get_configured_proxy())
    for attempt in range(1, 5):
        bridge = None
        try:
            (browser_proxy, bridge) = prepare_browser_proxy(use_proxy=use_proxy, log_callback=log_callback)
            _ns().browser = Chromium(create_browser_options(browser_proxy=browser_proxy))
            _ns().browser_proxy_bridge = bridge
            _ns().browser_started_with_proxy = bool(browser_proxy)
            tabs = _ns().browser.get_tabs()
            _ns().page = tabs[-1] if tabs else _ns().browser.new_tab()
            if log_callback and getattr(_ns().browser, 'user_data_path', None):
                log_callback(f'[Debug] 当前浏览器资料目录: {_ns().browser.user_data_path}')
            if log_callback and get_configured_proxy():
                mode = '代理' if _ns().browser_started_with_proxy else '直连'
                log_callback(f'[*] 浏览器网络模式: {mode}')
            if log_callback and attempt > 1:
                log_callback(f'[*] 浏览器第 {attempt} 次启动成功')
            return (_ns().browser, _ns().page)
        except Exception as exc:
            last_exc = exc
            if bridge is not None:
                try:
                    bridge.stop()
                except Exception:
                    pass
            if log_callback:
                mode = '代理' if proxy_enabled else '直连'
                log_callback(f'[Debug] 浏览器{mode}启动失败(第{attempt}/4次): {exc}')
            try:
                if _ns().browser is not None:
                    _ns().browser.quit(del_data=True)
            except Exception:
                pass
            _ns().browser = None
            _ns().page = None
            _ns().browser_proxy_bridge = None
            _ns().browser_started_with_proxy = False
            time.sleep(min(1.5 * attempt, 4))
    raise Exception(f'浏览器启动失败，已重试4次: {last_exc}')

def stop_browser():
    pass
    pid = None
    if _ns().browser is not None:
        try:
            pid = _ns().browser.process_id
        except Exception:
            pass
        try:
            _ns().browser.quit(del_data=True)
        except Exception:
            pass
    stop_browser_proxy_bridge()
    _ns().browser = None
    _ns().page = None
    _ns().browser_started_with_proxy = False
    if pid:
        time.sleep(0.5)
        _kill_browser_process(pid)

def restart_browser(log_callback=None, use_proxy=True):
    stop_browser()
    return start_browser(log_callback=log_callback, use_proxy=use_proxy)

def cleanup_runtime_memory(log_callback=None, reason='定期清理'):
    if log_callback:
        log_callback(f'[*] {reason}: 关闭浏览器并清理内存')
    stop_browser()
    # 仅任务结束时清理全局 CPA 浏览器注册表，避免并发 worker 互相误杀
    if '任务结束' in str(reason or ''):
        try:
            from cpa_xai.browser_confirm import shutdown_mint_browsers
            shutdown_mint_browsers()
        except Exception as exc:
            if log_callback:
                log_callback(f'[Debug] CPA 浏览器清理失败: {exc}')
    collected = gc.collect()
    if log_callback:
        log_callback(f'[*] Python GC 已回收对象数: {collected}')

def refresh_active_page():
    pass
    if _ns().browser is None:
        restart_browser()
    try:
        tabs = _ns().browser.get_tabs()
        if tabs:
            _ns().page = tabs[-1]
        else:
            _ns().page = _ns().browser.new_tab()
    except Exception:
        restart_browser()
    return _ns().page

def click_email_signup_button(timeout=10, log_callback=None, cancel_callback=None):
    pass
    deadline = time.time() + timeout
    while time.time() < deadline:
        raise_if_cancelled(cancel_callback)
        if page_has_proxy_error(_ns().page):
            raise Exception('注册页代理/网络错误（无法加载真实页面）')
        if log_callback:
            log_callback('[Debug] 尝试查找“使用邮箱注册”按钮...')
        clicked = _ns().page.run_js('\nfunction isVisible(node) {\n    if (!node) return false;\n    const style = window.getComputedStyle(node);\n    if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') return false;\n    const rect = node.getBoundingClientRect();\n    return rect.width > 0 && rect.height > 0;\n}\nfunction nodeText(node) {\n    return [\n        node.innerText,\n        node.textContent,\n        node.getAttribute(\'aria-label\'),\n        node.getAttribute(\'title\'),\n        node.getAttribute(\'href\'),\n    ].filter(Boolean).join(\' \').replace(/\\s+/g, \' \').trim();\n}\nfunction scoreEntry(node) {\n    const compact = nodeText(node).replace(/\\s+/g, \'\');\n    const lower = compact.toLowerCase();\n    if (compact.includes(\'使用邮箱注册\')) return 100;\n    if (lower.includes(\'signupwithemail\')) return 95;\n    if (lower.includes(\'continuewithemail\')) return 90;\n    if (lower.includes(\'email\') && (lower.includes(\'sign\') || lower.includes(\'continue\') || lower.includes(\'use\') || lower.includes(\'with\'))) return 80;\n    if (lower === \'email\' || lower.includes(\'邮箱\')) return 70;\n    return 0;\n}\nconst candidates = Array.from(document.querySelectorAll(\'button, a, [role="button"]\'))\n    .filter((node) => isVisible(node) && !node.disabled && node.getAttribute(\'aria-disabled\') !== \'true\')\n    .map((node) => ({ node, score: scoreEntry(node), text: nodeText(node) }))\n    .filter((item) => item.score > 0)\n    .sort((a, b) => b.score - a.score);\nconst target = candidates[0]?.node || null;\nif (!target) {\n    return false;\n}\ntarget.click();\nreturn candidates[0].text || true;\n        ')
        if clicked:
            if log_callback:
                detail = f': {clicked}' if isinstance(clicked, str) else ''
                log_callback(f'[*] 已点击「使用邮箱注册」按钮{detail}')
            sleep_with_cancel(2, cancel_callback)
            return True
        if log_callback:
            current_url = _ns().page.url if _ns().page else 'none'
            log_callback(f'[Debug] 当前URL: {current_url}')
        sleep_with_cancel(1, cancel_callback)
    if log_callback:
        page_html = _ns().page.html[:500] if _ns().page else 'no page'
        log_callback(f'[Debug] 页面内容片段: {page_html}')
    raise Exception('未找到「使用邮箱注册」按钮')

def open_signup_page(log_callback=None, cancel_callback=None):
    pass
    raise_if_cancelled(cancel_callback)
    if _ns().browser is None:
        start_browser(log_callback=log_callback)
        if log_callback:
            log_callback(f'[*] 浏览器已启动 | 代理: {proxy_log_label()}')

    def _open_with_current_browser():
        pass
        try:
            _ns().page = _ns().browser.get_tab(0)
            _ns().page.get(SIGNUP_URL)
        except Exception as e:
            if log_callback:
                log_callback(f'[Debug] 打开URL异常: {e}')
            _ns().page = _ns().browser.new_tab(SIGNUP_URL)
        _ns().page.wait.doc_loaded()

    def _page_is_broken():
        return page_has_proxy_error(_ns().page)

    def _try_open_once():
        _open_with_current_browser()
        sleep_with_cancel(1.5, cancel_callback)
        if _page_is_broken():
            raise Exception('注册页代理/网络错误（无法加载真实页面）')
        if log_callback:
            log_callback(f'[*] 当前URL: {_ns().page.url} | 代理: {proxy_log_label()}')
        click_email_signup_button(log_callback=log_callback, cancel_callback=cancel_callback)
    pool_n = proxy_pool_size()
    max_tries = min(3, pool_n) if pool_n > 1 else 1
    last_exc = None
    for attempt in range(1, max_tries + 1):
        raise_if_cancelled(cancel_callback)
        try:
            _try_open_once()
            return
        except Exception as e:
            last_exc = e
            if log_callback:
                log_callback(f'[!] 打开注册页失败({attempt}/{max_tries}) 代理={proxy_log_label()}: {e}')
            if attempt >= max_tries:
                break
            if pool_n > 1 and _ns().browser_started_with_proxy:
                restart_browser(log_callback=log_callback, use_proxy=True)
                if log_callback:
                    log_callback(f'[*] 已切换代理: {proxy_log_label()}')
            else:
                break
    if _ns().browser_started_with_proxy or get_configured_proxy():
        if log_callback:
            log_callback(f'[!] 代理失败，回退直连重试: {last_exc}')
        restart_browser(log_callback=log_callback, use_proxy=False)
        _try_open_once()
        return
    raise last_exc if last_exc else Exception('打开注册页失败')

def has_profile_form(log_callback=None):
    refresh_active_page()
    try:
        return bool(_ns().page.run_js('\nconst givenInput = document.querySelector(\'input[data-testid="givenName"], input[name="givenName"], input[autocomplete="given-name"]\');\nconst familyInput = document.querySelector(\'input[data-testid="familyName"], input[name="familyName"], input[autocomplete="family-name"]\');\nconst passwordInput = document.querySelector(\'input[data-testid="password"], input[name="password"], input[type="password"]\');\nreturn !!(givenInput && familyInput && passwordInput);\n            '))
    except Exception:
        return False

def fill_email_and_submit(timeout=45, log_callback=None, cancel_callback=None):
    raise_if_cancelled(cancel_callback)
    (email, dev_token) = get_email_and_token()
    if not email or not dev_token:
        raise Exception('获取邮箱失败')
    if log_callback:
        log_callback(f'[*] 已创建邮箱: {email}')
    deadline = time.time() + timeout
    last_diag_time = 0
    last_reclick_time = 0
    last_snapshot = None
    while time.time() < deadline:
        raise_if_cancelled(cancel_callback)
        filled = _ns().page.run_js('\nconst email = arguments[0];\nfunction isVisible(node) {\n    if (!node) return false;\n    const style = window.getComputedStyle(node);\n    if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') return false;\n    const rect = node.getBoundingClientRect();\n    return rect.width > 0 && rect.height > 0;\n}\nfunction textOf(node) {\n    return [\n        node.innerText,\n        node.textContent,\n        node.getAttribute(\'aria-label\'),\n        node.getAttribute(\'title\'),\n        node.getAttribute(\'placeholder\'),\n        node.getAttribute(\'data-testid\'),\n        node.getAttribute(\'name\'),\n        node.getAttribute(\'id\'),\n        node.getAttribute(\'autocomplete\'),\n    ].filter(Boolean).join(\' \').replace(/\\s+/g, \' \').trim();\n}\nfunction describeInput(node) {\n    return [\n        `type=${node.getAttribute(\'type\') || \'\'}`,\n        `name=${node.getAttribute(\'name\') || \'\'}`,\n        `id=${node.getAttribute(\'id\') || \'\'}`,\n        `placeholder=${node.getAttribute(\'placeholder\') || \'\'}`,\n        `aria=${node.getAttribute(\'aria-label\') || \'\'}`,\n        `testid=${node.getAttribute(\'data-testid\') || \'\'}`,\n    ].join(\' \').replace(/\\s+/g, \' \').trim().slice(0, 160);\n}\nfunction describeAction(node) {\n    return textOf(node).slice(0, 120);\n}\nfunction emailCandidates() {\n    const direct = Array.from(document.querySelectorAll(\'input[data-testid="email"], input[name="email"], input[type="email"], input[autocomplete="email"], input[placeholder*="mail" i], input[aria-label*="mail" i]\'));\n    const all = Array.from(document.querySelectorAll(\'input, textarea\'));\n    for (const node of all) {\n        const type = (node.getAttribute(\'type\') || \'\').toLowerCase();\n        if ([\'hidden\', \'submit\', \'button\', \'checkbox\', \'radio\', \'file\', \'search\'].includes(type)) continue;\n        const meta = textOf(node).toLowerCase();\n        if (meta.includes(\'email\') || meta.includes(\'e-mail\') || meta.includes(\'mail\') || meta.includes(\'邮箱\') || meta.includes(\'电子邮件\')) {\n            direct.push(node);\n        }\n    }\n    return Array.from(new Set(direct));\n}\nconst visibleInputs = Array.from(document.querySelectorAll(\'input, textarea\'))\n    .filter((node) => isVisible(node) && !node.disabled && !node.readOnly)\n    .map(describeInput)\n    .slice(0, 8);\nconst visibleActions = Array.from(document.querySelectorAll(\'button, a, [role="button"]\'))\n    .filter((node) => isVisible(node) && !node.disabled && node.getAttribute(\'aria-disabled\') !== \'true\')\n    .map(describeAction)\n    .filter(Boolean)\n    .slice(0, 10);\nconst input = emailCandidates().find((node) => isVisible(node) && !node.disabled && !node.readOnly) || null;\nif (!input) {\n    return {\n        state: \'not-ready\',\n        url: location.href,\n        title: document.title,\n        inputs: visibleInputs,\n        buttons: visibleActions,\n    };\n}\ninput.focus(); input.click();\nconst valueProto = input instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;\nconst valueSetter = Object.getOwnPropertyDescriptor(valueProto, \'value\')?.set;\nconst tracker = input._valueTracker;\nif (tracker) tracker.setValue(\'\');\nif (valueSetter) valueSetter.call(input, email); else input.value = email;\ninput.dispatchEvent(new InputEvent(\'beforeinput\', { bubbles: true, data: email, inputType: \'insertText\' }));\ninput.dispatchEvent(new InputEvent(\'input\', { bubbles: true, data: email, inputType: \'insertText\' }));\ninput.dispatchEvent(new Event(\'change\', { bubbles: true }));\nconst inputType = (input.getAttribute(\'type\') || \'\').toLowerCase();\nconst isValid = inputType !== \'email\' || input.checkValidity();\nif ((input.value || \'\').trim() !== email || !isValid) {\n    return {\n        state: \'fill-failed\',\n        value: input.value || \'\',\n        valid: isValid,\n        input: describeInput(input),\n        url: location.href,\n    };\n}\ninput.blur();\nreturn {\n    state: \'filled\',\n    input: describeInput(input),\n    url: location.href,\n};\n            ', email)
        state = filled.get('state') if isinstance(filled, dict) else filled
        if isinstance(filled, dict):
            last_snapshot = filled
        if state == 'not-ready':
            now = time.time()
            if now - last_reclick_time >= 3:
                reclicked = _ns().page.run_js('\nfunction isVisible(node) {\n    if (!node) return false;\n    const style = window.getComputedStyle(node);\n    if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') return false;\n    const rect = node.getBoundingClientRect();\n    return rect.width > 0 && rect.height > 0;\n}\nfunction nodeText(node) {\n    return [\n        node.innerText,\n        node.textContent,\n        node.getAttribute(\'aria-label\'),\n        node.getAttribute(\'title\'),\n        node.getAttribute(\'href\'),\n    ].filter(Boolean).join(\' \').replace(/\\s+/g, \' \').trim();\n}\nfunction scoreEntry(node) {\n    const compact = nodeText(node).replace(/\\s+/g, \'\');\n    const lower = compact.toLowerCase();\n    if (compact.includes(\'使用邮箱注册\')) return 100;\n    if (lower.includes(\'signupwithemail\')) return 95;\n    if (lower.includes(\'continuewithemail\')) return 90;\n    if (lower.includes(\'email\') && (lower.includes(\'sign\') || lower.includes(\'continue\') || lower.includes(\'use\') || lower.includes(\'with\'))) return 80;\n    if (lower === \'email\' || lower.includes(\'邮箱\')) return 70;\n    return 0;\n}\nconst candidates = Array.from(document.querySelectorAll(\'button, a, [role="button"]\'))\n    .filter((node) => isVisible(node) && !node.disabled && node.getAttribute(\'aria-disabled\') !== \'true\')\n    .map((node) => ({ node, score: scoreEntry(node), text: nodeText(node) }))\n    .filter((item) => item.score > 0)\n    .sort((a, b) => b.score - a.score);\nif (!candidates.length) return false;\ncandidates[0].node.click();\nreturn candidates[0].text || true;\n                ')
                last_reclick_time = now
                if reclicked and log_callback:
                    detail = f': {reclicked}' if isinstance(reclicked, str) else ''
                    log_callback(f'[Debug] 邮箱输入框未出现，已再次触发邮箱注册入口{detail}')
            if log_callback and now - last_diag_time >= 5:
                last_diag_time = now
                inputs = ' | '.join((filled or {}).get('inputs', [])[:6]) if isinstance(filled, dict) else ''
                buttons = ' | '.join((filled or {}).get('buttons', [])[:8]) if isinstance(filled, dict) else ''
                url = (filled or {}).get('url', _ns().page.url if _ns().page else '') if isinstance(filled, dict) else _ns().page.url if _ns().page else ''
                log_callback(f"[Debug] 等待邮箱输入框: url={url}; inputs={inputs or 'none'}; buttons={buttons or 'none'}")
            sleep_with_cancel(0.5, cancel_callback)
            continue
        if state != 'filled':
            if log_callback:
                log_callback(f'[Debug] 邮箱输入框已出现，但写入失败: {filled}')
            sleep_with_cancel(0.5, cancel_callback)
            continue
        sleep_with_cancel(0.8, cancel_callback)
        clicked = _ns().page.run_js('\nfunction isVisible(node) {\n    if (!node) return false;\n    const style = window.getComputedStyle(node);\n    if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') return false;\n    const rect = node.getBoundingClientRect();\n    return rect.width > 0 && rect.height > 0;\n}\nfunction textOf(node) {\n    return [\n        node.innerText,\n        node.textContent,\n        node.getAttribute(\'aria-label\'),\n        node.getAttribute(\'title\'),\n        node.getAttribute(\'placeholder\'),\n        node.getAttribute(\'data-testid\'),\n        node.getAttribute(\'name\'),\n        node.getAttribute(\'id\'),\n        node.getAttribute(\'autocomplete\'),\n    ].filter(Boolean).join(\' \').replace(/\\s+/g, \' \').trim();\n}\nfunction emailCandidates() {\n    const direct = Array.from(document.querySelectorAll(\'input[data-testid="email"], input[name="email"], input[type="email"], input[autocomplete="email"], input[placeholder*="mail" i], input[aria-label*="mail" i]\'));\n    const all = Array.from(document.querySelectorAll(\'input, textarea\'));\n    for (const node of all) {\n        const type = (node.getAttribute(\'type\') || \'\').toLowerCase();\n        if ([\'hidden\', \'submit\', \'button\', \'checkbox\', \'radio\', \'file\', \'search\'].includes(type)) continue;\n        const meta = textOf(node).toLowerCase();\n        if (meta.includes(\'email\') || meta.includes(\'e-mail\') || meta.includes(\'mail\') || meta.includes(\'邮箱\') || meta.includes(\'电子邮件\')) {\n            direct.push(node);\n        }\n    }\n    return Array.from(new Set(direct));\n}\nconst input = emailCandidates().find((node) => isVisible(node) && !node.disabled && !node.readOnly) || null;\nif (!input || !(input.value || \'\').trim()) return false;\nconst inputType = (input.getAttribute(\'type\') || \'\').toLowerCase();\nif (inputType === \'email\' && !input.checkValidity()) return false;\nconst buttons = Array.from(document.querySelectorAll(\'button[type="submit"], button, [role="button"], input[type="submit"]\'))\n    .filter((node) => isVisible(node) && !node.disabled && node.getAttribute(\'aria-disabled\') !== \'true\');\nconst submitButton = buttons.find((node) => {\n    const text = textOf(node).replace(/\\s+/g, \'\');\n    const lower = text.toLowerCase();\n    return (\n        text === \'注册\' ||\n        text.includes(\'注册\') ||\n        text.includes(\'继续\') ||\n        text.includes(\'下一步\') ||\n        text.includes(\'确认\') ||\n        lower.includes(\'signup\') ||\n        lower.includes(\'sign up\') ||\n        lower.includes(\'continue\') ||\n        lower.includes(\'next\') ||\n        lower.includes(\'createaccount\') ||\n        lower.includes(\'submit\')\n    );\n});\nif (submitButton) {\n    submitButton.click();\n    return textOf(submitButton) || true;\n}\nconst form = input.closest(\'form\');\nif (form) {\n    if (form.requestSubmit) form.requestSubmit();\n    else form.dispatchEvent(new Event(\'submit\', { bubbles: true, cancelable: true }));\n    return \'form-submit\';\n}\ninput.focus();\ninput.dispatchEvent(new KeyboardEvent(\'keydown\', { key: \'Enter\', code: \'Enter\', bubbles: true, cancelable: true }));\ninput.dispatchEvent(new KeyboardEvent(\'keyup\', { key: \'Enter\', code: \'Enter\', bubbles: true, cancelable: true }));\nreturn \'enter\';\n            ')
        if clicked:
            if log_callback:
                detail = f' ({clicked})' if isinstance(clicked, str) else ''
                log_callback(f'[*] 已填写邮箱并提交: {email}{detail}')
            return (email, dev_token)
        sleep_with_cancel(0.5, cancel_callback)
    if last_snapshot:
        inputs = ' | '.join(last_snapshot.get('inputs', [])[:6])
        buttons = ' | '.join(last_snapshot.get('buttons', [])[:8])
        url = last_snapshot.get('url', _ns().page.url if _ns().page else '')
        raise Exception(f"未找到邮箱输入框或注册按钮，最后页面: url={url}; inputs={inputs or 'none'}; buttons={buttons or 'none'}")
    raise Exception('未找到邮箱输入框或注册按钮')

def fill_code_and_submit(email, dev_token, timeout=180, log_callback=None, cancel_callback=None):

    def _resend_code():
        _ns().page.run_js('\nconst nodes = Array.from(document.querySelectorAll(\'button, a, [role="button"]\'));\nconst target = nodes.find((node) => {\n  const t = (node.innerText || node.textContent || \'\').replace(/\\s+/g, \'\').toLowerCase();\n  return t.includes(\'重新发送\') || t.includes(\'resend\') || t.includes(\'再次发送\');\n});\nif (target && !target.disabled) { target.click(); return true; }\nreturn false;\n            ')
    code = get_oai_code(dev_token, email, log_callback=log_callback, cancel_callback=cancel_callback, resend_callback=_resend_code)
    if not code:
        raise Exception('获取验证码失败')
    clean_code = str(code).replace('-', '').strip()
    deadline = time.time() + timeout
    while time.time() < deadline:
        raise_if_cancelled(cancel_callback)
        filled = _ns().page.run_js('\nconst code = String(arguments[0] || \'\').trim();\nif (!code) return \'empty-code\';\n\nfunction isVisible(node) {\n    if (!node) return false;\n    const style = window.getComputedStyle(node);\n    if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') return false;\n    const rect = node.getBoundingClientRect();\n    return rect.width > 0 && rect.height > 0;\n}\n\nfunction setInputValue(input, value) {\n    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, \'value\')?.set;\n    const tracker = input._valueTracker;\n    if (tracker) tracker.setValue(\'\');\n    if (nativeSetter) nativeSetter.call(input, value);\n    else input.value = value;\n    input.dispatchEvent(new InputEvent(\'beforeinput\', { bubbles: true, data: value, inputType: \'insertText\' }));\n    input.dispatchEvent(new InputEvent(\'input\', { bubbles: true, data: value, inputType: \'insertText\' }));\n    input.dispatchEvent(new Event(\'change\', { bubbles: true }));\n}\n\nconst aggregate = Array.from(document.querySelectorAll(\n  \'input[data-input-otp="true"], input[name="code"], input[autocomplete="one-time-code"], input[inputmode="numeric"], input[inputmode="text"]\'\n)).find((node) => isVisible(node) && !node.disabled && !node.readOnly && Number(node.maxLength || 6) > 1);\n\nif (aggregate) {\n    aggregate.focus();\n    aggregate.click();\n    setInputValue(aggregate, code);\n    return String(aggregate.value || \'\').replace(/\\s+/g, \'\') ? \'filled-aggregate\' : \'aggregate-failed\';\n}\n\nconst otpBoxes = Array.from(document.querySelectorAll(\'input\')).filter((node) => {\n    if (!isVisible(node) || node.disabled || node.readOnly) return false;\n    const maxLength = Number(node.maxLength || 0);\n    const ac = String(node.autocomplete || \'\').toLowerCase();\n    return maxLength === 1 || ac === \'one-time-code\';\n});\n\nif (otpBoxes.length >= code.length) {\n    for (let i = 0; i < code.length; i += 1) {\n        const ch = code[i] || \'\';\n        const box = otpBoxes[i];\n        box.focus();\n        box.click();\n        setInputValue(box, ch);\n        box.dispatchEvent(new KeyboardEvent(\'keydown\', { bubbles: true, key: ch }));\n        box.dispatchEvent(new KeyboardEvent(\'keyup\', { bubbles: true, key: ch }));\n    }\n    const merged = otpBoxes.slice(0, code.length).map((x) => String(x.value || \'\').trim()).join(\'\');\n    return merged.length ? \'filled-boxes\' : \'boxes-failed\';\n}\n\nreturn \'not-ready\';\n            ', clean_code)
        if filled == 'not-ready':
            sleep_with_cancel(0.5, cancel_callback)
            continue
        if 'failed' in str(filled):
            if log_callback:
                log_callback(f'[Debug] 验证码填写失败: {filled}')
            sleep_with_cancel(0.5, cancel_callback)
            continue
        clicked = _ns().page.run_js('\nfunction isVisible(node) {\n    if (!node) return false;\n    const style = window.getComputedStyle(node);\n    if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') return false;\n    const rect = node.getBoundingClientRect();\n    return rect.width > 0 && rect.height > 0;\n}\n\nconst buttons = Array.from(document.querySelectorAll(\'button[type=\\"submit\\"], button\')).filter((node) => {\n    return isVisible(node) && !node.disabled && node.getAttribute(\'aria-disabled\') !== \'true\';\n});\n\nconst btn = buttons.find((node) => {\n    const t = (node.innerText || node.textContent || \'\').replace(/\\\\s+/g, \'\').toLowerCase();\n    return (\n        t.includes(\'确认邮箱\') ||\n        t.includes(\'继续\') ||\n        t.includes(\'下一步\') ||\n        t.includes(\'confirm\') ||\n        t.includes(\'continue\') ||\n        t.includes(\'next\')\n    );\n});\n\nif (!btn) return \'no-button\';\nbtn.focus();\nbtn.click();\nreturn \'clicked\';\n            ')
        if clicked == 'clicked' or clicked == 'no-button':
            if log_callback:
                log_callback(f'[*] 已填写验证码并提交: {code}')
            sleep_with_cancel(1.5, cancel_callback)
            return code
        sleep_with_cancel(0.5, cancel_callback)
    raise Exception('验证码已获取，但自动填写/提交失败')

def getTurnstileToken(log_callback=None, cancel_callback=None):
    pass
    if _ns().page is None:
        raise Exception('页面未就绪，无法执行 Turnstile')
    try:
        _ns().page.run_js("try { if (window.turnstile && typeof turnstile.reset === 'function') turnstile.reset(); } catch(e) {}")
    except Exception:
        pass
    for _ in range(0, 12):
        raise_if_cancelled(cancel_callback)
        try:
            token = _ns().page.run_js('\ntry {\n  const byInput = String((document.querySelector(\'input[name="cf-turnstile-response"]\') || {}).value || \'\').trim();\n  if (byInput) return byInput;\n  if (window.turnstile && typeof turnstile.getResponse === \'function\') {\n    return String(turnstile.getResponse() || \'\').trim();\n  }\n  return \'\';\n} catch(e) { return \'\'; }\n                ')
            token = str(token or '').strip()
            if len(token) >= 80:
                if log_callback:
                    log_callback(f'[*] Turnstile 已通过，token长度={len(token)}')
                return token
            challenge_input = _ns().page.ele('@name=cf-turnstile-response')
            if challenge_input:
                wrapper = challenge_input.parent()
                iframe = None
                try:
                    iframe = wrapper.shadow_root.ele('tag:iframe')
                except Exception:
                    iframe = None
                if iframe:
                    try:
                        iframe.run_js("\nwindow.dtp = 1;\nfunction getRandomInt(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }\nlet sx = getRandomInt(800, 1200);\nlet sy = getRandomInt(400, 700);\nObject.defineProperty(MouseEvent.prototype, 'screenX', { value: sx });\nObject.defineProperty(MouseEvent.prototype, 'screenY', { value: sy });\n                            ")
                    except Exception:
                        pass
                    try:
                        body_sr = iframe.ele('tag:body').shadow_root
                        btn = body_sr.ele('tag:input')
                        if btn:
                            btn.click()
                    except Exception:
                        pass
            else:
                _ns().page.run_js("\nconst nodes = Array.from(document.querySelectorAll('div,span,iframe')).filter((n) => {\n  const txt = (n.className || '') + ' ' + (n.id || '') + ' ' + (n.getAttribute?.('src') || '');\n  return String(txt).toLowerCase().includes('turnstile');\n});\nif (nodes.length && typeof nodes[0].click === 'function') nodes[0].click();\n                    ")
        except Exception:
            pass
        sleep_with_cancel(1, cancel_callback)
    raise Exception('Turnstile 获取 token 失败')

def build_profile():
    given_name_pool = ['Neo', 'Ethan', 'Liam', 'Noah', 'Lucas', 'Mason', 'Ryan', 'Leo', 'Owen', 'Aiden', 'Elio', 'Aron', 'Ivan', 'Nolan', 'Evan', 'Kai', 'Caleb', 'Adam', 'Ezra', 'Miles', 'Logan', 'Carter', 'Hunter', 'Jason', 'Brian', 'Dylan', 'Alex', 'Colin', 'Blake', 'Gavin', 'Henry', 'Julian', 'Kevin', 'Louis', 'Marcus', 'Nathan', 'Oscar', 'Peter', 'Quinn', 'Robin', 'Simon', 'Tristan', 'Victor', 'Wesley', 'Xavier', 'Yuri', 'Zane', 'Felix', 'Aaron', 'Damian']
    family_name_pool = ['Lin', 'Wang', 'Zhao', 'Liu', 'Chen', 'Zhang', 'Xu', 'Sun', 'Guo', 'He', 'Yang', 'Wu', 'Zhou', 'Tang', 'Qin', 'Shi', 'Fang', 'Peng', 'Cao', 'Deng', 'Fan', 'Fu', 'Gao', 'Han', 'Hu', 'Jiang', 'Kong', 'Lu', 'Ma', 'Nie', 'Pan', 'Qiao', 'Ren', 'Shao', 'Tian', 'Xie', 'Yan', 'Yao', 'Yu', 'Zeng', 'Bai', 'Duan', 'Hou', 'Jin', 'Kang', 'Luo', 'Mao', 'Song', 'Wei', 'Xiong']
    given_name = random.choice(given_name_pool)
    family_name = random.choice(family_name_pool)
    password = 'N' + secrets.token_hex(4) + '!a7#' + secrets.token_urlsafe(6)
    return (given_name, family_name, password)

def fill_profile_and_submit(timeout=120, log_callback=None, cancel_callback=None):
    (given_name, family_name, password) = build_profile()
    deadline = time.time() + timeout
    form_filled_once = False
    wait_cf_since = None
    last_cf_retry_at = 0.0
    while time.time() < deadline:
        raise_if_cancelled(cancel_callback)
        if not form_filled_once:
            filled = _ns().page.run_js('\nconst givenName = arguments[0];\nconst familyName = arguments[1];\nconst password = arguments[2];\n\nfunction isVisible(node) {\n    if (!node) return false;\n    const style = window.getComputedStyle(node);\n    if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') return false;\n    const rect = node.getBoundingClientRect();\n    return rect.width > 0 && rect.height > 0;\n}\n\nfunction pickInput(selector) {\n    return Array.from(document.querySelectorAll(selector)).find((node) => {\n        return isVisible(node) && !node.disabled && !node.readOnly;\n    }) || null;\n}\n\nfunction setInputValue(input, value) {\n    if (!input) return false;\n    input.focus();\n    input.click();\n    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, \'value\')?.set;\n    const tracker = input._valueTracker;\n    if (tracker) tracker.setValue(\'\');\n    if (nativeSetter) nativeSetter.call(input, value);\n    else input.value = value;\n    input.dispatchEvent(new InputEvent(\'beforeinput\', { bubbles: true, data: value, inputType: \'insertText\' }));\n    input.dispatchEvent(new InputEvent(\'input\', { bubbles: true, data: value, inputType: \'insertText\' }));\n    input.dispatchEvent(new Event(\'change\', { bubbles: true }));\n    input.blur();\n    return String(input.value || \'\').trim() === String(value || \'\').trim();\n}\n\nconst givenInput = pickInput(\'input[data-testid="givenName"], input[name="givenName"], input[autocomplete="given-name"], input[aria-label*="名"]\');\nconst familyInput = pickInput(\'input[data-testid="familyName"], input[name="familyName"], input[autocomplete="family-name"], input[aria-label*="姓"]\');\nconst passwordInput = pickInput(\'input[data-testid="password"], input[name="password"], input[type="password"], input[autocomplete="new-password"]\');\n\nif (!givenInput || !familyInput || !passwordInput) return \'not-ready\';\n\nconst ok1 = setInputValue(givenInput, givenName);\nconst ok2 = setInputValue(familyInput, familyName);\nconst ok3 = setInputValue(passwordInput, password);\n\nif (!ok1 || !ok2 || !ok3) return \'fill-failed\';\n\nconst buttons = Array.from(document.querySelectorAll(\'button[type="submit"], button, [role="button"], input[type="submit"]\')).filter((node) => {\n    return isVisible(node) && !node.disabled && node.getAttribute(\'aria-disabled\') !== \'true\';\n});\nconst submitBtn = buttons.find((node) => {\n    const t = (node.innerText || node.textContent || \'\').replace(/\\s+/g, \'\').toLowerCase();\n    return t.includes(\'完成注册\') || t.includes(\'创建账户\') || t.includes(\'signup\') || t.includes(\'createaccount\');\n});\n\n// 必须等待 Cloudflare 校验通过后再提交\nconst cfInput = document.querySelector(\'input[name="cf-turnstile-response"]\');\nconst cfPresent = !!cfInput\n  || !!document.querySelector(\'iframe[src*="turnstile"], div.cf-turnstile, [data-sitekey], script[src*="turnstile"]\');\nif (cfPresent) {\n    const token = String((cfInput && cfInput.value) || \'\').trim();\n    const solvedByToken = token.length >= 80;\n    if (!solvedByToken) return \'wait-cloudflare:\' + token.length;\n}\n\nif (submitBtn) {\n    return \'ready-to-submit\';\n}\nreturn \'filled-no-submit\';\n            ', given_name, family_name, password)
            if isinstance(filled, str) and filled.startswith('wait-cloudflare'):
                form_filled_once = True
                if log_callback:
                    token_len = filled.split(':', 1)[1] if ':' in filled else '0'
                    log_callback(f'[*] 资料已填写，等待 Cloudflare 人机验证通过... 当前token长度={token_len}')
                if token_len == '0':
                    pause_seconds = random.uniform(1, 3)
                    if log_callback:
                        log_callback(f'[*] Cloudflare token 为空，暂停 {pause_seconds:.1f}s 后继续检测')
                    sleep_with_cancel(pause_seconds, cancel_callback)
                now = time.time()
                if wait_cf_since is None:
                    wait_cf_since = now
                if now - wait_cf_since >= 6 and now - last_cf_retry_at >= 5:
                    if log_callback:
                        log_callback('[*] Cloudflare 验证卡住，开始二次复用 Turnstile...')
                    try:
                        token = getTurnstileToken(log_callback=log_callback, cancel_callback=cancel_callback)
                        if token:
                            synced = _ns().page.run_js('\nconst token = String(arguments[0] || \'\').trim();\nconst cfInput = document.querySelector(\'input[name="cf-turnstile-response"]\');\nif (!cfInput || !token) return false;\nconst nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, \'value\')?.set;\nif (nativeSetter) nativeSetter.call(cfInput, token);\nelse cfInput.value = token;\ncfInput.dispatchEvent(new Event(\'input\', { bubbles: true }));\ncfInput.dispatchEvent(new Event(\'change\', { bubbles: true }));\nreturn String(cfInput.value || \'\').trim().length;\n                                ', token)
                            if log_callback:
                                log_callback(f'[*] Turnstile 二次复用完成，回填长度={synced}')
                    except Exception as cf_exc:
                        if log_callback:
                            log_callback(f'[Debug] Turnstile 二次复用失败: {cf_exc}')
                    last_cf_retry_at = now
                sleep_with_cancel(0.8, cancel_callback)
                continue
            if filled in ('ready-to-submit', 'filled-no-submit'):
                form_filled_once = True
            elif filled == 'fill-failed' and log_callback:
                log_callback('[Debug] 资料输入失败，重试中...')
                sleep_with_cancel(0.5, cancel_callback)
                continue
            elif filled == 'not-ready':
                sleep_with_cancel(0.5, cancel_callback)
                continue
        submit_state = _ns().page.run_js('\nfunction isVisible(node) {\n    if (!node) return false;\n    const style = window.getComputedStyle(node);\n    if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') return false;\n    const rect = node.getBoundingClientRect();\n    return rect.width > 0 && rect.height > 0;\n}\n\nconst cfInput = document.querySelector(\'input[name="cf-turnstile-response"]\');\nconst cfPresent = !!cfInput\n  || !!document.querySelector(\'iframe[src*="turnstile"], div.cf-turnstile, [data-sitekey], script[src*="turnstile"]\');\nif (cfPresent) {\n    const token = String((cfInput && cfInput.value) || \'\').trim();\n    const solvedByToken = token.length >= 80;\n    if (!solvedByToken) return \'wait-cloudflare:\' + token.length;\n}\n\nfunction buttonText(node) {\n    return [\n        node.innerText,\n        node.textContent,\n        node.getAttribute(\'value\'),\n        node.getAttribute(\'aria-label\'),\n        node.getAttribute(\'title\'),\n    ].filter(Boolean).join(\' \').replace(/\\s+/g, \' \').trim();\n}\nconst buttons = Array.from(document.querySelectorAll(\'button[type="submit"], button, [role="button"], input[type="submit"]\')).filter((node) => {\n    return isVisible(node) && !node.disabled && node.getAttribute(\'aria-disabled\') !== \'true\';\n});\nconst submitBtn = buttons.find((node) => {\n    const t = buttonText(node).replace(/\\s+/g, \'\').toLowerCase();\n    return t.includes(\'完成注册\') || t.includes(\'创建账户\') || t.includes(\'signup\') || t.includes(\'createaccount\');\n});\nif (!submitBtn) {\n    const visibleTexts = buttons.map(buttonText).filter(Boolean).slice(0, 8).join(\' | \');\n    return \'no-submit-button:\' + visibleTexts;\n}\nsubmitBtn.focus();\nsubmitBtn.click();\nreturn \'submitted\';\n            ')
        if isinstance(submit_state, str) and submit_state.startswith('wait-cloudflare'):
            if log_callback:
                token_len = submit_state.split(':', 1)[1] if ':' in submit_state else '0'
                log_callback(f'[*] 等待 Cloudflare 人机验证通过后再提交... 当前token长度={token_len}')
            now = time.time()
            if wait_cf_since is None:
                wait_cf_since = now
            if now - wait_cf_since >= 6 and now - last_cf_retry_at >= 5:
                if log_callback:
                    log_callback('[*] 提交前仍卡住，自动再次复用 Turnstile...')
                try:
                    token = getTurnstileToken(log_callback=log_callback, cancel_callback=cancel_callback)
                    if token:
                        synced = _ns().page.run_js('\nconst token = String(arguments[0] || \'\').trim();\nconst cfInput = document.querySelector(\'input[name="cf-turnstile-response"]\');\nif (!cfInput || !token) return false;\nconst nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, \'value\')?.set;\nif (nativeSetter) nativeSetter.call(cfInput, token);\nelse cfInput.value = token;\ncfInput.dispatchEvent(new Event(\'input\', { bubbles: true }));\ncfInput.dispatchEvent(new Event(\'change\', { bubbles: true }));\nreturn String(cfInput.value || \'\').trim().length;\n                            ', token)
                        if log_callback:
                            log_callback(f'[*] Turnstile 二次复用完成，回填长度={synced}')
                except Exception as cf_exc:
                    if log_callback:
                        log_callback(f'[Debug] Turnstile 二次复用失败: {cf_exc}')
                last_cf_retry_at = now
            sleep_with_cancel(0.8, cancel_callback)
            continue
        if submit_state == 'submitted':
            if log_callback:
                log_callback(f'[*] 已填写注册资料并提交: {given_name} {family_name}')
            return {'given_name': given_name, 'family_name': family_name, 'password': password}
        wait_cf_since = None
        if isinstance(submit_state, str) and submit_state.startswith('no-submit-button') and log_callback:
            visible_buttons = submit_state.split(':', 1)[1] if ':' in submit_state else ''
            suffix = f' 可见按钮: {visible_buttons}' if visible_buttons else ''
            log_callback(f'[Debug] 未找到提交按钮，继续等待页面稳定...{suffix}')
        sleep_with_cancel(0.5, cancel_callback)
    raise Exception('最终注册页资料填写失败')

def wait_for_sso_cookie(timeout=120, log_callback=None, cancel_callback=None):
    deadline = time.time() + timeout
    last_seen_names = set()
    last_submit_retry = 0.0
    last_cf_retry_at = 0.0
    final_no_submit_state = ''
    final_no_submit_since = None
    final_no_submit_timeout = 25
    last_wait_exception_message = ''
    last_wait_exception_at = 0.0
    while time.time() < deadline:
        raise_if_cancelled(cancel_callback)
        try:
            refresh_active_page()
            if _ns().page is None:
                sleep_with_cancel(1, cancel_callback)
                continue
            now = time.time()
            if now - last_submit_retry >= 2.5:
                retried = _ns().page.run_js('\nfunction isVisible(node) {\n    if (!node) return false;\n    const style = window.getComputedStyle(node);\n    if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') return false;\n    const rect = node.getBoundingClientRect();\n    return rect.width > 0 && rect.height > 0;\n}\nconst titleHit = !!Array.from(document.querySelectorAll(\'h1,h2,div,span\')).find((el) => {\n    const t = (el.textContent || \'\').replace(/\\s+/g, \'\');\n    const lower = t.toLowerCase();\n    return t.includes(\'完成注册\') || lower.includes(\'completeyoursignup\') || lower.includes(\'completesignup\');\n});\nif (!titleHit) return \'not-final-page\';\n\nconst cfInput = document.querySelector(\'input[name="cf-turnstile-response"]\');\nconst cfPresent = !!cfInput\n  || !!document.querySelector(\'iframe[src*="turnstile"], div.cf-turnstile, [data-sitekey], script[src*="turnstile"]\');\nif (cfPresent) {\n    const token = String((cfInput && cfInput.value) || \'\').trim();\n    const solved = token.length >= 80;\n    if (!solved) return \'final-page-wait-cf:\' + token.length;\n}\n\nfunction buttonText(node) {\n    return [\n        node.innerText,\n        node.textContent,\n        node.getAttribute(\'value\'),\n        node.getAttribute(\'aria-label\'),\n        node.getAttribute(\'title\'),\n    ].filter(Boolean).join(\' \').replace(/\\s+/g, \' \').trim();\n}\nconst buttons = Array.from(document.querySelectorAll(\'button[type="submit"], button, [role="button"], input[type="submit"]\')).filter((node) => {\n    return isVisible(node) && !node.disabled && node.getAttribute(\'aria-disabled\') !== \'true\';\n});\nconst submitBtn = buttons.find((node) => {\n    const t = buttonText(node).replace(/\\s+/g, \'\').toLowerCase();\n    return t.includes(\'完成注册\') || t.includes(\'创建账户\') || t.includes(\'signup\') || t.includes(\'createaccount\');\n});\nif (!submitBtn) {\n    const visibleTexts = buttons.map(buttonText).filter(Boolean).slice(0, 8).join(\' | \');\n    return \'final-page-no-submit:\' + visibleTexts;\n}\nsubmitBtn.focus();\nsubmitBtn.click();\nreturn \'final-page-clicked-submit\';\n                    ')
                last_submit_retry = now
                if log_callback and (retried == 'final-page-clicked-submit' or (isinstance(retried, str) and retried.startswith('final-page-no-submit'))):
                    log_callback(f'[Debug] 最终页状态: {retried}')
                if isinstance(retried, str) and retried.startswith('final-page-no-submit'):
                    if retried != final_no_submit_state:
                        final_no_submit_state = retried
                        final_no_submit_since = now
                    elif final_no_submit_since and now - final_no_submit_since >= final_no_submit_timeout:
                        raise AccountRetryNeeded(f'最终注册页状态 {final_no_submit_timeout}s 未变化且未找到提交按钮，重试当前账号: {retried}')
                else:
                    final_no_submit_state = ''
                    final_no_submit_since = None
                if log_callback and isinstance(retried, str) and retried.startswith('final-page-wait-cf'):
                    token_len = retried.split(':', 1)[1] if ':' in retried else '0'
                    log_callback(f'[Debug] 最终页状态: final-page-wait-cf, token长度={token_len}')
                    if now - last_cf_retry_at >= 10:
                        if log_callback:
                            log_callback('[*] 最终页 Cloudflare 卡住，自动二次复用 Turnstile...')
                        try:
                            token = getTurnstileToken(log_callback=log_callback, cancel_callback=cancel_callback)
                            if token:
                                synced = _ns().page.run_js('\nconst token = String(arguments[0] || \'\').trim();\nconst cfInput = document.querySelector(\'input[name="cf-turnstile-response"]\');\nif (!cfInput || !token) return false;\nconst nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, \'value\')?.set;\nif (nativeSetter) nativeSetter.call(cfInput, token);\nelse cfInput.value = token;\ncfInput.dispatchEvent(new Event(\'input\', { bubbles: true }));\ncfInput.dispatchEvent(new Event(\'change\', { bubbles: true }));\nreturn String(cfInput.value || \'\').trim().length;\n                                    ', token)
                                if log_callback:
                                    log_callback(f'[*] 最终页 Turnstile 二次复用完成，回填长度={synced}')
                        except Exception as cf_exc:
                            if log_callback:
                                log_callback(f'[Debug] 最终页 Turnstile 二次复用失败: {cf_exc}')
                        last_cf_retry_at = now
            cookies = _ns().page.cookies(all_domains=True, all_info=True) or []
            for item in cookies:
                if isinstance(item, dict):
                    name = str(item.get('name', '')).strip()
                    value = str(item.get('value', '')).strip()
                else:
                    name = str(getattr(item, 'name', '')).strip()
                    value = str(getattr(item, 'value', '')).strip()
                if name:
                    last_seen_names.add(name)
                if name == 'sso' and value:
                    if log_callback:
                        log_callback('[*] 已获取到 sso cookie')
                    return value
        except PageDisconnectedError:
            refresh_active_page()
        except AccountRetryNeeded:
            raise
        except Exception as exc:
            if log_callback:
                now = time.time()
                message = f'{exc.__class__.__name__}: {exc}'
                if message != last_wait_exception_message or now - last_wait_exception_at >= 10:
                    log_callback(f'[Debug] 等待 sso cookie 时出现异常，将继续等待: {message}')
                    last_wait_exception_message = message
                    last_wait_exception_at = now
        sleep_with_cancel(1, cancel_callback)
    raise Exception(f'等待超时：未获取到 sso cookie。已看到 cookies: {sorted(last_seen_names)}')
