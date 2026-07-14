#!/usr/bin/env python3
import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "grok_register_ttk.py"
CONFIG_PATH = ROOT / "config.example.json"
README_PATH = ROOT / "README.md"
GITIGNORE_PATH = ROOT / ".gitignore"


def ensure_contains(text, needle):
    if needle not in text:
        raise RuntimeError("missing expected marker: %s" % needle)


def replace_once(text, old, new):
    if old not in text:
        raise RuntimeError("anchor not found for replacement:\n%s" % old[:240])
    return text.replace(old, new, 1)


app = APP_PATH.read_text(encoding="utf-8-sig")

config_block_old = '''    "grok2api_auto_add_remote": False,
    "grok2api_remote_base": "",
    "grok2api_remote_app_key": "",
}'''
config_block_new = '''    "grok2api_auto_add_remote": False,
    "grok2api_remote_base": "",
    "grok2api_remote_app_key": "",
    "api_reverse_tools": "",
    "cpa_export_enabled": False,
    "cpa_auth_dir": "./cpa_auths",
    "cpa_copy_to_hotload": False,
    "cpa_hotload_dir": "",
    "cpa_base_url": "https://cli-chat-proxy.grok.com/v1",
    "cpa_proxy": "",
    "cpa_headless": False,
    "cpa_force_standalone": True,
    "cpa_mint_timeout_sec": 300,
    "cpa_mint_cookie_inject": True,
}'''
if '"cpa_export_enabled": False' not in app:
    app = replace_once(app, config_block_old, config_block_new)

helper_block = '''


def maybe_export_cpa_xai_after_success(email, password, sso="", log_callback=None, cancel_callback=None):
    if not bool(config.get("cpa_export_enabled", False)):
        return {"ok": False, "skipped": True, "reason": "disabled"}
    logger = log_callback or (lambda message: None)
    try:
        from cpa_export import export_cpa_xai_for_account
    except Exception as exc:
        logger(f"[!] CPA 模块导入失败，已跳过 OIDC 导出: {exc}")
        return {"ok": False, "error": str(exc)}
    current_page = None
    try:
        current_page = page
    except Exception:
        current_page = None
    try:
        result = export_cpa_xai_for_account(
            email=email,
            password=password,
            page=current_page,
            sso=sso,
            config=config,
            log_callback=logger,
            cancel_callback=cancel_callback,
        )
    except Exception as exc:
        logger(f"[!] CPA OIDC 导出失败，账号已保留: {exc}")
        return {"ok": False, "error": str(exc)}
    if result.get("ok"):
        exported_path = result.get("hotload_path") or result.get("path") or ""
        suffix = f": {exported_path}" if exported_path else ""
        logger(f"[+] CPA OIDC 导出成功{suffix}")
    elif not result.get("skipped"):
        logger(f"[!] CPA OIDC 导出失败，账号已保留: {result.get('error') or result}")
    return result
'''
if 'def maybe_export_cpa_xai_after_success(' not in app:
    app = replace_once(app, '\n\nclass GrokRegisterGUI:\n', helper_block + '\n\nclass GrokRegisterGUI:\n')

gui_fields_anchor = '''        add_label(11, 0, "grok2api 远端 app_key:")
        self.grok2api_remote_key_var = tk.StringVar(value=str(config.get("grok2api_remote_app_key", "")))
        self.grok2api_remote_key_entry = tk_entry(config_frame, textvariable=self.grok2api_remote_key_var, width=72)
        add_field(self.grok2api_remote_key_entry, 11, 1, columnspan=3)

        btn_frame = tk.Frame(main_frame, bg=UI_BG)'''
gui_fields_insert = '''        add_label(11, 0, "grok2api 远端 app_key:")
        self.grok2api_remote_key_var = tk.StringVar(value=str(config.get("grok2api_remote_app_key", "")))
        self.grok2api_remote_key_entry = tk_entry(config_frame, textvariable=self.grok2api_remote_key_var, width=72)
        add_field(self.grok2api_remote_key_entry, 11, 1, columnspan=3)

        add_label(12, 0, "OIDC / CPA:")
        self.cpa_export_var = tk.BooleanVar(value=bool(config.get("cpa_export_enabled", False)))
        self.cpa_export_check = tk_checkbutton(config_frame, text="注册成功后导出 CPA xAI OIDC", variable=self.cpa_export_var)
        add_field(self.cpa_export_check, 12, 1, sticky=tk.W)

        add_label(12, 2, "CPA 输出目录:")
        self.cpa_auth_dir_var = tk.StringVar(value=str(config.get("cpa_auth_dir", "./cpa_auths")))
        self.cpa_auth_dir_entry = tk_entry(config_frame, textvariable=self.cpa_auth_dir_var, width=34)
        add_field(self.cpa_auth_dir_entry, 12, 3)

        btn_frame = tk.Frame(main_frame, bg=UI_BG)'''
