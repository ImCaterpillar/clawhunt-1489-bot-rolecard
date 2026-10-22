# 环境与运行说明

## 环境要求

- **Python 3.8 或更高**
- **无需安装任何第三方依赖**（实现只用标准库）

验证环境：

```bash
python --version          # 应 >= 3.8
```

## 运行

### 1. 验收验证（推荐先跑这个）

```bash
python run_tests.py
```

预期输出：`Result: PASS 12   FAIL 0`，退出码 0。

每项断言直接对应验收标准：

| # | 断言 | 对应验收要求 |
|---|---|---|
| 1-2 | schema 加载 + 8 必填字段声明 | 角色卡 **schema** |
| 3-4 | 两份合规示例通过 | **示例** |
| 5 | default 填充生效 | schema 可用性 |
| **6** | **8 个必填字段逐个删除均被捕获** | **必填字段校验** |
| 7 | 非法样例被拒（8 个错误） | 校验器的拒绝能力 |
| 8 | 额外字段被拒 | additionalProperties |
| 9 | domain 枚举校验 | 枚举约束 |
| 10 | 未知工具被拒 | 最小权限原则 |
| 11 | 验证记录存在且非空 | 交付要求 **验证记录** |
| 12 | 交付齐套（11 文件无死引用） | 交付完整性 |

### 2. 单独校验一个角色卡

```bash
python validate.py <card.json> schema/bot_rolecard.schema.json
```

- 通过 → 打印 `✅ <bot_id>: 通过`，退出码 0
- 失败 → 打印每个错误与路径，退出码 1

### 3. 在自己的代码里调用

```python
import sys
sys.path.insert(0, ".")
from validate import check_file, validate, apply_defaults, load

schema = load("schema/bot_rolecard.schema.json")
errs, card = check_file("examples/rolecard_hr_onboarding.json",
                        "schema/bot_rolecard.schema.json")
if errs:
    for e in errs:
        print("ERROR:", e)
else:
    print("OK:", card["bot_id"])
```

## 退出码

| 码 | 含义 |
|---|---|
| 0 | 全部通过 |
| 1 | 有校验失败 |
| 2 | 参数用法错误 |

## 故障排查

**Q: 报 `UnicodeEncodeError: 'gbk' codec`**
A: Windows 控制台默认 GBK。`run_tests.py` 已内置
`sys.stdout.reconfigure(encoding="utf-8")`；若你自己写脚本调用，
需要加上同样的两行。

**Q: 报 `ModuleNotFoundError: No module named 'validate'`**
A: 需在交付物根目录运行（`validate.py` 与 `run_tests.py` 同级）。

## 可移植性

整个交付物不依赖任何第三方包、不依赖网络、不依赖平台。
复制到任意装有 Python 3.8+ 的机器即可运行。
