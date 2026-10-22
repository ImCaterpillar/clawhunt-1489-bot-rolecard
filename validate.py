# -*- coding: utf-8 -*-
"""角色卡校验器 —— 零第三方依赖，实现 JSON Schema draft-07 的必要子集。

支持的关键字：type / required / properties / additionalProperties /
items / enum / pattern / minLength / maxLength / minItems / maxItems /
minimum / maximum / default（default 仅用于填充，不参与校验）。
"""
import json
import re
import sys

# Windows 控制台默认 GBK：不重配编码时，中文/emoji 输出会 UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class ValidationError(Exception):
    pass


def _type_ok(value, t):
    if t == "object":
        return isinstance(value, dict)
    if t == "array":
        return isinstance(value, list)
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "null":
        return value is None
    return True


def validate(instance, schema, path="$"):
    """返回错误列表；空列表表示通过。"""
    errors = []

    if "type" in schema and not _type_ok(instance, schema["type"]):
        errors.append(f"{path}: 期望类型 {schema['type']}，实为 "
                      f"{type(instance).__name__}")
        return errors          # 类型不对，后续检查无意义

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: 值 {instance!r} 不在允许集合 {schema['enum']}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: 长度 {len(instance)} < 最小 "
                          f"{schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: 长度 {len(instance)} > 最大 "
                          f"{schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: 值 {instance!r} 不匹配模式 "
                          f"{schema['pattern']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} < {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: {instance} > {schema['maximum']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: 元素数 {len(instance)} < {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: 元素数 {len(instance)} > {schema['maxItems']}")
        if "items" in schema:
            for i, item in enumerate(instance):
                errors += validate(item, schema["items"], f"{path}[{i}]")

    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: 缺少必填字段 '{req}'")
        props = schema.get("properties", {})
        for key, val in instance.items():
            if key in props:
                errors += validate(val, props[key], f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: 不允许的额外字段 '{key}'")
        for key, sub in props.items():
            if key not in instance and "default" in sub:
                pass              # default 由 apply_defaults 处理
    return errors


def apply_defaults(instance, schema):
    """按 schema 的 default 填充缺失字段（返回新对象，不修改入参）。"""
    if not isinstance(instance, dict):
        return instance
    out = dict(instance)
    for key, sub in (schema.get("properties") or {}).items():
        if key not in out and "default" in sub:
            out[key] = sub["default"]
        elif key in out and sub.get("type") == "object":
            out[key] = apply_defaults(out[key], sub)
        elif key in out and sub.get("type") == "array" and "items" in sub:
            out[key] = [apply_defaults(i, sub["items"]) for i in out[key]]
    return out


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_file(card_path, schema_path):
    schema = load(schema_path)
    card = load(card_path)
    card = apply_defaults(card, schema)
    errs = validate(card, schema)
    return errs, card


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python validate.py <card.json> <schema.json>")
        sys.exit(2)
    errs, card = check_file(sys.argv[1], sys.argv[2])
    name = card.get("bot_id", "?")
    if errs:
        print(f"❌ {name}: {len(errs)} 个错误")
        for e in errs:
            print(f"   - {e}")
        sys.exit(1)
    print(f"✅ {name}: 通过")