if 'self.cpa_export_var = tk.BooleanVar' not in app:
    app = replace_once(app, gui_fields_anchor, gui_fields_insert)

start_config_anchor = '''        config["grok2api_auto_add_remote"] = bool(self.grok2api_remote_auto_var.get())
        config["grok2api_remote_base"] = self.grok2api_remote_base_var.get().strip()
        config["grok2api_remote_app_key"] = self.grok2api_remote_key_var.get().strip()
        raw_paths = [x.strip() for x in self.cloudflare_paths_var.get().split(",") if x.strip()]'''
start_config_insert = '''        config["grok2api_auto_add_remote"] = bool(self.grok2api_remote_auto_var.get())
        config["grok2api_remote_base"] = self.grok2api_remote_base_var.get().strip()
        config["grok2api_remote_app_key"] = self.grok2api_remote_key_var.get().strip()
        config["cpa_export_enabled"] = bool(self.cpa_export_var.get())
        config["cpa_auth_dir"] = self.cpa_auth_dir_var.get().strip() or "./cpa_auths"
        raw_paths = [x.strip() for x in self.cloudflare_paths_var.get().split(",") if x.strip()]'''
if 'config["cpa_export_enabled"] = bool(self.cpa_export_var.get())' not in app:
    app = replace_once(app, start_config_anchor, start_config_insert)

gui_success_anchor = '                    add_token_to_grok2api_pools(sso, email=email, log_callback=self.log)\n                    self.success_count += 1'
gui_success_insert = '''                    add_token_to_grok2api_pools(sso, email=email, log_callback=self.log)
                    maybe_export_cpa_xai_after_success(
                        email=email,
                        password=profile.get("password", ""),
                        sso=sso,
                        log_callback=self.log,
                        cancel_callback=self.should_stop,
                    )
                    self.success_count += 1'''
if 'maybe_export_cpa_xai_after_success(' not in app.split('class CliStopController', 1)[0]:
    app = replace_once(app, gui_success_anchor, gui_success_insert)

cli_success_anchor = '                add_token_to_grok2api_pools(sso, email=email, log_callback=cli_log)\n                success_count += 1'
cli_success_insert = '''                add_token_to_grok2api_pools(sso, email=email, log_callback=cli_log)
                maybe_export_cpa_xai_after_success(
                    email=email,
                    password=profile.get("password", ""),
                    sso=sso,
                    log_callback=cli_log,
                    cancel_callback=controller.should_stop,
                )
                success_count += 1'''
cli_part = app.split('def main_cli():', 1)[0]
if 'maybe_export_cpa_xai_after_success(' not in cli_part.split('def run_registration_cli', 1)[-1]:
    app = replace_once(app, cli_success_anchor, cli_success_insert)

ast.parse(app)
APP_PATH.write_text(app, encoding="utf-8-sig")

config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
if "cpa_export_enabled" not in config:
    new_config = {}
    for key, value in config.items():
        new_config[key] = value
        if key == "grok2api_remote_app_key":
            new_config["api_reverse_tools"] = ""
            new_config["cpa_export_enabled"] = False
            new_config["cpa_auth_dir"] = "./cpa_auths"
            new_config["cpa_copy_to_hotload"] = False
            new_config["cpa_hotload_dir"] = ""
            new_config["cpa_base_url"] = "https://cli-chat-proxy.grok.com/v1"
            new_config["cpa_proxy"] = ""
            new_config["cpa_headless"] = False
            new_config["cpa_force_standalone"] = True
            new_config["cpa_mint_timeout_sec"] = 300
            new_config["cpa_mint_cookie_inject"] = True
    config = new_config
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

gitignore = GITIGNORE_PATH.read_text(encoding="utf-8")
for line in ("cpa_auths/", "xai-*.json", "cpa_auth_failed.txt"):
    if line not in gitignore:
        if not gitignore.endswith("\n"):
            gitignore += "\n"
        gitignore += line + "\n"
