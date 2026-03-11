# OpenClaw 系统设计分析文档

基于 OpenClaw 最新源码的深度分析

---

## 1. 系统架构概览

### 1.1 核心组件关系

OpenClaw 采用 **Gateway 中心化架构**，核心组件包括：

```
┌─────────────────────────────────────────────────────────────┐
│                        Gateway 守护进程                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 消息平台连接  │  │ WebSocket服务 │  │ Canvas服务器  │      │
│  │ WhatsApp     │  │ (18789端口)  │  │ (18793端口)  │      │
│  │ Telegram     │  │              │  │              │      │
│  │ Discord等    │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────┐         ┌──────────┐        ┌──────────┐
    │ 消息路由  │         │ 客户端    │        │ 节点设备  │
    │ 会话管理  │         │ CLI/App  │        │ iOS/Mac  │
    └──────────┘         └──────────┘        └──────────┘
```

**关键设计原则：**

- **单一 Gateway 守护进程**：每台主机只运行一个 Gateway，它是所有消息平台连接的唯一拥有者
- **WebSocket 通信**：所有客户端（CLI、App、Web UI）和节点设备都通过 WebSocket 连接到 Gateway
- **会话隔离**：每个对话通过 `sessionKey` 隔离，支持多用户、多群组、多频道
- **设备配对机制**：基于设备身份的配对和认证，本地连接可自动批准

### 1.2 数据流向

```
用户消息 → 消息平台 → Gateway → 会话路由 → Agent运行时 → 工具调用 → 结果返回
                                      ↓
                                 会话存储
                              (sessions.json + 
                               transcript.jsonl)
```

---

## 2. 记忆系统设计

OpenClaw 的记忆系统是其最核心的设计之一，分为**短期记忆**和**长期记忆**两层。

### 2.1 短期记忆（对话上下文）

**存储位置：**
- `~/.openclaw/agents/<agentId>/sessions/<sessionId>.jsonl`

**数据结构：**
```jsonl
{"type":"session","id":"sess_xxx","cwd":"/path","timestamp":1234567890}
{"type":"message","id":"msg_1","parentId":"sess_xxx","role":"user","content":"..."}
{"type":"message","id":"msg_2","parentId":"msg_1","role":"assistant","content":"..."}
{"type":"message","id":"msg_3","parentId":"msg_2","role":"toolResult","content":"..."}
```

**特点：**
- JSONL 格式，每行一个条目
- 树状结构（通过 `id` + `parentId` 链接）
- 仅追加（append-only），不修改历史
- 包含完整的对话历史、工具调用和结果

### 2.2 长期记忆（持久化知识）

**存储位置：**
- `MEMORY.md` - 精心整理的长期记忆（仅在主会话加载）
- `memory/YYYY-MM-DD.md` - 每日日志（自动加载今天和昨天）

**为什么这样设计？**

1. **安全隔离**：`MEMORY.md` 只在私人会话加载，不会在群组中泄露个人信息
2. **自动管理**：每日文件自动创建，无需手动维护
3. **易于编辑**：纯 Markdown 格式，人类可读可编辑
4. **版本控制友好**：可以用 Git 管理记忆文件

### 2.3 向量记忆搜索

OpenClaw 使用 **混合搜索**（向量 + BM25）来检索记忆：

```javascript
// 伪代码
function memorySearch(query) {
  // 1. 向量搜索（语义相似）
  const vectorResults = embedAndSearch(query, topK * 4);
  
  // 2. BM25 全文搜索（精确匹配）
  const bm25Results = fullTextSearch(query, topK * 4);
  
  // 3. 混合打分
  const merged = mergeResults(vectorResults, bm25Results, {
    vectorWeight: 0.7,
    textWeight: 0.3
  });
  
  return merged.slice(0, topK);
}
```

**为什么混合搜索？**

