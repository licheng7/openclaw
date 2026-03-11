# OpenClaw Skill 定制完整教程

## 目录
1. [什么是 Skill](#什么是-skill)
2. [Skill 的结构](#skill-的结构)
3. [创建 Skill 的完整流程](#创建-skill-的完整流程)
4. [核心设计原则](#核心设计原则)
5. [实战示例](#实战示例)
6. [常见问题](#常见问题)

---

## 什么是 Skill

Skill 是 OpenClaw 的**模块化知识包**，用于扩展 AI 助手的能力。可以把它理解为：

- 📚 **专业领域的操作手册** - 为特定任务提供详细指导
- 🔧 **工具集成的使用指南** - 教会 AI 如何使用特定工具
- 🔄 **特定任务的工作流程** - 定义标准化的操作步骤
- 💾 **可复用的脚本和资源** - 提供现成的代码和模板

### Skill 的价值

Skill 将 OpenClaw 从通用助手转变为**领域专家**：

- **无需重复编写代码** - 常用脚本打包复用
- **标准化工作流程** - 确保任务执行的一致性
- **领域知识沉淀** - 公司规范、API 文档、数据模式等
- **提高响应质量** - 提供上下文相关的专业指导

---

## Skill 的结构

每个 Skill 由以下部分组成：

\`\`\`
skill-name/
├── SKILL.md (必需)
│   ├── YAML frontmatter (name + description)
│   └── Markdown 指令
└── 可选资源/
    ├── scripts/      - 可执行脚本 (Python/Bash/Node.js)
    ├── references/   - 参考文档 (按需加载)
    └── assets/       - 输出用的文件 (模板、图标等)
\`\`\`

### SKILL.md (必需)

每个 SKILL.md 包含两部分：

#### 1. YAML Frontmatter (元数据)

\`\`\`yaml
---
name: skill-name
description: 清晰描述 Skill 做什么，以及何时使用它
---
\`\`\`

**description 非常重要！** 它是 Skill 的**触发机制**：
- 描述 Skill 的功能
- 列出具体的使用场景
- 包含触发关键词

示例：
\`\`\`yaml
description: "PDF 文档处理工具。支持旋转、合并、拆分、提取文本。当用户需要处理 PDF 文件时使用。"
\`\`\`

#### 2. Markdown 正文 (指令)

提供详细的使用说明：
- 如何使用 Skill
- 工作流程步骤
- 脚本和资源的使用方法
- 示例代码

**写作原则：**
- 使用**祈使句/不定式**（"使用 X" 而不是 "你可以使用 X"）
- **简洁至上** - 只包含必要信息
- **优先示例** - 代码胜过长篇解释

### 可选资源

#### scripts/ - 可执行脚本

存放需要确定性执行的代码：

**何时使用：**
- 重复编写相同代码
- 需要精确的执行逻辑
- 复杂的数据处理

**示例：**
- \`scripts/rotate_pdf.py\` - PDF 旋转
- \`scripts/merge_images.sh\` - 图片合并
- \`scripts/parse_json.js\` - JSON 解析

#### references/ - 参考文档

存放需要按需加载的文档：

**何时使用：**
- 数据库模式
- API 文档
- 公司规范
- 详细的工作流程指南

**示例：**
- \`references/database_schema.md\` - 数据库结构
- \`references/api_docs.md\` - API 接口文档
- \`references/company_policies.md\` - 公司政策

#### assets/ - 输出资源

存放用于输出的文件（不加载到上下文）：

**何时使用：**
- 模板文件
- 样板代码
- 图片、图标
- 字体文件

**示例：**
- \`assets/template.html\` - HTML 模板
- \`assets/logo.png\` - Logo 图片
- \`assets/boilerplate/\` - 项目脚手架

---

## 创建 Skill 的完整流程

### 步骤 1: 理解需求（具体例子）

在创建 Skill 之前，先明确：
- 这个 Skill 要解决什么问题？
- 用户会如何使用它？
- 什么样的请求应该触发它？

**示例问题：**
- "你想让 Skill 支持哪些功能？"
- "能给我一些使用场景的例子吗？"
- "用户会怎么描述这个需求？"

**示例场景：**
- 用户说："帮我旋转这个 PDF"
- 用户说："合并这些图片"
- 用户说："查询数据库中的用户数"

### 步骤 2: 规划资源

分析每个使用场景，确定需要哪些资源：

| 场景 | 需要的资源 | 类型 |
|------|-----------|------|
| 旋转 PDF | PDF 旋转脚本 | scripts/ |
| 查询数据库 | 数据库模式文档 | references/ |
| 创建网页 | HTML 模板 | assets/ |

**决策标准：**
- **重复编写的代码** → scripts/
- **需要参考的文档** → references/
- **用于输出的文件** → assets/

### 步骤 3: 初始化 Skill

使用 OpenClaw 提供的初始化脚本：

\`\`\`bash
# 基本用法
scripts/init_skill.py <skill-name> --path <输出目录>

# 指定资源类型
scripts/init_skill.py pdf-editor --path skills/public --resources scripts,references

# 包含示例文件
scripts/init_skill.py bigquery --path skills/public --resources references --examples
\`\`\`

**参数说明：**
- \`<skill-name>\`: Skill 名称（小写字母、数字、连字符）
- \`--path\`: 输出目录
- \`--resources\`: 需要的资源类型（逗号分隔）
- \`--examples\`: 生成示例文件

**示例：**
\`\`\`bash
# 创建 PDF 编辑 Skill
scripts/init_skill.py pdf-editor --path /root/.openclaw/workspace/skills --resources scripts

# 创建 BigQuery Skill
scripts/init_skill.py bigquery --path /root/.openclaw/workspace/skills --resources references
\`\`\`

脚本会自动创建：
- Skill 目录结构
- SKILL.md 模板（带 TODO 占位符）
- 指定的资源目录

### 步骤 4: 编辑 Skill

#### 4.1 编写 YAML Frontmatter

\`\`\`yaml
---
name: pdf-editor
description: PDF 文档处理工具。支持旋转、合并、拆分、提取文本。当用户需要处理 PDF 文件（.pdf）时使用，包括：(1) 旋转页面，(2) 合并多个 PDF，(3) 拆分 PDF，(4) 提取文本内容。
---
\`\`\`

**description 写作技巧：**
- 第一句：简短描述功能
- 第二句：列出支持的操作
- 第三句：明确触发条件

#### 4.2 编写 Markdown 正文

\`\`\`markdown
# PDF Editor Skill

## 快速开始

旋转 PDF 页面：

\\\`\\\`\\\`bash
python scripts/rotate_pdf.py input.pdf output.pdf --angle 90
\\\`\\\`\\\`

## 支持的操作

### 1. 旋转页面
使用 \\\`rotate_pdf.py\\\` 脚本旋转 PDF 页面。

### 2. 合并 PDF
使用 \\\`merge_pdf.py\\\` 脚本合并多个 PDF 文件。

### 3. 拆分 PDF
使用 \\\`split_pdf.py\\\` 脚本拆分 PDF 文件。

## 高级功能

详细的 API 文档请参考 [references/pdf_api.md](references/pdf_api.md)。
\`\`\`

#### 4.3 添加脚本

创建 \`scripts/rotate_pdf.py\`：

\`\`\`python
#!/usr/bin/env python3
import sys
from PyPDF2 import PdfReader, PdfWriter

def rotate_pdf(input_path, output_path, angle):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)
    
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: rotate_pdf.py input.pdf output.pdf --angle 90")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    angle = int(sys.argv[4])
    
    rotate_pdf(input_path, output_path, angle)
    print(f"PDF rotated {angle} degrees: {output_path}")
\`\`\`

**重要：测试脚本！**
\`\`\`bash
# 测试脚本是否正常工作
python scripts/rotate_pdf.py test.pdf output.pdf --angle 90
\`\`\`

#### 4.4 添加参考文档

创建 \`references/pdf_api.md\`：

\`\`\`markdown
# PDF API 参考

## PyPDF2 常用方法

### PdfReader
- \\\`PdfReader(file)\\\` - 读取 PDF 文件
- \\\`reader.pages\\\` - 获取所有页面

### PdfWriter
- \\\`PdfWriter()\\\` - 创建 PDF 写入器
- \\\`writer.add_page(page)\\\` - 添加页面
- \\\`writer.write(file)\\\` - 写入文件

## 示例

### 提取特定页面
\\\`\\\`\\\`python
reader = PdfReader('input.pdf')
writer = PdfWriter()
writer.add_page(reader.pages[0])  # 只提取第一页
\\\`\\\`\\\`
\`\`\`

### 步骤 5: 打包 Skill

使用打包脚本验证并打包 Skill：

\`\`\`bash
scripts/package_skill.py /root/.openclaw/workspace/skills/pdf-editor
\`\`\`

**打包过程：**
1. **自动验证** Skill：
   - YAML frontmatter 格式
   - 必需字段（name, description）
   - 文件结构
   - 命名规范

2. **生成 .skill 文件**：
   - 文件名：\`pdf-editor.skill\`
   - 格式：ZIP 压缩包（扩展名为 .skill）
   - 包含所有文件和目录结构

**如果验证失败：**
- 脚本会报告具体错误
- 修复错误后重新运行打包命令

**指定输出目录：**
\`\`\`bash
scripts/package_skill.py /root/.openclaw/workspace/skills/pdf-editor ./dist
\`\`\`

### 步骤 6: 测试和迭代

1. **安装 Skill** 到 OpenClaw
2. **实际使用** Skill 处理任务
3. **观察问题**：
   - Skill 是否正确触发？
   - 指令是否清晰？
   - 脚本是否正常工作？
4. **改进 Skill**：
   - 更新 SKILL.md
   - 修复脚本 bug
   - 添加缺失的文档
5. **重新打包** 并测试

---

## 核心设计原则

### 1. 渐进式加载

Skill 使用三级加载系统管理上下文：

| 级别 | 内容 | 何时加载 | 大小限制 |
|------|------|---------|---------|
| 1 | 元数据 (name + description) | 始终 | ~100 词 |
| 2 | SKILL.md 正文 | Skill 触发后 | <5k 词 |
| 3 | 捆绑资源 | 按需 | 无限制 |

**为什么重要？**
- 上下文窗口是稀缺资源
- 只加载需要的信息
- 提高响应速度

### 2. 简洁为王

**核心原则：** 只包含 AI 不知道的信息。

**挑战每一句话：**
- "AI 真的需要这个解释吗？"
- "这段话值得占用 token 吗？"

**优先示例代码：**
❌ 不好：
\`\`\`markdown
要旋转 PDF，你需要使用 PyPDF2 库。首先导入必要的模块，然后创建一个 PdfReader 对象来读取文件，接着创建一个 PdfWriter 对象...
\`\`\`

✅ 好：
\`\`\`python
from PyPDF2 import PdfReader, PdfWriter

reader = PdfReader('input.pdf')
writer = PdfWriter()
for page in reader.pages:
    page.rotate(90)
    writer.add_page(page)
\`\`\`

**保持 SKILL.md < 500 行：**
- 超过限制时，拆分到 references/
- 在 SKILL.md 中引用外部文档

### 3. 适当的自由度

根据任务的脆弱性和变化性选择指令的具体程度：

| 自由度 | 形式 | 适用场景 |
|--------|------|---------|
| 高 | 文本指令 | 多种方法都可行，需要根据上下文决策 |
| 中 | 伪代码 + 参数 | 有首选模式，允许一定变化 |
| 低 | 具体脚本 | 操作脆弱，需要严格顺序 |

**示例：**

**高自由度（文本指令）：**
\`\`\`markdown
分析用户反馈，识别主要问题和改进建议。
\`\`\`

**中等自由度（伪代码）：**
\`\`\`markdown
1. 读取反馈文件
2. 使用情感分析识别负面反馈
3. 提取关键词和主题
4. 生成摘要报告
\`\`\`

**低自由度（具体脚本）：**
\`\`\`bash
python scripts/analyze_feedback.py --input feedback.csv --output report.md
\`\`\`

### 4. 渐进式披露

当 Skill 支持多个变体或框架时：

**模式 1: 高层指南 + 引用**
\`\`\`markdown
# PDF 处理

## 快速开始
基础旋转示例...

## 高级功能
- **表单填充**: 查看 [FORMS.md](references/FORMS.md)
- **API 参考**: 查看 [API.md](references/API.md)
\`\`\`

**模式 2: 多领域组织**
\`\`\`
bigquery-skill/
├── SKILL.md (概览和导航)
└── references/
    ├── finance.md (财务指标)
    ├── sales.md (销售数据)
    └── product.md (产品使用)
\`\`\`

**模式 3: 条件详情**
\`\`\`markdown
## 编辑文档
简单编辑直接修改 XML。

**需要追踪更改？** 查看 [TRACKING.md](references/TRACKING.md)
\`\`\`

**重要指南：**
- 避免深层嵌套引用（保持一级）
- 长文档（>100 行）包含目录
- 在 SKILL.md 中明确引用所有 references

---

## 实战示例

### 示例 1: PDF 编辑 Skill

**需求：** 处理 PDF 文件（旋转、合并、拆分）

**步骤 1: 理解需求**
- 用户场景："旋转这个 PDF"、"合并这些 PDF"
- 触发词：PDF、旋转、合并、拆分

**步骤 2: 规划资源**
- scripts/rotate_pdf.py - 旋转脚本
- scripts/merge_pdf.py - 合并脚本
- scripts/split_pdf.py - 拆分脚本

**步骤 3: 初始化**
\`\`\`bash
scripts/init_skill.py pdf-editor --path skills --resources scripts
\`\`\`

**步骤 4: 编辑**

SKILL.md:
\`\`\`yaml
---
name: pdf-editor
description: PDF 文档处理。支持旋转、合并、拆分。当用户需要处理 PDF 文件时使用。
---

# PDF Editor

## 旋转 PDF
\\\`\\\`\\\`bash
python scripts/rotate_pdf.py input.pdf output.pdf --angle 90
\\\`\\\`\\\`

## 合并 PDF
\\\`\\\`\\\`bash
python scripts/merge_pdf.py file1.pdf file2.pdf output.pdf
\\\`\\\`\\\`
\`\`\`

**步骤 5: 打包**
\`\`\`bash
scripts/package_skill.py skills/pdf-editor
\`\`\`

### 示例 2: BigQuery Skill

**需求：** 查询公司数据库

**步骤 1: 理解需求**
- 用户场景："今天有多少用户登录？"、"本月收入是多少？"
- 触发词：查询、数据库、BigQuery、用户数、收入

**步骤 2: 规划资源**
- references/schema.md - 数据库模式
- references/finance.md - 财务指标定义
- references/sales.md - 销售指标定义

**步骤 3: 初始化**
\`\`\`bash
scripts/init_skill.py bigquery --path skills --resources references
\`\`\`

**步骤 4: 编辑**

SKILL.md:
\`\`\`yaml
---
name: bigquery
description: BigQuery 数据查询。支持用户、财务、销售数据查询。当用户需要查询数据库时使用。
---

# BigQuery Skill

## 数据库结构
查看 [schema.md](references/schema.md) 了解完整的表结构。

## 常见查询

### 用户登录数
\\\`\\\`\\\`sql
SELECT COUNT(*) FROM users WHERE login_date = CURRENT_DATE()
\\\`\\\`\\\`

### 财务指标
详见 [finance.md](references/finance.md)
\`\`\`

references/schema.md:
\`\`\`markdown
# 数据库模式

## users 表
- user_id (STRING) - 用户 ID
- login_date (DATE) - 登录日期
- email (STRING) - 邮箱

## revenue 表
- date (DATE) - 日期
- amount (FLOAT) - 金额
- currency (STRING) - 货币
\`\`\`

**步骤 5: 打包**
\`\`\`bash
scripts/package_skill.py skills/bigquery
\`\`\`

### 示例 3: 前端脚手架 Skill

**需求：** 快速创建前端项目

**步骤 1: 理解需求**
- 用户场景："创建一个 Todo 应用"、"搭建一个仪表板"
- 触发词：创建、前端、网页、应用

**步骤 2: 规划资源**
- assets/template/ - HTML/CSS/JS 模板
- assets/react-template/ - React 模板

**步骤 3: 初始化**
\`\`\`bash
scripts/init_skill.py frontend-scaffold --path skills --resources assets
\`\`\`

**步骤 4: 编辑**

SKILL.md:
\`\`\`yaml
---
name: frontend-scaffold
description: 前端项目脚手架。提供 HTML 和 React 模板。当用户需要创建前端应用时使用。
---

# Frontend Scaffold

## HTML 模板
复制 \\\`assets/template/\\\` 目录作为起点。

## React 模板
复制 \\\`assets/react-template/\\\` 目录作为起点。
\`\`\`

assets/template/index.html:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
    <title>App</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="app"></div>
    <script src="app.js"></script>
</body>
</html>
\`\`\`

**步骤 5: 打包**
\`\`\`bash
scripts/package_skill.py skills/frontend-scaffold
\`\`\`

---

## 常见问题

### Q1: Skill 什么时候会被触发？

**A:** Skill 通过 \`description\` 字段触发。AI 会读取所有 Skill 的 name 和 description，根据用户请求选择最匹配的 Skill。

**提示：**
- description 要包含触发关键词
- 列出具体的使用场景
- 描述支持的操作

### Q2: SKILL.md 应该多长？

**A:** 尽量保持 < 500 行。超过时，拆分内容到 references/。

**原因：**
- 上下文窗口有限
- 只加载必要信息
- 提高响应速度

### Q3: 什么时候用 scripts/ vs references/ vs assets/？

**A:**
- **scripts/** - 重复编写的代码、需要确定性的任务
- **references/** - 需要参考的文档（数据库模式、API 文档）
- **assets/** - 用于输出的文件（模板、图片）

### Q4: 如何测试 Skill？

**A:**
1. 打包 Skill
2. 安装到 OpenClaw
3. 使用真实场景测试
4. 观察 AI 的响应
5. 根据反馈改进

### Q5: Skill 命名有什么规范？

**A:**
- 只用小写字母、数字、连字符
- 动词开头（pdf-rotate, gh-address-comments）
- 简短清晰（< 64 字符）
- 必要时加命名空间（gh-*, linear-*）

### Q6: 如何组织大型 Skill？

**A:** 使用渐进式披露：

1. SKILL.md 保持简洁（概览 + 导航）
2. 详细内容拆分到 references/
3. 按领域或框架组织 references/

示例：
\`\`\`
bigquery-skill/
├── SKILL.md (概览)
└── references/
    ├── finance.md
    ├── sales.md
    └── product.md
\`\`\`

### Q7: 脚本需要测试吗？

**A:** 是的！添加的脚本必须测试：

\`\`\`bash
# 测试脚本
python scripts/rotate_pdf.py test.pdf output.pdf --angle 90

# 检查输出
ls -lh output.pdf
\`\`\`

如果有多个类似脚本，测试代表性样本即可。

### Q8: 如何更新已有的 Skill？

**A:**
1. 修改 Skill 文件（SKILL.md、scripts、references）
2. 重新打包：\`scripts/package_skill.py path/to/skill\`
3. 重新安装到 OpenClaw
4. 测试更新后的功能

### Q9: 可以在 Skill 中使用外部依赖吗？

**A:** 可以，但需要在 SKILL.md 中说明：

\`\`\`markdown
## 依赖

此 Skill 需要以下 Python 包：
\\\`\\\`\\\`bash
pip install PyPDF2 pillow
\\\`\\\`\\\`
\`\`\`

### Q10: 如何分享 Skill？

**A:**
1. 打包 Skill 生成 .skill 文件
2. 分享 .skill 文件给其他用户
3. 其他用户安装到他们的 OpenClaw

---

## 总结

创建 Skill 的关键要点：

1. ✅ **从具体例子开始** - 不要抽象设计
2. ✅ **简洁为王** - 只包含必要信息
3. ✅ **description 是关键** - 决定触发时机
4. ✅ **测试脚本** - 确保代码正常工作
5. ✅ **渐进式披露** - 详细内容放 references/
6. ✅ **迭代改进** - 根据实际使用反馈优化

**记住：** Skill 是为另一个 AI 实例准备的操作手册。包含它需要的信息，省略它已经知道的。

---

## 附录

### 有用的参考文档

OpenClaw 提供了额外的参考指南：

- \`references/workflows.md\` - 多步骤流程和条件逻辑模式
- \`references/output-patterns.md\` - 输出格式和质量标准模式

### 工具脚本位置

- 初始化脚本：\`scripts/init_skill.py\`
- 打包脚本：\`scripts/package_skill.py\`

### 命名示例

好的命名：
- pdf-rotate
- gh-address-comments
- linear-create-issue
- bigquery-finance

不好的命名：
- PDFRotate (大写)
- pdf_rotate (下划线)
- rotate (太泛)
- this-is-a-very-long-skill-name-that-exceeds-reasonable-length (太长)

---

**祝你创建出优秀的 Skill！** 🍊
