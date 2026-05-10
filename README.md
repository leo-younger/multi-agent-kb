# 多智能体协同知识库系统

基于多智能体协同的企业知识库 MVP 系统，支持文档上传、实体关系抽取、向量检索、知识图谱可视化和智能问答。

## 核心功能

| 功能 | 说明 |
|------|------|
| 文档解析 | 上传 PDF/Word/TXT 文件，自动解析文本并切片（500字/片，100字重叠） |
| 实体抽取 | 从文档切片中提取人员、部门、系统、模块、接口等实体及关系 |
| 向量入库 | 使用 sentence-transformers 生成文本向量，存入内存向量库 |
| 知识图谱 | 实体和关系存入 Neo4j，ECharts 关系图可视化展示 |
| 智能问答 | 多智能体（总控/检索/拓扑/总结）协同检索推理，给出带逻辑的答案 |

## 技术架构

```
┌─────────────────────────────────────────────────┐
│                Vue3 前端                         │
│       Element Plus + ECharts                     │
├──────────────┬───────────────┬──────────────────┤
│  文档管理     │  智能问答      │  知识图谱         │
└──────┬───────┴───────┬───────┴────────┬─────────┘
       │               │                │
       ▼               ▼                ▼
┌─────────────────────────────────────────────────┐
│              FastAPI 后端                        │
│  /api/upload  /api/extract  /api/embed  /api/chat│
├──────────────┬──────────────┬───────────────────┤
│  文档解析     │  实体抽取     │  Embedding         │
│  PyPDF2      │  规则匹配     │  sentence-         │
│  python-docx │  mock 数据    │  transformers      │
├──────────────┴──────────────┴───────────────────┤
│      numpy 向量检索       │      Neo4j           │
│     (内存余弦相似度)       │    (图数据库)        │
└─────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 + Vite |
| UI 组件 | Element Plus |
| 图谱可视化 | ECharts 5 |
| 后端框架 | Python FastAPI |
| 文档解析 | PyPDF2 + python-docx |
| Embedding | sentence-transformers (all-MiniLM-L6-v2) |
| 向量检索 | numpy 余弦相似度（内存模式） |
| 图数据库 | Neo4j 5 |
| 容器化 | Docker Compose |

## 项目结构

```
multi-agent-kb/
├── backend/                    # Python 后端
│   ├── main.py                 # FastAPI 入口 + 路由
│   ├── requirements.txt        # Python 依赖
│   ├── models/
│   │   └── schemas.py          # Pydantic 数据模型
│   ├── services/
│   │   ├── document_parser.py  # 文档解析 + 文本切片
│   │   ├── entity_extractor.py # 实体关系抽取（规则+mock）
│   │   ├── embedding.py        # Embedding 服务
│   │   ├── vector_store.py     # numpy 向量检索
│   │   ├── graph_store.py      # Neo4j 图数据库操作
│   │   └── agents.py           # 多智能体协同（asyncio 并行）
│   └── tests/
│       └── test_optimizations.py  # 15 个单元测试
├── frontend/                   # Vue3 前端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js             # Vue3 入口
│       ├── App.vue             # 主页面（侧边栏+内容区）
│       └── components/
│           ├── DocumentManager.vue  # 文档管理
│           ├── ChatInterface.vue    # 智能问答
│           └── KnowledgeGraph.vue   # 知识图谱
├── test-data/                  # 测试文档
│   ├── 系统架构说明.txt
│   ├── 运维手册.txt
│   └── API接口文档.txt
├── docker-compose.yml          # Neo4j 容器配置
└── README.md
```

## 快速开始

### 1. 启动 Neo4j 数据库

```bash
docker-compose up -d
```

Neo4j 管理界面：http://localhost:7474
- 用户名：`neo4j`
- 密码：`password123`

等待约 30 秒启动完成。

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

后端运行在 http://localhost:8000
API 文档：http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

### 4. 使用流程

1. 打开 http://localhost:5173
2. **文档管理**：上传 `test-data/` 目录下的测试文件 → 点击「开始抽取」→ 点击「开始入库」
3. **智能问答**：输入问题（如"张三负责什么模块？"），查看 Agent 协同过程
4. **知识图谱**：查看实体关系的可视化图谱，支持拖拽和缩放

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 健康检查 |
| POST | `/api/upload` | 文档上传（multipart/form-data） |
| POST | `/api/extract` | 实体关系抽取 |
| POST | `/api/embed` | 向量入库 |
| POST | `/api/chat?question=xxx` | 智能问答 |
| GET | `/api/graph` | 知识图谱数据 |
| GET | `/api/docs` | 已上传文档列表 |

## 多智能体协同流程

```
用户提问
  │
  ▼
