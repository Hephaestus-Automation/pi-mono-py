# pi-mono-py 实施规划（基于实际代码审查）

> 最后更新: 2026-02-12
> 基于: 实际代码审查结果

---

## 1. 当前状态总览

### 1.1 代码统计

```
总代码行数: 3,185 行
├── pi-ai (1,726 行)
│   ├── types.py           315 ✓ 核心类型完整
│   ├── providers/openai.py 339 ⚠️ 有 bug
│   ├── providers/anthropic.py 330 ⚠️ 有 bug
│   ├── providers/google.py 367 ⚠️ 有 bug
│   ├── providers/transform.py 210 ⚠️ 不完整
│   ├── event_stream.py     68 ✓ 基本完整
│   ├── models.py           51 ⚠️ 缺少预定义模型
│   ├── stream.py           48 ✓ 基本完整
│   ├── registry.py         46 ⚠️ 有 bug
│   └── env_keys.py         72 ✓ 基本完整
│
└── pi-agent (1,095 行)
    ├── agent.py           413 ✓ 大部分完成
    ├── loop.py            417 ⚠️ 有 bug/不完整
    └── types.py           156 ✓ 核心类型完整
```

### 1.2 测试状态

```
测试用例: 8 个 (全部通过)
├── pi-ai/tests/test_types.py
│   ├── test_user_message_creation ✓
│   ├── test_model_cost_calculation ✓
│   ├── test_env_api_key ✓
│   └── test_event_stream_basic ✓
│
└── pi-agent/tests/test_agent.py
    ├── test_agent_state_default ✓
    ├── test_agent_tool_result ✓
    ├── test_agent_events ✓
    └── test_steering_queue_one_at_a_time ✓

覆盖率: 未知 (需要配置 pytest-cov)
```

### 1.3 已知问题

| 文件 | 问题 | 严重性 |
|------|------|--------|
| `openai.py` | 缺少事件类型导入 | 🔴 高 |
| `anthropic.py` | 事件类型未定义、缩进错误 | 🔴 高 |
| `google.py` | 事件类型未定义 | 🔴 高 |
| `transform.py` | `is_same_model` 未定义 | 🔴 高 |
| `registry.py` | `_registry` 变量作用域错误 | 🔴 高 |
| `agent.py` | `AgentEndEvent` 未导入 | 🟡 中 |
| `models.py` | 缺少预定义模型注册 | 🟡 中 |

---

## 2. 实施阶段规划

### Phase 0: 修复现有 Bug (1-2 天) 🔴 紧急

**目标**: 修复所有已知的代码错误，确保基本功能可用

#### 任务清单

- [ ] **修复 pi-ai/types.py**
  - [ ] 确认所有事件类型导出
  - [ ] 添加缺失的类型别名

- [ ] **修复 pi-ai/providers/openai.py**
  ```python
  # 需要添加导入
  from pi_ai.types import (
      StartEvent, TextDeltaEvent, ThinkingDeltaEvent,
      ToolcallEndEvent, ToolcallDeltaEvent, DoneEvent, ErrorEvent
  )
  ```

- [ ] **修复 pi-ai/providers/anthropic.py**
  - [ ] 添加事件类型导入
  - [ ] 修复缩进问题 (except 块)
  - [ ] 修复 `normalize_mistral_tool_id` 引用

- [ ] **修复 pi-ai/providers/google.py**
  - [ ] 添加事件类型导入
  - [ ] 修复事件发射逻辑

- [ ] **修复 pi-ai/providers/transform.py**
  - [ ] 实现 `is_same_model` 函数
  - [ ] 修复类型注解

- [ ] **修复 pi-ai/registry.py**
  - [ ] 修复 `_registry` 变量作用域
  - [ ] 确保注册/注销功能正常

- [ ] **修复 pi-agent/agent.py**
  - [ ] 添加 `AgentEndEvent` 导入

#### 验证标准
- [ ] 所有文件通过 `python -m py_compile`
- [ ] 所有文件通过 `ruff check`
- [ ] 所有现有测试通过
- [ ] 基础示例可以运行

---

### Phase 1: 完善类型系统 (2-3 天)

**目标**: 确保所有类型定义与 TypeScript 版本一致

#### 1.1 事件类型完善 (types.py)

当前状态: ✅ 12/12 事件类型已定义