- **向量搜索**擅长语义理解："Mac Studio gateway host" ≈ "运行 gateway 的机器"
- **BM25 搜索**擅长精确匹配：代码符号、ID、错误信息
- **结合两者**：既能理解自然语言，又能精确定位关键信息

**嵌入缓存机制：**
```javascript
// 缓存策略
const cacheKey = hash(text + provider + model);
if (cache.has(cacheKey)) {
  return cache.get(cacheKey);
}
const embedding = await embed(text);
cache.set(cacheKey, embedding);
```

这避免了重复嵌入相同文本，大幅提升性能。

---

## 3. 对话上下文管理

### 3.1 上下文窗口限制

每个模型都有固定的上下文窗口（如 200K tokens）。OpenClaw 需要在这个限制内管理：

- 系统提示词（工具定义、Skills 列表、工作区文件）
- 对话历史
- 工具调用结果
- 附件（图片、音频转录）

### 3.2 超出限制的处理策略

**1. 自动压缩（Compaction）**

当上下文接近上限时，OpenClaw 会自动压缩旧对话：

```javascript
// 压缩触发条件
if (contextTokens > contextWindow - reserveTokens) {
  // 1. 总结旧对话
  const summary = await summarizeOldMessages(oldMessages);
  
  // 2. 保留最近消息
  const recentMessages = messages.slice(-keepRecentTokens);
  
  // 3. 持久化压缩记录
  transcript.append({
    type: "compaction",
    summary: summary,
    firstKeptEntryId: recentMessages[0].id,
    tokensBefore: contextTokens
  });
}
```

**压缩后的上下文结构：**
```
[系统提示词]
[压缩摘要] ← 旧对话的总结
[最近 20K tokens 的完整对话]
```

**2. 预压缩记忆刷新**

在压缩发生前，OpenClaw 会触发一个**静默回合**，让 AI 把重要信息写入持久化记忆：

```javascript
// 软阈值触发
if (contextTokens > contextWindow - reserveTokens - softThresholdTokens) {
  // 静默提示 AI 写入记忆
  await silentTurn({
    systemPrompt: "Session nearing compaction. Store durable memories now.",
    userPrompt: "Write any lasting notes to memory/YYYY-MM-DD.md; reply with NO_REPLY if nothing to store."
  });
}
```

**为什么这样设计？**
- 避免重要信息在压缩时丢失
- 使用 `NO_REPLY` 机制，用户完全无感知
- 每个压缩周期只触发一次，避免重复

**3. 会话修剪（Session Pruning）**

对于工具调用结果过大的情况，OpenClaw 会在内存中修剪：

```javascript
// 修剪策略（不修改磁盘文件）
function pruneToolResults(messages) {
  return messages.map(msg => {
    if (msg.role === "toolResult" && msg.content.length > maxSize) {
      return {
        ...msg,
        content: msg.content.slice(0, maxSize) + "\n[truncated]"
      };
    }
    return msg;
  });
}
```

**压缩 vs 修剪的区别：**
- **压缩**：持久化到磁盘，永久生效
- **修剪**：仅在内存中，不修改 transcript 文件

---

## 4. 语义理解实现

OpenClaw 本身**不做语义理解** - 它完全依赖底层的 LLM（如 Claude、GPT-4）。

### 4.1 OpenClaw 的角色

OpenClaw 是一个**编排层**（Orchestration Layer），负责：

1. **构建上下文**：组装系统提示词、对话历史、工具定义
2. **工具调用路由**：解析 LLM 的工具调用请求，执行对应工具
3. **结果注入**：把工具执行结果注入回上下文
4. **循环控制**：管理多轮对话的 Agent Loop

### 4.2 上下文构建

```javascript
// 伪代码：构建发送给 LLM 的上下文
function buildContext(session) {
  return [
    // 1. 系统提示词
    {
      role: "system",
      content: buildSystemPrompt({
        tools: getAvailableTools(),
        skills: listSkills(),
        workspace: loadWorkspaceFiles(),
        runtime: getRuntimeInfo()
      })
    },
    
    // 2. 对话历史（可能包含压缩摘要）
    ...loadTranscript(session.sessionId),
    
    // 3. 当前用户消息
    {
      role: "user",
      content: userMessage
    }
  ];
}
```