┌─────────────┐
│  总控 Agent  │  分析问题类型，调度其他 Agent
└──────┬──────┘
       │
  ┌────┴────┐
  ▼         ▼
┌────────┐ ┌────────┐
│检索 Agent│ │拓扑 Agent│  ← asyncio.gather 并行执行
│向量检索  │ │图谱查询  │
└────┬───┘ └────┬───┘
     │          │
     └────┬─────┘
          ▼
    ┌───────────┐
    │ 总结 Agent │  综合信息生成答案
    └───────────┘
```

## 测试

```bash
cd backend
python -m pytest tests/ -v
```

15 个测试用例覆盖：

| 测试组 | 用例数 | 覆盖内容 |
|--------|--------|---------|
| 文档切片 | 3 | overlap 防护、正常切片、单切片 |
| Embedding | 3 | mock 向量、确定性、维度 |
| 实体抽取 | 3 | 去重、词典匹配、默认回退 |
| 图谱查询 | 2 | 空关键词、UNWIND 优化 |
| Agent 流水线 | 4 | 问题分析、关键词提取、回退、async 流水线 |

## 测试数据

`test-data/` 目录提供 3 个测试文档，包含以下实体和关系：

| 实体类型 | 实体 |
|---------|------|
| 人员 | 张三、李四、王五、赵六、刘七 |
| 部门 | 技术部、运维部、产品部、数据部 |
| 系统 | 订单系统、用户系统、支付系统、库存系统、日志系统 |
| 模块 | 知识库模块、解析服务、网关模块、认证模块、调度模块 |
| 接口 | 用户查询接口、订单创建接口、数据同步接口、文件上传接口 |

## Neo4j 配置

| 配置项 | 值 |
|--------|-----|
| Web 管理界面 | http://localhost:7474 |
| Bolt 协议地址 | bolt://localhost:7687 |
| 用户名 | neo4j |
| 密码 | password123 |

可在 `backend/services/graph_store.py` 中修改连接配置。

## 技术亮点

1. **多智能体并行协同**：检索 Agent 和拓扑 Agent 通过 `asyncio.gather` 并行执行，缩短响应时间
2. **双存储架构**：向量检索 + 图谱查询，实现语义检索与关系推理结合
3. **本地 Embedding**：sentence-transformers 本地推理，不依赖外部 API；加载失败自动降级为 mock 模式
4. **知识图谱可视化**：ECharts force-directed 布局，SVG 分类图标，支持节点拖拽和详情浮层
5. **完整 MVP 流程**：上传 → 解析 → 抽取 → 入库 → 问答 → 可视化，全链路打通
6. **健壮性保障**：overlap 参数防护、embedding 加载竞态修复、XSS 防护

## 注意事项

- Neo4j 默认密码为 `password123`，可在 `graph_store.py` 中修改
- Embedding 模型使用 `hf-mirror.com` 国内镜像下载，首次加载约 80MB，如下载失败自动降级为 mock 模式
- 向量检索使用 numpy 余弦相似度（内存模式），重启后数据需重新入库
- 本项目为 MVP 演示，实体抽取使用规则匹配，生产环境建议接入大模型

## 许可证

MIT
