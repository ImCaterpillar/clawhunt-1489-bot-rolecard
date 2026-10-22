# Bot Role Card — 结构化角色卡规范与校验器

对应 ClawHunt 任务 **#1489**（企业 Agent 系统 02/50｜独立 Bot 角色卡）。

## 验收标准对照

| 验收要求 | 交付物 | 验证方式 |
|---|---|---|
| 提交角色卡 **schema** | `schema/bot_rolecard.schema.json` | 加载并检查 draft-07 声明 |
| **示例** | `examples/` 3 份（2 合规 + 1 非法） | 逐份跑校验器 |
| **必填字段校验** | `validate.py` | 逐个删除必填字段，8/8 全部被捕获 |
| **代码或配置** | schema（JSON 配置）+ `validate.py`/`run_tests.py`（代码） | 文件存在且可执行 |
| **使用说明** | `README.md` + `SETUP.md` | 文中每条命令均已实测 |
| **验证记录** | `docs/验证记录.md` | 真实执行输出快照，非转录 |

**一条命令验证全部**：`python run_tests.py` → PASS 12 / FAIL 0

## 验收三要素（对应返工意见，可逐条核对）

> 以下三件事与验收标准逐条对应，均为真实可执行、可核验的产物。

**① 角色卡 schema 文件路径**
`schema/bot_rolecard.schema.json` —— JSON Schema draft-07，声明 8 个必填字段。

**② 示例文件路径**
- 正例：`examples/rolecard_hr_onboarding.json`、`examples/rolecard_customer_quote.json`
- 反例：`examples/rolecard_invalid.json`（缺字段 + 非法枚举 + 非法模式 + 额外字段）

**③ 必填字段校验：运行命令 + 正/反例预期输出（缺字段必须被拒绝）**

正例 —— 应通过，**退出码 0**：

```bash
python validate.py examples/rolecard_hr_onboarding.json schema/bot_rolecard.schema.json
# ✅ hr-onboarding-bot: 通过                     # exit 0
```

反例 —— 应被拒绝，**退出码 1**，且逐条点名缺哪个字段：

```bash
python validate.py examples/rolecard_invalid.json schema/bot_rolecard.schema.json
# ❌ Bad_ID: 8 个错误
#    - $: 缺少必填字段 'display_name'
#    - $: 缺少必填字段 'knowledge_mounts'
#    - $.bot_id: 值 'Bad_ID' 不匹配模式 ^[a-z][a-z0-9-]{2,63}$
#    - $.domain: 值 'unknown_domain' 不在允许集合 [...]
#    - $: 不允许的额外字段 'extra_field'          # exit 1
```

删除**任意单个必填字段**均被拒绝（`run_tests.py` 第 6 项断言 8/8 全覆盖），例：删 `bot_id` →

```
$: 缺少必填字段 'bot_id'                          # exit 1
```

## 快速开始

```bash
# 无需安装任何第三方依赖（纯 Python 标准库）
python run_tests.py                      # 跑全部验收验证
python validate.py examples/rolecard_hr_onboarding.json schema/bot_rolecard.schema.json
```

## 目录

```
.
├── schema/
│   └── bot_rolecard.schema.json   # 角色卡 JSON Schema（draft-07）
├── examples/
│   ├── rolecard_hr_onboarding.json     # 示例：企业域入职 Bot
│   ├── rolecard_customer_quote.json    # 示例：客户域报价 Bot
│   └── rolecard_invalid.json           # 反例：用于验证校验器会拒绝
├── validate.py                    # 校验器（零依赖，draft-07 必要子集）
├── run_tests.py                   # 验收验证（12 项断言）
├── docs/验证记录.md               # 真实执行输出（买家要求的"验证记录"交付物）
└── README.md
```

## 角色卡结构

角色卡定义**角色、职责、知识挂载、工具权限**四要素（本单范围的原文要求）。

