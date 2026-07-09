# AIOps 智能诊断系统

基于本地大模型 + HugeGraph 的智能运维诊断平台，支持从微服务架构文档和故障日志中自动提取实体与关系，构建知识图谱并进行根因分析。

## 功能特性

### 🎯 核心功能

| 功能模块 | 说明 |
|---------|------|
| **架构图谱构建** | 解析架构设计文档（Markdown/YAML），自动提取微服务节点和调用关系，构建静态本体图谱 |
| **故障日志融合** | 解析故障日志（带 TraceID），提取时序链路，动态挂载到本体图谱，实现动静融合 |
| **HDFS 日志预处理** | 将 HDFS 日志转换为 Cypher 语句，支持导出到 Neo4j 进行离线分析 |

### 🔧 技术特性

- **本地大模型接入**：支持 llama.cpp、LM Studio 等本地推理服务，无需联网
- **图数据库驱动**：基于 HugeGraph REST API，支持节点去重和关系补全
- **可视化交互**：Streamlit 聊天界面，支持文件上传和实时进度展示
- **自动 Schema 初始化**：首次启动自动创建图模式（顶点标签、边标签、属性）

## 技术栈

| 层次 | 技术 | 版本要求 |
|-----|------|---------|
| AI 解析层 | LangChain、OpenAI API 兼容接口 | - |
| 业务逻辑层 | Python 3.10+ | - |
| 数据访问层 | HugeGraph REST API | 1.x |
| 前端交互 | Streamlit | 1.x |
| 依赖管理 | pip | - |

## 目录结构

```
code/
├── demo/                    # 核心服务模块
│   ├── analyzer.py          # AI 解析层 - 大模型交互封装
│   ├── database.py          # 数据访问层 - HugeGraph 客户端
│   ├── service.py           # 业务逻辑层 - 图谱构建服务
│   ├── chat_ui.py           # 前端交互 - Streamlit 聊天界面
│   ├── test_hg.py           # 测试脚本
│   ├── err.log              # 错误日志
│   └── 系统架构设计文档.md    # 示例架构文档
├── export_cypher.py         # HDFS 日志转 Cypher 工具（独立模块）
├── HDFS.log                 # 示例 HDFS 日志文件
├── prompt.md                # AIOps Agent 提示词模板（基于 Neo4j 的自然语言故障诊断，扩展功能）
└── README.md                # 项目说明文档
```

## 快速开始

### 前置条件

1. **启动本地大模型服务**（端口 1234）
   - 推荐使用 LM Studio 或 llama.cpp server
   - 确保模型支持 JSON 输出格式

2. **启动 HugeGraph 服务**（端口 8080）
   ```bash
   # 下载并启动 HugeGraph Server
   # 访问 http://127.0.0.1:8080 验证服务状态
   ```

### 安装依赖

```bash
cd code
pip install -r requirements.txt
```

> 如无 requirements.txt，可手动安装：
> ```bash
> pip install streamlit requests langchain langchain-openai
> ```

### 运行系统

```bash
cd code/demo
streamlit run chat_ui.py
```

### 使用流程

1. 在浏览器中打开 `http://localhost:8501`
2. 上传架构文档（如 `demo/系统架构设计文档.md`）或故障日志文件（如 `demo/err.log` 或 `HDFS.log`）
3. 点击发送，系统自动完成：
   - 大模型解析 → 提取实体与关系
   - 图数据库写入 → 构建知识图谱
   - 结果展示 → 查看 JSON 数据和执行日志

> **快速体验**：项目已包含示例文件 `demo/系统架构设计文档.md`、`demo/err.log` 和 `HDFS.log`，可直接上传测试。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit 前端                        │
│              (chat_ui.py - 聊天交互界面)                  │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                  业务逻辑层                              │
│          (service.py - GraphBuilderService)             │
│  ┌─────────────────────────────────────────────────┐   │
│  │  build_ontology_graph()  →  构建静态本体图谱      │   │
│  │  build_mechanism_graph() →  构建动态故障图谱      │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
┌─────────▼─────────┐                 ┌─────────▼─────────┐
│   AI 解析层       │                 │   数据访问层       │
│ (analyzer.py)    │                 │ (database.py)     │
│                   │                 │                   │
│ LangChain + LLM  │                 │ HugeGraph REST API│
│ - 架构文档解析    │                 │ - Schema 初始化   │
│ - 日志链路提取    │                 │ - 顶点/边写入     │
└───────────────────┘                 └───────────────────┘
```

## 图数据模型

### 顶点标签

| 标签 | 主键 | 属性 |
|-----|------|------|
| Service | name | name, layer_type |
| LogEvent | trace_id + timestamp | trace_id, timestamp, level, message |

### 边标签

| 标签 | 起点 | 终点 | 语义 |
|-----|------|------|------|
| CALLS | Service | Service | 服务调用关系 |
| OCCURRED_ON | LogEvent | Service | 日志发生在服务上 |
| PRECEDES | LogEvent | LogEvent | 日志时序关系 |

## 独立工具

### HDFS 日志转 Cypher

`export_cypher.py` 是一个独立工具，用于将 HDFS 日志转换为 Neo4j Cypher 语句：

```bash
python export_cypher.py
```

输出文件：`cypher_commands.txt`

> 注意：此工具面向 Neo4j，与主流程的 HugeGraph 方向不同，用于离线分析场景。

## 注意事项

1. **Schema 初始化**：首次运行会自动创建 Schema，重复运行可能提示已存在，属正常现象
2. **网络要求**：本地大模型和 HugeGraph 服务需运行在同一网络，确保端口可达
3. **日志格式**：故障日志需包含 TraceID 和时间戳，以便正确提取链路
4. **模型兼容性**：推荐使用支持结构化输出（JSON）的模型，如 Llama 3 系列

## License

MIT License