需要验证:
- [ ] 所有事件类型的字段完整性
- [ ] Pydantic 验证规则
- [ ] JSON 序列化/反序列化
- [ ] Union 类型的正确性

#### 1.2 消息类型完善

需要添加/验证:
- [ ] `UserMessage.content` 支持 `str | list[UserContent]`
- [ ] `AssistantMessage` 所有必需字段
- [ ] `ToolResultMessage` 所有必需字段
- [ ] 消息的 JSON Schema 生成

#### 1.3 新增测试

```python
# tests/pi_ai/test_types_complete.py
- [ ] test_all_event_types_creation
- [ ] test_message_serialization
- [ ] test_content_type_validation
- [ ] test_union_type_discrimination
```

---

### Phase 2: 完善 Provider 实现 (3-5 天)

**目标**: 实现完整、健壮的 Provider 支持

#### 2.1 Provider 接口标准化

```python
# 需要定义标准接口
class Provider(Protocol):
    api: str
    
    def stream(
        self, model: Model, context: Context, options: StreamOptions | None
    ) -> AssistantMessageEventStream: ...
    
    def stream_simple(
        self, model: Model, context: Context, options: SimpleStreamOptions | None
    ) -> AssistantMessageEventStream: ...
```

#### 2.2 OpenAI Provider 完善

**当前问题**:
- 流式响应解析可能有问题
- 工具调用处理不完整
- 缺少错误重试逻辑

**需要实现**:
- [ ] 完整的 Chat Completions API
  - [ ] 文本生成
  - [ ] 流式响应
  - [ ] 工具调用 (完整流程)
  - [ ] 图片输入
  
- [ ] Responses API (o1/o3)
  - [ ] reasoning_effort 参数
  - [ ] 非流式响应处理

- [ ] 错误处理
  - [ ] 重试逻辑 (指数退避)
  - [ ] 超时处理
  - [ ] API 错误映射

- [ ] 成本计算
  - [ ] 缓存 token 处理
  - [ ] 价格计算

#### 2.3 Anthropic Provider 完善

**需要实现**:
- [ ] Messages API
  - [ ] 文本生成
  - [ ] 流式响应
  - [ ] 工具调用
  - [ ] 图片输入

- [ ] Thinking Blocks
  - [ ] thinking_enabled 参数
  - [ ] thinking_budget_tokens 参数
  - [ ] thinking 事件流

- [ ] OAuth 支持
  - [ ] ANTHROPIC_OAUTH_TOKEN
  - [ ] 令牌刷新

#### 2.4 Google Provider 完善

**需要实现**:
- [ ] Generative AI API
  - [ ] 文本生成
  - [ ] 流式响应
  - [ ] 工具调用
  - [ ] 图片输入

- [ ] Vertex AI
  - [ ] ADC 认证
  - [ ] 项目/区域配置

#### 2.5 其他 Provider (P2 优先级)

- [ ] Groq (OpenAI 兼容)
- [ ] Mistral (OpenAI 兼容)
- [ ] xAI (OpenAI 兼容)

#### 2.6 跨提供商转换 (transform.py)

**需要完善**:
- [ ] `transform_messages()` 完整实现
  - [ ] thinking 块转换
  - [ ] 工具调用 ID 规范化
  - [ ] 消息格式适配

- [ ] `normalize_tool_call_id()` 多格式支持
  - [ ] Mistral 格式
  - [ ] 其他 provider 格式

#### 2.7 Provider 测试

```python
# tests/pi_ai/providers/
- [ ] test_openai_chat_completions.py
- [ ] test_openai_responses_api.py
- [ ] test_anthropic_messages.py
- [ ] test_google_generative_ai.py
- [ ] test_transform_messages.py
```

---

### Phase 3: 模型注册系统 (1-2 天)

**目标**: 完善模型注册和查询功能

#### 3.1 模型注册表完善

```python
# packages/pi_ai/src/pi_ai/models.py

# 需要添加
- [ ] 预定义模型注册函数
  - [ ] register_openai_models()
  - [ ] register_anthropic_models()
  - [ ] register_google_models()
  - [ ] register_all_models()

# 预定义模型数据
- [ ] OpenAI 模型列表 (gpt-4o, gpt-4o-mini, etc.)
- [ ] Anthropic 模型列表 (claude-3.5-sonnet, etc.)
- [ ] Google 模型列表 (gemini-2.5-flash, etc.)
```

#### 3.2 成本计算验证

