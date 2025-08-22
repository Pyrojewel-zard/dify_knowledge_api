# Dify Knowledge Base API Client

基于Dify官方API文档创建的知识库管理客户端，提供了完整的知识库操作功能。

## 功能特性

- **数据集管理** (DatasetManager): 创建、查询、更新、删除知识库
- **文档管理** (DocumentManager): 上传、更新、删除文档，支持文件和文本
- **段落管理** (SegmentManager): 管理文档段落和子块
- **模型管理** (ModelManager): 查询可用的嵌入和检索模型
- **元数据和标签管理** (MetadataManager): 管理标签和元数据

## 安装依赖

```bash
pip install requests
```

## 快速开始

### 1. 环境配置

首先设置必要的环境变量，可以通过以下方式：

**Windows PowerShell (accessapiprivate.ps1):**
```powershell
$env:DIFY_API_BASE="https://llm.bupt.edu.cn/v1"
$env:DIFY_DATASET_ID="your-dataset-id"
$env:DIFY_API_KEY="your-api-key"
```

**Linux/macOS:**
```bash
export DIFY_API_BASE="https://llm.bupt.edu.cn/v1"
export DIFY_DATASET_ID="your-dataset-id"
export DIFY_API_KEY="your-api-key"
```

### 2. 测试连接

在开始使用之前，建议先测试API连接：

```bash
python test_connection.py
```

这个脚本会验证：
- 环境变量是否正确设置
- API客户端是否能正常初始化
- 数据集访问是否正常
- 文档列表功能是否正常
- 模型访问是否正常

### 3. 基本使用

```python
from dify_knowledge_api import DifyKnowledgeAPI

# 初始化客户端
client = DifyKnowledgeAPI(
    api_base="https://your-dify-instance.com/v1",
    api_key="your-api-key"
)

# 创建知识库
ok, dataset = client.datasets.create_dataset(
    name="我的知识库",
    description="用于存储技术文档的知识库"
)

# 上传文档
ok, result = client.documents.create_document_from_file(
    dataset_id="dataset-id",
    file_path="document.md"
)
```

### 2. 数据集管理

```python
# 列出所有数据集
ok, datasets = client.datasets.list_datasets(page=1, limit=20)

# 获取特定数据集详情
ok, dataset = client.datasets.get_dataset("dataset-id")

# 更新数据集
ok, result = client.datasets.update_dataset(
    dataset_id="dataset-id",
    name="新名称",
    description="新描述"
)

# 删除数据集
ok, result = client.datasets.delete_dataset("dataset-id")
```

### 3. 文档管理

```python
# 从文件创建文档
ok, result = client.documents.create_document_from_file(
    dataset_id="dataset-id",
    file_path="document.md",
    indexing_technique="high_quality"
)

# 从文本创建文档
ok, result = client.documents.create_document_from_text(
    dataset_id="dataset-id",
    name="文档名称",
    text="文档内容..."
)

# 列出数据集中的文档
ok, documents = client.documents.list_documents(
    dataset_id="dataset-id",
    page=1,
    limit=20
)

# 获取文档详情
ok, document = client.documents.get_document(
    dataset_id="dataset-id",
    document_id="document-id"
)

# 删除文档
ok, result = client.documents.delete_document(
    dataset_id="dataset-id",
    document_id="document-id"
)
```

### 4. 段落管理

```python
# 创建段落
ok, result = client.segments.create_segments(
    dataset_id="dataset-id",
    document_id="document-id",
    segments=[{"content": "段落内容"}]
)

# 列出文档段落
ok, segments = client.segments.list_segments(
    dataset_id="dataset-id",
    document_id="document-id"
)

# 更新段落
ok, result = client.segments.update_segment(
    dataset_id="dataset-id",
    document_id="document-id",
    segment_id="segment-id",
    content="新内容"
)
```

### 5. 标签管理

```python
# 创建标签
ok, tag = client.metadata.create_tag("技术文档")

# 列出所有标签
ok, tags = client.metadata.list_tags()

# 绑定标签到数据集
ok, result = client.metadata.bind_tags_to_dataset(
    dataset_id="dataset-id",
    tag_ids=["tag-id-1", "tag-id-2"]
)

# 获取数据集标签
ok, dataset_tags = client.metadata.get_dataset_tags("dataset-id")
```

### 6. 知识库检索

```python
# 搜索知识库
ok, results = client.datasets.retrieve_segments(
    dataset_id="dataset-id",
    query="搜索查询",
    retrieval_model={"top_k": 10}
)
```

## 更新后的 upload_markdown.py

原有的 `upload_markdown.py` 已经更新为使用新的API类。主要变化：

- 移除了直接的HTTP请求代码
- 使用 `DifyKnowledgeAPI` 类进行所有操作
- 保持了原有的功能和命令行参数
- 代码更加清晰和易于维护
- **新增了 `--api-base` 参数支持**

### 使用方式

```bash
# 设置环境变量
export DIFY_API_KEY="your-api-key"
export DIFY_DATASET_ID="your-dataset-id"
export DIFY_API_BASE="https://your-dify-instance.com/v1"

# 上传markdown文件
python upload_markdown.py --dir markdown

# 复制缺失的文件
python upload_markdown.py --copy-missing-from-output

# 仅复制文件，不上传
python upload_markdown.py --copy-missing-only

# 使用自定义API基础URL
python upload_markdown.py --api-base "https://custom-dify-instance.com/v1" --dir markdown
```

### 命令行参数

- `--api-base`: Dify API的基础URL (默认: https://llm.bupt.edu.cn/v1)
- `--dataset-id`: 目标数据集ID
- `--api-key`: Dify API密钥
- `--dir`: 包含Markdown文件的目录 (默认: ./markdown)
- `--output-dir`: 源Markdown文件目录 (默认: ./output)
- `--copy-missing-from-output`: 上传前从output目录复制缺失的文件
- `--copy-missing-only`: 仅复制文件，不上传
- `--timeout`: HTTP超时时间（秒）(默认: 120)
- `--indexing-timeout`: 索引超时时间（秒）(默认: 600)
- `--poll-interval`: 轮询间隔（秒）(默认: 5)

## 错误处理

所有API方法都返回 `(success, result)` 元组：

- `success`: 布尔值，表示操作是否成功
- `result`: 成功时返回响应数据，失败时返回错误信息

```python
ok, result = client.datasets.create_dataset("测试知识库")
if ok:
    print(f"创建成功: {result}")
else:
    print(f"创建失败: {result}")
```

## 配置选项

支持通过环境变量配置：

- `DIFY_API_KEY`: API密钥
- `DIFY_DATASET_ID`: 数据集ID
- `DIFY_API_BASE`: API基础URL
- `DIFY_HTTP_TIMEOUT`: HTTP超时时间（秒）
- `DIFY_INDEXING_TIMEOUT`: 索引超时时间（秒）
- `DIFY_POLL_INTERVAL`: 轮询间隔（秒）

## 示例代码

查看 `example_usage.py` 文件了解完整的使用示例。

## 注意事项

1. 确保API密钥有足够的权限
2. 文件上传支持多种格式，建议使用Markdown格式
3. 索引过程可能需要时间，请耐心等待
4. 大量文档上传时建议分批进行
5. 定期检查API使用限制和配额

## 许可证

本项目基于Dify官方API文档创建，遵循相应的使用条款。