GITIGNORE_PATH.write_text(gitignore, encoding="utf-8")

readme = README_PATH.read_text(encoding="utf-8")
feature_old = "- 支持将 SSO token 写入 grok2api 本地或远端池。"
feature_new = "- 支持将 SSO token 写入 grok2api 本地或远端池。\n- 支持注册成功后可选导出 CLIProxyAPI 使用的 CPA xAI OAuth 凭证。"
if "CPA xAI OAuth 凭证" not in readme:
    readme = replace_once(readme, feature_old, feature_new)

table_old = "| `grok2api_remote_app_key` | 远端 grok2api app key |"
table_new = '''| `grok2api_remote_app_key` | 远端 grok2api app key |
| `cpa_export_enabled` | 是否在 SSO 成功后额外导出 CPA xAI OIDC 凭证 |
| `cpa_auth_dir` | 本地 CPA 导出目录，生成 `xai-*.json` |
| `cpa_copy_to_hotload` | 是否额外复制到 CLIProxyAPI 的 auth-dir |
| `cpa_hotload_dir` | CLIProxyAPI auth-dir 路径 |
| `cpa_proxy` | CPA/OIDC 专用代理；留空则回退到 `proxy` |
| `cpa_headless` | CPA/OIDC 浏览器是否无头，默认建议 `false` |'''
if "| `cpa_export_enabled` |" not in readme:
    readme = replace_once(readme, table_old, table_new)

section_anchor = "`config.json` 包含个人配置和密钥，不要提交到 Git。\n"
section_block = '''`config.json` 包含个人配置和密钥，不要提交到 Git。

### CPA / xAI OIDC 导出（可选）

当 `cpa_export_enabled=true` 时，程序会在**账号已经注册成功、SSO 已保存**之后，额外发起一次 xAI Device Authorization，自动批准授权并导出 `xai-*.json`。

这条线路是附加功能，不会替代原有的 SSO 保存流程。即使 OIDC 导出失败，原账号与 SSO 结果仍会保留。

推荐最小配置：

```json
{
  "cpa_export_enabled": true,
  "cpa_auth_dir": "./cpa_auths",
  "cpa_base_url": "https://cli-chat-proxy.grok.com/v1",
  "cpa_proxy": "",
  "cpa_headless": false
}
```

如需让 CLIProxyAPI 自动热加载，可额外填写：

```json
{
  "cpa_copy_to_hotload": true,
  "cpa_hotload_dir": "/path/to/cli-proxy-api/auth-dir"
}
```
'''
if "### CPA / xAI OIDC 导出（可选）" not in readme:
    readme = replace_once(readme, section_anchor, section_block)

output_old = "- `accounts_*.txt`：成功账号、密码和 SSO token。\n- `mail_credentials.txt`：临时邮箱凭证。"
output_new = "- `accounts_*.txt`：成功账号、密码和 SSO token。\n- `mail_credentials.txt`：临时邮箱凭证。\n- `cpa_auths/xai-*.json`：可选导出的 CPA xAI OAuth 凭证。\n- `cpa_auths/cpa_auth_failed.txt`：OIDC 导出失败记录。"
if "cpa_auths/xai-*.json" not in readme:
    readme = replace_once(readme, output_old, output_new)

README_PATH.write_text(readme, encoding="utf-8")

for path in (
    APP_PATH,
    ROOT / "cpa_export.py",
    ROOT / "cpa_xai" / "__init__.py",
    ROOT / "cpa_xai" / "proxyutil.py",
    ROOT / "cpa_xai" / "oauth_device.py",
    ROOT / "cpa_xai" / "schema.py",
    ROOT / "cpa_xai" / "writer.py",
    ROOT / "cpa_xai" / "browser_confirm.py",
    ROOT / "cpa_xai" / "mint.py",
):
    source = path.read_text(encoding="utf-8-sig" if path == APP_PATH else "utf-8")
    ast.parse(source)

ensure_contains(APP_PATH.read_text(encoding="utf-8-sig"), 'def maybe_export_cpa_xai_after_success(')
ensure_contains(README_PATH.read_text(encoding="utf-8"), "### CPA / xAI OIDC 导出（可选）")
ensure_contains(CONFIG_PATH.read_text(encoding="utf-8"), '"cpa_export_enabled": false')
print("CPA/OIDC upgrade applied successfully.")