- [ ] 验证 `calculate_cost()` 计算逻辑
- [ ] 添加测试用例

---

### Phase 4: Agent 运行时完善 (3-4 天)

**目标**: 完善 Agent 类和循环逻辑

#### 4.1 Agent 类完善

**当前状态**: 大部分完成，有小问题

需要修复/完善:
- [ ] 导入 `AgentEndEvent` 类型
- [ ] 验证事件发射逻辑
- [ ] 错误处理流程

#### 4.2 Agent 循环完善

**当前状态**: 基本结构存在，需要完善

需要实现:
- [ ] 完整的 `agent_loop()` 函数
  - [ ] 消息注入
  - [ ] LLM 调用
  - [ ] 工具执行
  - [ ] 事件发射
  - [ ] 转向检查
  - [ ] 跟进检查

- [ ] `agent_loop_continue()` 函数
  - [ ] 从现有上下文继续

- [ ] 工具执行逻辑
  - [ ] 并行执行
  - [ ] 超时处理
  - [ ] 取消支持

- [ ] 重试逻辑
  - [ ] API 错误重试
  - [ ] 指数退避

#### 4.3 Agent 测试

```python
# tests/pi_agent/
- [ ] test_agent_prompt.py
- [ ] test_agent_continue.py
- [ ] test_agent_tool_execution.py
- [ ] test_agent_steering.py
- [ ] test_agent_follow_up.py
- [ ] test_agent_error_handling.py
```

---

### Phase 5: 工具系统 (2-3 天)

**目标**: 实现完整的工具系统

#### 5.1 工具验证

- [ ] JSON Schema 参数验证
- [ ] 必填字段检查
- [ ] 类型转换

#### 5.2 工具执行框架

- [ ] 同步/异步执行
- [ ] 超时处理
- [ ] 错误捕获
- [ ] 进度更新
- [ ] 取消支持

#### 5.3 内置工具示例

```python
# packages/pi_agent/src/pi_agent/tools/
- [ ] read_file.py
- [ ] write_file.py
- [ ] edit_file.py
- [ ] bash.py
```

---

### Phase 6: 测试基础设施 (1-2 天)

**目标**: 建立完整的测试体系

#### 6.1 测试配置

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=pi_ai --cov=pi_agent --cov-report=html"
```

#### 6.2 测试覆盖率目标

| 模块 | 目标 | 当前 |
|------|------|------|
| pi-ai/types | 90% | ? |
| pi-ai/providers | 80% | 0% |
| pi-ai/stream | 85% | 0% |
| pi-agent/agent | 85% | ? |
| pi-agent/loop | 80% | 0% |

#### 6.3 Mock 策略

```python
# tests/mocks/
- [ ] mock_httpx.py (HTTP 响应 Mock)
- [ ] mock_providers.py (Provider Mock)
- [ ] mock_tools.py (工具 Mock)
```

---

### Phase 7: 文档和示例 (2-3 天)

**目标**: 完善文档和使用示例

#### 7.1 API 文档

```
docs/
├── api/
│   ├── pi-ai/
│   │   ├── types.md
│   │   ├── stream.md
│   │   └── providers.md
│   └── pi-agent/
│       ├── agent.md
│       ├── tools.md
│       └── loop.md
└── guides/
    ├── getting-started.md
    ├── providers.md
    └── tools.md
