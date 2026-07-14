#!/usr/bin/env python3
from pathlib import Path

script = Path(__file__).resolve().with_name("apply_final_flow_fixes.py")
text = script.read_text(encoding="utf-8")

old_import = '''remote_tests = r\'''import unittest
from unittest.mock import patch

import grok_register_ttk as app
'''
new_import = '''remote_tests = r\'''import sys
import types
import unittest
from unittest.mock import patch

# Keep this unit test independent from optional browser/network dependencies.
drission = types.ModuleType("DrissionPage")
drission.Chromium = type("Chromium", (), {})
drission.ChromiumOptions = type("ChromiumOptions", (), {})
drission_errors = types.ModuleType("DrissionPage.errors")
drission_errors.PageDisconnectedError = type("PageDisconnectedError", (Exception,), {})
curl_cffi = types.ModuleType("curl_cffi")
curl_cffi.requests = types.SimpleNamespace()
sys.modules.setdefault("DrissionPage", drission)
sys.modules.setdefault("DrissionPage.errors", drission_errors)
sys.modules.setdefault("curl_cffi", curl_cffi)

import grok_register_ttk as app
'''
if old_import not in text:
    if new_import not in text:
        raise RuntimeError("remote test import block not found")
else:
    text = text.replace(old_import, new_import, 1)

old_cleanup = '        interval_cleanups = [event for event in fake.events if isinstance(event, tuple) and "已成功" in event[1]]\n'
new_cleanup = '        interval_cleanups = [\n            event for event in fake.events\n            if isinstance(event, tuple)\n            and len(event) > 1\n            and isinstance(event[1], str)\n            and "已成功" in event[1]\n        ]\n'
if old_cleanup not in text:
    if new_cleanup not in text:
        raise RuntimeError("cleanup test expression not found")
else:
    text = text.replace(old_cleanup, new_cleanup, 1)

script.write_text(text, encoding="utf-8")
print("final flow test generation repaired")