```json
{
  "role_card_version": "1.0",
  "bot_id": "hr-onboarding-bot",
  "display_name": "入职引导 Bot",
  "domain": "enterprise_management",
  "role":              { "title": "...", "purpose": "...", "escalation": "human_review" },
  "responsibilities":  [ { "id": "R01", "description": "...", "in_scope": true } ],
  "knowledge_mounts":  [ { "mount_id": "...", "source": "...", "access": "read",
                           "citation_required": true, "acl_scope": ["..."] } ],
  "tool_permissions":  [ { "tool": "web_browsing", "mode": "read",
                           "requires_approval": false } ],
  "review_gate":       { "required": true, "approver_role": "...", "applies_to": [...] }
}
```

### 8 个必填字段

`role_card_version` · `bot_id` · `display_name` · `domain` ·
`role` · `responsibilities` · `knowledge_mounts` · `tool_permissions`

### 设计要点

1. **`domain` 枚举隔离**：`enterprise_management` / `customer_operation`
   两个域，为后续「域隔离」任务提供基础。
2. **最小权限**：`tool_permissions` 未列出的工具视为 **deny**，
   `mode` 只有 `deny` / `read` / `write` 三档。
3. **`in_scope: false`**：职责清单支持显式声明「不在本 Bot 范围」，
   把边界写进结构里而不是文档里。
4. **`citation_required`**：知识挂载点可要求引用来源，
   为后续「知识接线」「证据台账」任务预留字段。
5. **`review_gate`**：强制人工审核门，对应后续「高风险操作人工审核」任务。
6. **`additionalProperties: false`**：拒绝未定义字段，防止角色卡随意膨胀。

## 校验器能力

`validate.py` 实现 JSON Schema draft-07 的**必要子集**（零依赖）：

- `type` / `required` / `properties` / `additionalProperties`
- `items` / `enum` / `pattern` / `minLength` / `maxLength`
- `minItems` / `maxItems` / `minimum` / `maximum` / `default`（填充）

错误信息带**精确路径**，例如：

```
$.bot_id: 值 'Bad_ID' 不匹配模式 ^[a-z][a-z0-9-]{2,63}$
$.role.purpose: 长度 2 < 最小 10
$: 缺少必填字段 'display_name'
$: 不允许的额外字段 'extra_field'
```

## 验收验证结果

```
✅ 1. schema loadable, draft-07 -- title=Bot Role Card
✅ 2. schema declares 8 required fields -- ['role_card_version', 'bot_id', 'display_name', 'role', 'responsibilities', 'knowledge_mounts', 'tool_permissions', 'domain']
✅ 3. valid example passes (rolecard_hr_onboarding.json) -- bot_id=hr-onboarding-bot
✅ 4. valid example passes (rolecard_customer_quote.json) -- bot_id=customer-quote-bot
✅ 5. defaults applied (escalation) -- escalation=human_review
✅ 6. each required field caught when removed -- 8/8 caught
✅ 7. invalid example rejected (>=5 errors) -- 8 errors
✅ 8. extra field rejected
✅ 9. domain enum enforced
✅ 10. unknown tool rejected (least privilege)
✅ 11. verification record exists -- 3986 bytes
✅ 12. delivery set complete (11 files) -- 11 files
Result: PASS 12   FAIL 0
```

第 6 项是关键：**逐个删除 8 个必填字段，校验器必须全部报错** ——
这直接对应验收标准的「必填字段校验」，不是只看代码存在。
第 11-12 项证明交付齐套：验证记录存在、全部 11 个交付文件无死引用。

## 环境

- Python 3.8+
- **零第三方依赖**（纯标准库：json / re / os / sys）

## 边界说明

本单范围为「实现角色、职责、知识挂载与工具权限的结构化角色卡」。
以下**不在本单范围**：

- 角色卡的实际运行时执行（Bot 调度、会话管理）—— 属其他拆分单
- 知识库的实际接入与检索实现 —— 属「知识接线」类拆分单
- 真实账号与数据 —— 本单按原文要求使用脱敏样例