```

#### 7.2 示例完善

```python
examples/
├── 00_quick_start.py          ✓ 已有
├── 01_simple_agent.py          ✓ 已有
├── 02_agent_with_tools.py      ✓ 已有
├── 03_agent_events.py          ✓ 已有
├── 04_steering_followup.py    ✓ 已有
├── 05_streaming_response.py   ✓ 已有
├── 06_provider_config.py       ✓ 已有
├── 07_custom_tools.py          # 新增
├── 08_context_compression.py   # 新增
└── 09_multi_turn.py            # 新增
```

---

## 3. 优先级和时间表

### 紧急 (本周)

| 任务 | 时间 | 优先级 |
|------|------|--------|
| Phase 0: 修复 Bug | 1-2 天 | 🔴 P0 |
| Phase 1: 类型系统完善 | 2-3 天 | 🔴 P0 |

### 短期 (2 周内)

| 任务 | 时间 | 优先级 |
|------|------|--------|
| Phase 2: Provider 实现 | 3-5 天 | 🔴 P0 |
| Phase 3: 模型注册 | 1-2 天 | 🟡 P1 |
| Phase 6: 测试基础设施 | 1-2 天 | 🟡 P1 |

### 中期 (1 个月内)

| 任务 | 时间 | 优先级 |
|------|------|--------|
| Phase 4: Agent 运行时 | 3-4 天 | 🟡 P1 |
| Phase 5: 工具系统 | 2-3 天 | 🟡 P1 |
| Phase 7: 文档 | 2-3 天 | 🟢 P2 |

---

## 4. 技术债务

### 当前需要修复

1. **导入错误** - 多个文件缺少必要的导入
2. **变量作用域** - `registry.py` 的 `_registry` 问题
3. **类型注解** - 部分函数缺少返回类型
4. **错误处理** - Provider 缺少统一的错误处理

### 需要重构

1. **Provider 接口** - 需要定义标准 Protocol
2. **事件发射** - 统一事件发射逻辑
3. **配置管理** - 统一配置加载方式

---

## 5. 风险评估

### 高风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Provider API 变化 | 高 | 使用稳定 API 版本 |
| 异步复杂性 | 中 | 充分测试 |
| 类型不匹配 | 中 | 使用 Pydantic 严格模式 |

### 中风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 测试覆盖不足 | 中 | 优先添加核心测试 |
| 文档滞后 | 低 | 同步更新 |
| 性能问题 | 低 | 基准测试 |

---

## 6. 下一步行动

### 立即执行 (今天)

1. [ ] 修复所有导入错误
2. [ ] 修复 registry.py 变量作用域
3. [ ] 修复 transform.py 的 is_same_model

### 本周完成

1. [ ] 所有 Provider 文件可正常导入
2. [ ] 基础测试通过
3. [ ] 示例可以运行

### 下周计划

1. [ ] 完善 OpenAI Provider
2. [ ] 完善 Anthropic Provider
3. [ ] 添加 Provider 测试

---

## 7. 附录

### A. 文件状态详细列表

```
pi-ai/
├── types.py           ✅ 完整 (315 行)
├── event_stream.py    ✅ 基本完整 (68 行)
├── stream.py          ✅ 基本完整 (48 行)
├── env_keys.py        ✅ 基本完整 (72 行)
├── models.py          ⚠️ 缺少预定义模型 (51 行)
├── registry.py        🔴 有 bug (46 行)
├── __init__.py        ✅ 正常 (84 行)
└── providers/
    ├── __init__.py    ⚠️ 需要完善 (82 行)
    ├── openai.py      🔴 有 bug (339 行)
    ├── anthropic.py   🔴 有 bug (330 行)
    ├── google.py      🔴 有 bug (367 行)
    └── transform.py   🔴 不完整 (210 行)

pi-agent/
├── types.py           ✅ 完整 (156 行)
├── agent.py           ⚠️ 小问题 (413 行)
├── loop.py            ⚠️ 不完整 (417 行)
└── __init__.py        ✅ 正常 (30 行)
```

### B. 测试覆盖计划

```python
# Phase 1 后应该有的测试
tests/
├── pi_ai/
│   ├── test_types.py          ✓ 4 个测试
│   ├── test_types_complete.py # 新增 10+ 个测试
│   ├── test_event_stream.py   # 新增 5+ 个测试
│   └── test_models.py         # 新增 5+ 个测试
│
└── pi_agent/
    ├── test_agent.py          ✓ 4 个测试
    ├── test_agent_prompt.py   # 新增 5+ 个测试
    ├── test_agent_tools.py    # 新增 5+ 个测试
    └── test_agent_loop.py     # 新增 5+ 个测试
```

### C. 代码风格检查命令

```bash
# 类型检查
pyright packages/

# 代码风格
ruff check packages/

# 测试
pytest -v --cov=pi_ai --cov=pi_agent

# 格式化
ruff format packages/
```

### D. 与原始 TypeScript 版本对应

| TypeScript 包 | Python 状态 | 说明 |
|--------------|------------|------|
| pi-ai | 60% | 核心类型完成，Provider 需要完善 |
| pi-agent-core | 50% | Agent 类基本完成，循环需要完善 |
| pi-coding-agent | 0% | 未开始 |
| pi-tui | 0% | 未开始 (可考虑使用 rich/textual) |
| pi-web-ui | 0% | 未开始 |
| pi-mom | 0% | 未开始 |
| pi-pods | 0% | 未开始 |
