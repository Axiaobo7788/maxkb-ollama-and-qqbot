下面给你一套**端到端落地方案**：用 **Ollama** 跑本地大模型、用 **MaxKB** 作为知识库/RAG与应用编排、用 **Python（FastAPI）** 做业务中台服务层、前端以 **QQ 机器人**（官方 QQ 机器人或 OneBot 生态）来呈现与交互。我把关键架构、部署步骤、核心代码样例、以及常见坑都整理好了，照着做即可上线原型。

---

## 一、总体架构（业务中台视角）

- **模型层（LLM/Embedding/Reranker）**：  
  在本机或服务器通过 **Ollama** 运行中文能力强的开源模型（如 Qwen3 8B/14B/30B），并可同时启用 **Embedding / Reranker** 模型，给 RAG 提升检索与重排质量。[1](https://ollama.com/library/qwen3)[2](https://github.com/ollama/ollama/blob/main/docs/api.md)[3](https://apidog.com/blog/qwen-3-embedding-reranker-ollama/)

- **知识层（RAG/工作流/应用）**：  
  用 **MaxKB** 构建知识库、做文档拆分+向量化、配置应用（可渐进到工作流/Agent），并**对接本地 Ollama** 以模型中立方式输出答案。[4](https://maxkb.cn/docs/v2/)[5](https://github.com/1panel-dev/MaxKB)[6](https://docs.maxkb.pro/user_manual/model/ollama_model/)

- **业务中台服务层（Python/FastAPI）**：  
  统一封装会话管理、权限/配额、提示词模板、工具调用（如检索→重排→拼接上下文→调用 LLM）、埋点监控与日志，向上暴露 REST/WebSocket API。此层通过 **Ollama REST 或 Python SDK** 调模型，通过 **MaxKB Open API** 检索知识库。[2](https://github.com/ollama/ollama/blob/main/docs/api.md)[7](https://pypi.org/project/ollama/)[8](https://fit2cloud.com/maxkb/download/introduce-maxkb_202503.pdf)

- **前端呈现层（QQ 机器人）**：  
  两种接入路线：  
  1) **官方 QQ 机器人**（QQ 开放平台）：用 **NoneBot2** 的 QQ 适配器接入沙箱/群聊；  
  2) **OneBot v11 生态**（LLOneBot / NapCat / go-cqhttp 等）：用 **NoneBot2** + OneBot v11 适配器与你的中台服务交互。[9](https://blog.csdn.net/weixin_58403216/article/details/144715878)[10](https://www.bilibili.com/opus/864496617981476867)[11](https://github.com/nonebot/nonebot)[12](https://github.com/botuniverse/onebot-11)[13](https://www.kafuuchino.fun/archives/30)[14](https://blog.csdn.net/changwenpeng/article/details/144649045)

---

## 二、环境与部署（一步步）

### 1) 安装并启动 Ollama（含模型）
```bash
# Linux / macOS
curl -fsSL https://ollama.com/install.sh | sh
# Windows PowerShell
iwr https://ollama.com/install.ps1 -useb | iex

# 运行服务并绑定外网/容器可访问地址
# （很关键：让 MaxKB / 其它容器能访问，不要仅监听 localhost）
# systemd 环境示例：
# /etc/systemd/system/ollama.service 中加入：
Environment="OLLAMA_HOST=0.0.0.0:11434"
```
拉取并测试模型（示例选 Qwen3）：
```bash
ollama pull qwen3:8b        # 或 qwen3:4b/qwen3:14b/...
ollama run qwen3:8b
```
Ollama 提供完整 REST API（`/api/generate`、`/api/chat` 等）与 Python 客户端（`pip install ollama`），支持同步/流式、embed、list、ps 等。[2](https://github.com/ollama/ollama/blob/main/docs/api.md)[7](https://pypi.org/project/ollama/)[1](https://ollama.com/library/qwen3)  
如做高质量 RAG，建议再拉取 **Qwen3 embedding / reranker** 变体并在中台中调用。[3](https://apidog.com/blog/qwen-3-embedding-reranker-ollama/)

### 2) 部署 MaxKB（Docker）
```bash
# 官方镜像（示例）
docker run -d --name=maxkb --restart=always \
  -p 8080:8080 \
  -v ~/.maxkb:/opt/maxkb \
  1panel/maxkb

# 初始账号：admin / 密码：MaxKB@123..
# 登录 http://<server>:8080 后可修改
```
MaxKB 面向企业知识库与 RAG，支持上传文档/爬取网页、向量化、工作流/函数库/MCP 工具调用、以及无代码嵌入第三方系统。后端基于 Python/Django + PostgreSQL/pgvector。[5](https://github.com/1panel-dev/MaxKB)[4](https://maxkb.cn/docs/v2/)

### 3) MaxKB 对接 Ollama（关键点）
在「系统设置 → 模型设置 → 添加模型」选择 **供应商：Ollama**，填写：模型类型（LLM/向量/重排/视觉）、基础模型名（如 `qwen3:8b`），以及 **API 域名**（Ollama 服务地址）。**注意不要用 `localhost/127.0.0.1`**，容器之间请用主机 IP 或 `host.docker.internal:11434`。[6](https://docs.maxkb.pro/user_manual/model/ollama_model/)[15](https://maxkb.cn/docs/v1/user_manual/model/ollama_model/)[16](https://bbs.fit2cloud.com/t/topic/4165)[17](https://juejin.cn/post/7452355150143029298)

> MaxKB 文档与社区明确：旧版需 `/v1` 路径，新版直接 `http://IP:11434`；且必须在 MaxKB 容器内能连通 Ollama，“Ollama is running”。[16](https://bbs.fit2cloud.com/t/topic/4165)

### 4) QQ 机器人前端（选一条路线即可）

**路线 A：官方 QQ 机器人（推荐合规）**  
- 在 QQ 开放平台创建应用与沙箱群；  
- 用 **NoneBot2** 选择「QQ 官方机器人」适配器，配置 `id/token/secret` 与 websocket 心跳；按文档/教程跑通 Echo。[9](https://blog.csdn.net/weixin_58403216/article/details/144715878)[10](https://www.bilibili.com/opus/864496617981476867)

**路线 B：OneBot v11（社区生态丰富）**  
- 安装 **LLOneBot / NapCat / go-cqhttp** 等 OneBot 实现（可正/反向 WebSocket）；  
- 用 **NoneBot2** 的 OneBot v11 适配器连接；官方标准见 OneBot 11。[13](https://www.kafuuchino.fun/archives/30)[14](https://blog.csdn.net/changwenpeng/article/details/144649045)[18](https://docs.go-cqhttp.org/guide/quick_start.html)[12](https://github.com/botuniverse/onebot-11)

---

## 三、业务中台（Python/FastAPI）最小可用样例

> 作用：统一“RAG + 对话”的业务编排；对上给 QQ 机器人一个简单 `/chat`；内部先查 MaxKB（检索/重排），再把上下文喂给 Ollama 的 `/api/chat`；附带权限/日志。

### 1) 依赖与项目结构
```bash
pip install fastapi uvicorn[standard] httpx ollama python-dotenv
```

```
app/
├─ main.py           # FastAPI入口
├─ rag.py            # 调MaxKB检索/重排
├─ llm.py            # 调Ollama（Python SDK 或 REST）
├─ config.py         # 配置/密钥/模型名等
└─ logs/
```

### 2) 代码（示例）
**llm.py**：通过官方 Python SDK（也可用 REST）
```python
# llm.py
from ollama import Client

client = Client(host="http://<ollama_ip>:11434")  # 不要用localhost
MODEL = "qwen3:8b"

def chat(messages, stream=False, options=None):
    return client.chat(model=MODEL, messages=messages, stream=stream, options=options)
```
> Ollama Python SDK支持 `chat/generate/embed/list/ps/pull` 等全套能力；也支持异步与流式。[7](https://pypi.org/project/ollama/)

**rag.py**：调用 MaxKB 的开放 API（伪示例）
```python
# rag.py
import httpx
from typing import List

MAXKB_BASE = "http://<maxkb_ip>:8080"
MAXKB_API_KEY = "<your_key>"
APP_ID = "<your_app_id>"  # 在MaxKB中创建应用

def kb_search(query: str, top_k: int = 5) -> List[dict]:
    # 具体 Open API 路径以官方文档为准（下面为示意）
    url = f"{MAXKB_BASE}/api/v1/apps/{APP_ID}/search"
    headers = {"Authorization": f"Bearer {MAXKB_API_KEY}"}
    resp = httpx.post(url, json={"query": query, "top_k": top_k}, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json().get("hits", [])
```
> MaxKB 提供 REST API/嵌入能力，用于第三方系统集成与应用调用，细节参见官方产品文档/版本对比说明。[8](https://fit2cloud.com/maxkb/download/introduce-maxkb_202503.pdf)

**main.py**：业务编排（RAG→LLM）
```python
# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from rag import kb_search
from llm import chat

app = FastAPI()

class ChatReq(BaseModel):
    user_id: str
    text: str

SYSTEM_PROMPT = (
    "你是企业业务中台的AI助手。回答要准确、引用来源；"
    "当问题涉及公司知识，先检索知识库再回答；无法确定时请说明不确定并给出建议。"
)

@app.post("/chat")
def chat_api(req: ChatReq):
    # 1) RAG 检索
    hits = kb_search(req.text, top_k=5)
    context = "\n\n".join([f"[{i+1}] {h['text']}" for i, h in enumerate(hits)])
    citations = "\n".join([f"[{i+1}] {h.get('source','')}" for i, h in enumerate(hits)])

    # 2) 组织对话消息
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": f"问题：{req.text}\n\n已检索到的参考:\n{context}\n\n请结合参考作答。"},
    ]

    # 3) 调用 Ollama
    resp = chat(messages=messages, stream=False, options={"temperature": 0.2})
    answer = resp["message"]["content"]

    return {
        "answer": answer,
        "citations": citations,
        "kb_hits": len(hits),
    }
```
> Ollama REST/SDK 的对话接口 `chat` 支持流式与额外选项（温度、系统提示、模板等）；也可改为 `/api/generate` 简化一问一答。[2](https://github.com/ollama/ollama/blob/main/docs/api.md)[7](https://pypi.org/project/ollama/)

---

## 四、QQ 机器人把消息转发到中台

### 路线 A：NoneBot2 + 官方 QQ 机器人适配器
**bot.py（示例）**
```python
import nonebot
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.plugin import on_message
import httpx

nb = nonebot.get_driver()
nb.register_adapter(QQAdapter)
forward = on_message(priority=10, block=False)

API = "http://<gateway_ip>:8000/chat"

@forward.handle()
async def _(event):
    text = event.get_message().extract_plain_text().strip()
    if not text:
        return
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(API, json={"user_id": str(event.get_user_id()), "text": text})
        data = r.json()
    await forward.finish(f"{data['answer']}\n\n引用：\n{data['citations']}")
```
> NoneBot2 官方 QQ 机器人适配器与沙箱/群聊的配置流程详见教程与文档。[9](https://blog.csdn.net/weixin_58403216/article/details/144715878)[10](https://www.bilibili.com/opus/864496617981476867)

### 路线 B：NoneBot2 + OneBot v11 适配器（配 LLOneBot/NapCat/go-cqhttp）
在 LLOneBot/NapCat/go-cqhttp 中启用**正向 WebSocket**（如 `ws://127.0.0.1:6700`），在 NoneBot2 侧设置 `ONEBOT_WS_URLS` 即可，消息处理逻辑同上。[13](https://www.kafuuchino.fun/archives/30)[14](https://blog.csdn.net/changwenpeng/article/details/144649045)[18](https://docs.go-cqhttp.org/guide/quick_start.html)  
OneBot v11 的事件与 API 规范参考标准文档。[12](https://github.com/botuniverse/onebot-11)

---

## 五、Docker Compose（可选，一键编排）

```yaml
version: "3.9"
services:
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    volumes:
      - ollama:/root/.ollama

  maxkb:
    image: 1panel/maxkb:latest
    ports: ["8080:8080"]
    volumes:
      - maxkb:/opt/maxkb
    restart: always

  gateway:
    build: ./gateway        # 你的 FastAPI 服务 Dockerfile
    ports: ["8000:8000"]
    environment:
      - OLLAMA_URL=http://ollama:11434
      - MAXKB_URL=http://maxkb:8080
    depends_on: [ollama, maxkb]

  nonebot:
    build: ./qqbot          # 你的 NoneBot 项目 Dockerfile
    ports: ["7070:7070"]
    depends_on: [gateway]

volumes:
  ollama:
  maxkb:
```
> 通过 `OLLAMA_HOST=0.0.0.0` 保证外部/容器可访问；MaxKB 中添加 Ollama 模型时请使用服务名或宿主 IP，不要写 localhost。[16](https://bbs.fit2cloud.com/t/topic/4165)

---

## 六、模型选型与效果提升建议

- **中文综合对话**：优先试 **Qwen3-8B/14B**；算力足时试 30B/32B。[1](https://ollama.com/library/qwen3)  
- **RAG 策略**：向量检索 + 交叉编码重排（Qwen3 reranker）并控制温度、加入“必须结合引用回答”的系统提示。[3](https://apidog.com/blog/qwen-3-embedding-reranker-ollama/)  
- **本地化部署优势**：隐私、延迟、成本可控；Ollama 提供了简洁 CLI/REST/SDK。[2](https://github.com/ollama/ollama/blob/main/docs/api.md)[7](https://pypi.org/project/ollama/)  
- **MaxKB 优势**：开箱即用的知识库/RAG与工作流、模型中立、嵌入第三方系统与开放 API。[4](https://maxkb.cn/docs/v2/)[5](https://github.com/1panel-dev/MaxKB)

---

## 七、常见坑与排障

1) **MaxKB “API 域名不可用”**：  
   - 不要用 `127.0.0.1/localhost`；改用宿主机 IP 或 `host.docker.internal:11434`；  
   - 在容器中 `curl http://<ollama_ip>:11434` 应返回 “Ollama is running”。  
   - 旧版可能要求 `/v1` 路径；新版直接到端口即可。[16](https://bbs.fit2cloud.com/t/topic/4165)

2) **Ollama 监听范围**：  
   设置 `OLLAMA_HOST=0.0.0.0:11434` 或在 Docker 中暴露端口，确保跨容器访问。[2](https://github.com/ollama/ollama/blob/main/docs/api.md)

3) **QQ 机器人连通**：  
   官方 QQ 路线需在开放平台申请并配置沙箱；OneBot 路线需正确配置 WebSocket（正/反向）与 token。[9](https://blog.csdn.net/weixin_58403216/article/details/144715878)[10](https://www.bilibili.com/opus/864496617981476867)[18](https://docs.go-cqhttp.org/guide/quick_start.html)

---

## 八、上线与治理（中台必备）

- **权限/配额**：基于 user_id 做频控与额度；  
- **日志与指标**：记录命中片段、响应时延、被重排文档、token 统计；  
- **安全与合规**：过滤敏感词，明确免责声明与知识来源；  
- **多租户**：MaxKB 分库/分应用，后端加租户隔离；  
- **可灰度**：按群/用户开关不同模型与提示词策略。

---

## 九、你可以直接复用的清单

- **Ollama**：安装、拉取模型、REST/SDK 用法。[2](https://github.com/ollama/ollama/blob/main/docs/api.md)[7](https://pypi.org/project/ollama/)  
- **Qwen3（适合中文）**：模型列表与大小/上下文；embedding/reranker用法。[1](https://ollama.com/library/qwen3)[3](https://apidog.com/blog/qwen-3-embedding-reranker-ollama/)  
- **MaxKB**：文档与 GitHub（部署、对接 Ollama、RAG/工作流/应用、Open API）。[4](https://maxkb.cn/docs/v2/)[5](https://github.com/1panel-dev/MaxKB)[6](https://docs.maxkb.pro/user_manual/model/ollama_model/)  
- **QQ 机器人**：NoneBot2（官方 QQ / OneBot v11）、OneBot 标准、生态实现。[9](https://blog.csdn.net/weixin_58403216/article/details/144715878)[10](https://www.bilibili.com/opus/864496617981476867)[11](https://github.com/nonebot/nonebot)[12](https://github.com/botuniverse/onebot-11)

---

## 接下来我需要你两点信息，好给出**贴合你场景**的落地细则与代码：

1) 你的**业务场景**是什么？（例如客服质检、内部规章问答、流程审批助手、报表问答等）  
2) 你预计的**并发与部署环境**？（单机/容器，多人群聊还是点对点，是否有 GPU）  
3) QQ 机器人你更偏向 **官方 QQ 适配** 还是 **OneBot v11 生态**？

有了这些，我可以把上面的中台逻辑（提示词、RAG 策略、会话态、配额与日志）按你的场景做成**可跑的模板仓库**并发你。