**系统提示词包含：**
- 工具列表和 JSON Schema
- Skills 元数据（名称、描述、位置）
- 工作区文件（AGENTS.md、SOUL.md、USER.md 等）
- 运行时信息（时间、操作系统、模型名称）

---

## 5. 人机交互设计

OpenClaw 的交互设计非常人性化，体现在多个方面：

### 5.1 多平台支持

支持主流消息平台，用户可以在熟悉的环境中使用：
- WhatsApp
- Telegram
- Discord
- Slack
- iMessage
- Signal

### 5.2 斜杠命令系统

提供直观的命令接口：

```
/status        - 查看会话状态和 token 使用
/context       - 查看上下文构成
/compact       - 手动触发压缩
/new           - 开始新会话
/think         - 启用思考模式
/verbose       - 启用详细输出
/model gpt-4   - 切换模型
```

### 5.3 静默操作（NO_REPLY）

对于后台任务，AI 可以回复 `NO_REPLY` 来避免打扰用户：

```javascript
// AI 的回复
if (reply.startsWith("NO_REPLY")) {
  // 不发送给用户，静默完成
  return;
}
```

**应用场景：**
- 预压缩记忆刷新
- 后台数据整理
- 定时任务执行

### 5.4 心跳机制（Heartbeat）

AI 可以主动检查和提醒：

```markdown
# HEARTBEAT.md
每 30 分钟检查一次：
- 未读邮件
- 即将到来的日历事件
- 重要通知
```

**智能判断：**
- 深夜时段（23:00-08:00）保持安静
- 有重要事项时主动提醒
- 没有新信息时回复 `HEARTBEAT_OK`

### 5.5 线程绑定（Thread Binding）

在 Discord 等平台，可以为子任务创建独立线程：

```javascript
// 创建线程绑定的子 Agent
await sessions_spawn({
  task: "研究这个技术问题",
  thread: true,  // 创建独立线程
  mode: "session"  // 持久会话
});
```

用户可以在线程中继续对话，不会干扰主会话。

---

## 6. 复杂代码生成的自我调试

### 6.1 工具生态

OpenClaw 提供丰富的工具让 AI 自主完成开发任务：

**文件操作：**
```javascript
read(path)           // 读取文件
write(path, content) // 写入文件
edit(path, oldText, newText)  // 精确编辑
```

**代码执行：**
```javascript
exec(command)        // 执行 shell 命令
process(action)      // 管理后台进程
```

**代码分析：**
```javascript
readCode(path)       // 读取代码并提供 AST 分析
getDiagnostics()     // 获取语法/类型错误
```

### 6.2 自我调试流程

AI 可以自主完成完整的开发循环：

```
1. 生成代码
   ↓
2. 写入文件 (write)
   ↓
3. 检查错误 (getDiagnostics)
   ↓
4. 发现问题？
   ├─ 是 → 修复代码 (edit) → 回到步骤 3
   └─ 否 → 运行测试 (exec)
          ↓
          测试失败？
          ├─ 是 → 分析错误 → 修复 → 回到步骤 3
          └─ 否 → 完成 ✓
```

**实际案例：**

```javascript
// AI 的思考过程（伪代码）
async function implementFeature() {
  // 1. 生成代码
  await write("feature.ts", generateCode());
  
  // 2. 检查语法错误
  const diagnostics = await getDiagnostics("feature.ts");
  if (diagnostics.errors.length > 0) {
    // 3. 修复错误
    await edit("feature.ts", buggyCode, fixedCode);
  }
  
  // 4. 运行测试
  const testResult = await exec("npm test");
  if (testResult.exitCode !== 0) {
    // 5. 分析失败原因
    const analysis = analyzeTestFailure(testResult.stderr);
    // 6. 修复并重试
    await edit("feature.ts", oldImpl, newImpl);
    return implementFeature(); // 递归重试
  }
  
  return "Feature implemented successfully";
}
```

