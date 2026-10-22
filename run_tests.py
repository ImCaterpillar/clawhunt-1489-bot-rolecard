# -*- coding: utf-8 -*-
"""角色卡主流程验证 —— 对应验收标准「提交角色卡 schema、示例与必填字段校验」

零第三方依赖。打印每条验收标准的实测结果。
"""
import json
import os
import sys

# 控制台强制 UTF-8（Windows 默认 GBK 会导致 emoji 报错）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import check_file, validate, apply_defaults, load  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "schema", "bot_rolecard.schema.json")

PASS, FAIL = [], []
OK = "\u2705"
NO = "\u274c"


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    mark = OK if cond else NO
    line = "  " + mark + " " + name
    if detail:
        line += " -- " + detail
    print(line)


print("=" * 78)
print("Bot Role Card -- acceptance verification")
print("=" * 78)
print("Acceptance: role card schema, examples, required-field validation\n")

# 1. schema 有效且可加载
schema = load(SCHEMA)
check("1. schema loadable, draft-07",
      schema.get("$schema", "").endswith("draft-07/schema#"),
      "title=" + str(schema.get("title")))
check("2. schema declares 8 required fields",
      len(schema.get("required", [])) == 8,
      str(schema.get("required")))

# 2. 合规示例通过（断言 3、4）
for idx, fn in enumerate(("rolecard_hr_onboarding.json",
                          "rolecard_customer_quote.json"), start=3):
    p = os.path.join(HERE, "examples", fn)
    errs, card = check_file(p, SCHEMA)
    check(str(idx) + ". valid example passes (" + fn + ")", not errs,
          "bot_id=" + str(card.get("bot_id")) if not errs else str(errs[:2]))

# 3. default 填充生效
card = load(os.path.join(HERE, "examples", "rolecard_hr_onboarding.json"))
filled = apply_defaults(card, schema)
check("5. defaults applied (escalation)",
      filled["role"].get("escalation") == "human_review",
      "escalation=" + str(filled["role"].get("escalation")))

# 4. 必填字段校验：逐个删除，必须全部报错
base = load(os.path.join(HERE, "examples", "rolecard_hr_onboarding.json"))
missed = []
for req in schema["required"]:
    broken = {k: v for k, v in base.items() if k != req}
    errs = validate(broken, schema)
    if not any(req in e for e in errs):
        missed.append(req)
check("6. each required field caught when removed", not missed,
      ("missed: " + str(missed)) if missed else "8/8 caught")

# 5. 坏样例被拒
errs_bad = validate(load(os.path.join(HERE, "examples",
                                      "rolecard_invalid.json")), schema)
check("7. invalid example rejected (>=5 errors)", len(errs_bad) >= 5,
      str(len(errs_bad)) + " errors")

# 6. 额外字段被拒
extra = dict(base)
extra["unknown_key"] = 1
check("8. extra field rejected",
      any("unknown_key" in e for e in validate(extra, schema)))

# 7. 枚举校验
enum_bad = json.loads(json.dumps(base))
enum_bad["domain"] = "nope"
check("9. domain enum enforced",
      any("domain" in e for e in validate(enum_bad, schema)))

# 8. 工具枚举（未知工具必须被拒）
tb = json.loads(json.dumps(base))
tb["tool_permissions"] = [{"tool": "magic_tool", "mode": "write"}]
check("10. unknown tool rejected (least privilege)",
      any("magic_tool" in e or "tool" in e for e in validate(tb, schema)))

# 9. 交付完整性：验证记录存在且非空（买家要求"验证记录"交付物）
vr_path = os.path.join(HERE, "docs", "验证记录.md")
vr_ok = os.path.isfile(vr_path) and os.path.getsize(vr_path) > 500
check("11. verification record exists", vr_ok,
      str(os.path.getsize(vr_path)) + " bytes" if vr_ok else "missing")

# 10. 交付齐套：所有应交付文件真实存在（无死引用）
refs = ["schema/bot_rolecard.schema.json", "validate.py", "run_tests.py",
        "examples/rolecard_hr_onboarding.json",
        "examples/rolecard_customer_quote.json",
        "examples/rolecard_invalid.json",
        "README.md", "SETUP.md",
        "docs/验收对照.md", "docs/实现说明.md", "docs/验证记录.md"]
broken_refs = [rf for rf in refs if not os.path.isfile(
    os.path.join(HERE, rf.replace("/", os.sep)))]
check("12. delivery set complete (11 files)", not broken_refs,
      "broken=" + str(broken_refs) if broken_refs else str(len(refs)) + " files")

print()
print("=" * 78)
print("Result: PASS " + str(len(PASS)) + "   FAIL " + str(len(FAIL)))
print("=" * 78)
if FAIL:
    print("Failed: " + ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
