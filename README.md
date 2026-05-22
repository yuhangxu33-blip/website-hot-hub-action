# Website Hot Hub - 自动化热榜聚合器

[![GitHub Actions Workflow Status](https://github.com/Snychng/website-hot-hub/actions/workflows/schedule-update.yml/badge.svg)](https://github.com/Snychng/website-hot-hub/actions/workflows/schedule-update.yml)

这是一个自动化的热榜信息聚合项目。它通过 GitHub Actions 定时执行，抓取多个主流平台（如36氪、掘金、GitHub Trending）的每日热榜，将数据以结构化的 JSON 格式存档，并通过一个精美的、可交互的飞书卡片消息，将最新的热榜简报推送到指定的群聊中。

## ✨ 主要特性

*   **🚀 完全自动化**: 无需人工干预，每半小时自动抓取、更新并推送最新热榜。
*   **🔧 结构化数据存储**: 每日热榜数据以干净的 JSON 格式独立存档在 `raw/` 目录下，便于后续的数据分析和使用。
*   **🎨 精美的飞书通知**: 使用飞书消息卡片进行推送，内容结构清晰、排版美观，并包含可交互的链接和跳转按钮。
*   **💪 高度可扩展**: 架构设计清晰，新增一个热榜来源只需“两步走”，对现有代码侵入性极低。
*   **☁️ 零服务器成本**: 完全基于免费的 GitHub Actions 运行，无需自己部署和维护服务器。

## 🤖 工作流程

本项目的核心驱动是 GitHub Actions，其工作流程如下：

1.  **定时触发 (Schedule)**: `.github/workflows/schedule-update.yml` 文件配置了一个定时任务，每半小时自动启动一次工作流。
2.  **环境准备 (Setup)**: Action 自动准备好 Python 运行环境并安装所需的依赖库。
3.  **执行 Python 脚本 (`main.py`)**:
    *   主程序并发调用各个平台的爬虫模块 (`website_*.py`)。
    *   每个爬虫模块负责抓取对应平台的热榜数据，并将其与当天已有的数据合并、去重。
    *   最终，每个平台最新的热榜数据被保存为一个独立的 JSON 文件（例如 `raw/36kr/2025-09-10.json`）。
4.  **提交代码变更 (Git Push)**: Action 检查 `raw/` 目录下是否有文件变动。如果有，则自动将这些新的数据文件提交并推送到代码仓库。
5.  **构建并发送通知 (Feishu Notification)**:
    *   如果检测到代码变更，Action 会继续执行。
    *   它会从刚刚提交的最新 `commit` 中，直接读取各个平台的 `.json` 数据文件。
    *   利用 `jq` 工具，将这些结构化的 JSON 数据动态地转换成格式化的 Markdown 列表。
    *   最后，将这些列表组装成一个精美的飞书消息卡片，并通过 Webhook 发送到一个或多个飞书群。

## 📁 项目结构

```
.
├── .github/workflows/
│   └── schedule-update.yml  # 核心！GitHub Action 配置文件，负责调度、执行和通知
├── raw/                     # 存储每日抓取的原始JSON数据，按平台和日期组织
│   ├── 36kr/
│   │   └── 2025-09-10.json
│   ├── juejin/
│   └── github/
├── main.py                  # 主程序入口，负责并发调度各个爬虫任务
├── utils.py                 # 通用工具函数（如文件读写、时间处理）
├── website_36kr.py          # 36氪热榜的爬虫模块
├── website_juejin.py        # 掘金热榜的爬虫模块
└── website_github.py        # GitHub Trending 的爬虫模块
```

## 🛠️ 如何配置和运行

如果您想 Fork 本项目并运行自己的版本，请遵循以下步骤：

1.  **Fork 项目**: 将本项目 Fork 到您自己的 GitHub 账户下。

2.  **配置 Python 环境 (本地测试用)**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置 GitHub Secrets**:
    为了让 Action 能够向您的飞书机器人发送通知，您需要在 Fork 后的仓库中配置 Secrets。
    *   前往您的仓库页面，点击 `Settings` > `Secrets and variables` > `Actions`。
    *   点击 `New repository secret`，创建以下一个或两个 Secrets：
        *   `FEISHU_WEBHOOK_URL`: 您的主要飞书机器人的 Webhook 地址。
        *   `FEISHU_WEBHOOK_URL_TEST` (可选): 您的测试飞书机器人的 Webhook 地址。

4.  **启用 GitHub Actions**:
    *   前往您的仓库页面，点击 `Actions` 标签页。
    *   如果出现一个 "I understand my workflows, go ahead and enable them" 的按钮，请点击它以启用。
    *   工作流将根据 `.github/workflows/schedule-update.yml` 中定义的 `schedule` 自动开始运行。您也可以通过 `workflow_dispatch` 手动触发一次来立即测试。

## 🧩 如何扩展 (新增一个热榜来源)

本项目的架构使得添加新的热榜来源变得非常简单。假设您想新增一个“知乎热榜”，只需遵循以下步骤：

### 第一步：创建新的爬虫模块 (`website_zhihu.py`)

1.  在项目根目录创建一个新文件，例如 `website_zhihu.py`。
2.  参考 `website_36kr.py` 的结构，实现一个 `WebSiteZhiHu` 类。
3.  这个类至少需要包含一个 `run(self)` 方法，该方法的核心职责是：
    *   抓取知乎热榜的原始数据。
    *   将其清洗为您期望的、统一的 JSON 格式：`[{"title": "...", "url": "..."}, ...]`。
    *   将最终的 JSON 数据写入到对应的文件中，例如 `raw/zhihu/YYYY-MM-DD.json`。
    *   成功后返回一个字典，例如 `{"success": True, "data_count": 50}`。

### 第二步：集成到 `main.py`

打开 `main.py` 文件，将您新创建的爬虫模块集成进去。

```python
# main.py

# 1. 导入你的新模块
from website_zhihu import WebSiteZhiHu 
# ... 其他 import

def main():
    # ...
    all_websites = [
        (WebSite36Kr(), "36KR"),
        (WebSiteGitHub(), "GITHUB"),
        (WebSiteJueJin(), "JUEJIN"),
        (WebSiteZhiHu(), "ZHIHU"), # <--- 2. 在这里添加你的新实例
    ]
    # ...
```

### 第三步：更新 GitHub Action (`schedule-update.yml`)

打开 `.github/workflows/schedule-update.yml` 文件，让它能够处理并展示来自“知乎”的数据。

1.  **找到步骤 8 (`Build and Send Notifications ...`)**

2.  **在 `run` 脚本中，复制并修改以下三处：**

    ```yaml
    # ... yml 文件内容 ...
    run: |
      # ... (json_to_markdown_list 函数定义) ...

      # [修改点 1: 增加 JSON 文件读取]
      CURRENT_DATE=$(date +%Y-%m-%d)
      KR_JSON=$(git show HEAD:./raw/36kr/$CURRENT_DATE.json 2>/dev/null || echo "[]")
      JUEJIN_JSON=$(git show HEAD:./raw/juejin/$CURRENT_DATE.json 2>/dev/null || echo "[]")
      GITHUB_JSON=$(git show HEAD:./raw/github/$CURRENT_DATE.json 2>/dev/null || echo "[]")
      ZHIHU_JSON=$(git show HEAD:./raw/zhihu/$CURRENT_DATE.json 2>/dev/null || echo "[]") # <--- 新增
      UPDATE_TIME=$(date '+%Y年%m月%d日 %H:%M')

      # [修改点 2: 增加 Markdown 转换]
      KR_MD=$(echo "$KR_JSON" | json_to_markdown_list)
      JUEJIN_MD=$(echo "$JUEJIN_JSON" | json_to_markdown_list)
      GITHUB_MD=$(echo "$GITHUB_JSON" | json_to_markdown_list)
      ZHIHU_MD=$(echo "$ZHIHU_JSON" | json_to_markdown_list) # <--- 新增

      # [修改点 3: 增加卡片板块构建]
      ELEMENTS_JSON="..." # ...

      # ... (if [ -n "$GITHUB_MD" ]; then ... fi) ...

      if [ -n "$ZHIHU_MD" ]; then # <--- 新增
        SECTION=$(jq -n --arg content "$ZHIHU_MD" '[{"tag": "hr"}, {"tag": "div", "text": {"tag": "lark_md", "content": "**知乎 | 热榜**"}}, {"tag": "div", "text": {"tag": "lark_md", "content": $content}}]')
        ELEMENTS_JSON=$(echo "$ELEMENTS_JSON" | jq --argjson section "$SECTION" '. + $section')
      fi

      # 您可能还需要在按钮区域添加一个“前往知乎”的按钮
      # ...
    ```

完成以上步骤后，您的项目就成功集成了新的热榜来源！

## 💌 飞书通知预览

<pre>
📰 <strong>每日热榜简报</strong>
--------------------------------------------------------------------------------
<strong>更新时间:</strong> 2025年09月10日 20:00

--------------------------------------------------------------------------------
<strong>36氪 | 热榜</strong>
1. <a href="https://36kr.com/...">留学生们，正在围攻夸克</a>
2. <a href="https://36kr.com/...">李想还有三根救命毫毛</a>

--------------------------------------------------------------------------------
<strong>掘金 | 热榜</strong>
1. <a href="https://juejin.cn/...">前端最新框架深度解析</a>
...

--------------------------------------------------------------------------------
| <a href="https://36kr.com/">前往 36氪</a> | <a href="https://juejin.cn/hot">前往 掘金</a> | <a href="https://github.com/trending">前往 GitHub</a> |
</pre>

## 🤝 贡献

欢迎提交 Pull Request 来修复 Bug 或增加新的功能和热榜来源！

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。