### 6.3 循环检测

为了防止 AI 陷入无限循环，OpenClaw 有循环检测机制：

```javascript
// 检测重复的工具调用模式
function detectLoop(recentCalls) {
  const pattern = findRepeatingPattern(recentCalls);
  if (pattern && pattern.repeatCount > 3) {
    throw new LoopDetectedError(
      "Detected repeating pattern: " + pattern.description
    );
  }
}
```

---

## 7. Agent 架构：单 Agent 还是多 Agent？

### 7.1 主 Agent + 子 Agent 架构

OpenClaw 采用**混合架构**：

```
主 Agent (depth 0)
  ├─ 子 Agent 1 (depth 1) - 可以是编排者
  │   ├─ 子子 Agent 1.1 (depth 2) - 工作者
  │   └─ 子子 Agent 1.2 (depth 2) - 工作者
  ├─ 子 Agent 2 (depth 1)
  └─ 子 Agent 3 (depth 1)
```

**深度限制：**
- 默认 `maxSpawnDepth = 1`（只允许一层子 Agent）
- 可配置为 `2`（支持编排者模式）
- 最大深度为 `5`

### 7.2 子 Agent 的特点

**隔离性：**
- 独立的会话（`agent:<id>:subagent:<uuid>`）
- 独立的上下文窗口
- 独立的 token 计数

**通信机制：**
```javascript
// 子 Agent 完成后自动通知父 Agent
{
  status: "completed",
  result: "任务完成，发现 3 个问题...",
  runtime: "5m12s",
  tokens: { input: 1234, output: 567 },
  sessionKey: "agent:main:subagent:abc123"
}
```

**工具权限：**
- 默认：所有工具 **除了** 会话管理工具
- 编排者（depth 1，当 maxSpawnDepth >= 2）：额外获得 `sessions_spawn`、`subagents` 等
- 工作者（depth 2）：无会话管理权限

### 7.3 并发控制

```javascript
// 配置
{
  subagents: {
    maxConcurrent: 8,           // 全局并发上限
    maxChildrenPerAgent: 5,     // 每个 Agent 的子 Agent 上限
    archiveAfterMinutes: 60     // 自动归档时间
  }
}
```

**为什么需要限制？**
- 防止资源耗尽
- 避免 token 成本失控
- 保持系统响应性

---

## 8. 主 Agent Loop 实现

### 8.1 核心循环

```javascript
// 简化的 Agent Loop 伪代码
async function agentLoop(userMessage) {
  let context = buildContext(session, userMessage);
  
  while (true) {
    // 1. 调用 LLM
    const response = await callLLM(context);
    
    // 2. 检查是否需要工具调用
    if (response.toolCalls && response.toolCalls.length > 0) {
      // 3. 执行工具
      const toolResults = await executeTools(response.toolCalls);
      
      // 4. 把结果注入上下文
      context.push({
        role: "assistant",
        content: response.content,
        toolCalls: response.toolCalls
      });
      context.push({
        role: "toolResult",
        content: toolResults
      });
      
      // 5. 继续循环
      continue;
    }
    
    // 6. 没有工具调用，返回最终回复
    return response.content;
  }
}
```

### 8.2 关键设计点

**1. 工具调用的原子性**

```javascript
// 批量执行工具调用
async function executeTools(toolCalls) {
  // 并行执行独立的工具调用
  const results = await Promise.all(
    toolCalls.map(call => executeTool(call))
  );
  return results;
}
```

**2. 错误处理**

```javascript
async function executeTool(call) {
  try {
    return await tools[call.name](call.params);
  } catch (error) {
    // 把错误作为工具结果返回给 LLM
    return {
      error: error.message,
      stack: error.stack
    };
  }
}
```

LLM 会看到错误信息，并尝试修复或换一种方式。

**3. 上下文溢出处理**

```javascript
async function callLLM(context) {
  try {
    return await llm.complete(context);
  } catch (error) {
    if (error.code === "context_overflow") {
      // 触发压缩
      await compactSession();
      // 重试
      return await llm.complete(buildContext());
    }
    throw error;
  }
}
```

**4. 循环检测**

```javascript
// 检测工具调用模式
const recentCalls = session.getRecentToolCalls(10);
if (detectRepeatingPattern(recentCalls)) {
  throw new Error("Detected infinite loop in tool calls");
}
```

### 8.3 值得借鉴的设计

**1. 事件驱动架构**

```javascript
// Gateway 发出事件
gateway.emit("agent", {
  type: "streaming",
  content: partialResponse
});

// 客户端监听事件
gateway.on("agent", (event) => {
  if (event.type === "streaming") {
    updateUI(event.content);
  }
});
```

**2. 幂等性保证**

```javascript
// 每个请求都有幂等键
const idempotencyKey = randomUUID();
await gateway.request("agent", {
  idempotencyKey,
  message: userMessage
});

// 服务器端去重
if (cache.has(idempotencyKey)) {
  return cache.get(idempotencyKey);
}
```

**3. 渐进式增强**

```javascript
// 基础功能：简单的对话
// 增强功能：工具调用
// 高级功能：子 Agent、记忆搜索、代码分析

// 用户可以逐步启用功能，不会一次性被复杂性淹没
```

**4. 配置驱动**

```javascript
// 几乎所有行为都可以通过配置调整
{
  agents: {
    defaults: {
      model: "claude-opus-4",
      thinking: "off",
      compaction: { enabled: true },
      memorySearch: { enabled: true },
      subagents: { maxConcurrent: 8 }
    }
  }
}
```

---

## 9. 总结与启示

### 9.1 核心设计哲学

1. **简单优于复杂**：纯文本文件作为记忆，JSONL 作为会话存储
2. **渐进式增强**：基础功能稳定，高级功能可选
3. **用户无感知**：自动压缩、静默操作、智能心跳
4. **开发者友好**：丰富的工具、清晰的文档、灵活的配置

### 9.2 技术亮点

- **混合记忆搜索**：向量 + BM25，兼顾语义和精确匹配
- **预压缩刷新**：在压缩前自动保存重要信息
- **子 Agent 编排**：支持复杂任务的分解和并行
- **自我调试能力**：AI 可以独立完成开发-测试-修复循环

### 9.3 可借鉴的模式

1. **Gateway 中心化**：单一守护进程管理所有连接
2. **WebSocket 通信**：实时双向通信，支持流式输出
3. **设备配对**：安全的远程访问机制
4. **工具权限分层**：主 Agent、编排者、工作者有不同权限
5. **事件驱动**：解耦组件，易于扩展

---

## 附录：关键代码路径

### A.1 会话管理
- 会话存储：`src/config/sessions.ts`
- 会话路由：`src/auto-reply/reply/session.ts`
- 压缩逻辑：`src/agents/pi-embedded-runner.ts`

### A.2 记忆系统
- 记忆搜索：`extensions/memory-lancedb/`
- 向量索引：使用 LanceDB + sqlite-vec
- 混合搜索：向量 + BM25 融合

### A.3 Gateway
- 协议定义：TypeBox schemas
- WebSocket 服务：`src/gateway/`
- 设备配对：`src/gateway/pairing/`

### A.4 工具系统
- 工具注册：`src/tools/`
- 工具执行：`src/agents/pi-embedded-runner.ts`
- 权限控制：`src/tools/policy.ts`

---

**文档版本**：基于 OpenClaw 2026.1.x 源码分析  
**生成时间**：2026-03-05  
**作者**：硅基小橘子 🍊
