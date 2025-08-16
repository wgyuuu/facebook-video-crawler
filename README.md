# Facebook Video Crawler System

一个功能强大的Facebook视频爬虫系统，具备先进的反检测能力和高效的数据提取功能。

## 功能特性

- 🚀 **高性能爬虫引擎**: 基于Playwright的现代化爬虫系统
- 🛡️ **先进反检测**: 浏览器指纹伪造、代理IP轮换、行为模拟
- 📊 **全面数据提取**: 视频元数据、播放量、点赞数、评论数等
- 🌍 **多地区支持**: 支持美国、英国、加拿大、澳大利亚、德国等地区
- 💾 **本地存储**: 视频文件本地存储，元数据数据库管理
- 📈 **实时监控**: 爬取状态监控、性能指标、错误追踪
- 🔧 **高度可配置**: YAML配置文件，支持运行时调整

## 系统架构

```
Facebook Video Crawler System
├── Core Layer (核心层)
│   ├── Crawler Engine (爬虫引擎)
│   ├── Session Manager (会话管理)
│   └── Task Scheduler (任务调度)
├── Anti-Detection Layer (反检测层)
│   ├── Browser Fingerprint Manager (浏览器指纹管理)
│   ├── Proxy Manager (代理管理)
│   ├── Behavior Simulator (行为模拟)
│   └── Request Disguiser (请求伪装)
├── Data Layer (数据层)
│   ├── Video Extractor (视频提取器)
│   ├── Data Parser (数据解析器)
│   └── Storage Manager (存储管理)
└── Utility Layer (工具层)
    ├── Logger (日志系统)
    ├── Config Manager (配置管理)
    └── Error Handler (错误处理)
```

## 安装要求

### 系统要求
- Python 3.8+
- 8GB+ RAM
- 100GB+ 可用磁盘空间
- 稳定的网络连接

### 依赖安装

```bash
# 克隆项目
git clone <repository-url>
cd facebook-video-crawler

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install
```

## 配置说明

### 1. 主配置文件 (config/config.yaml)

系统的主要配置文件，包含所有爬虫参数设置：

```yaml
crawler:
  engine: "playwright"
  headless: false
  timeout: 30000
  
anti_detection:
  proxy:
    enabled: true
    pool_size: 50
```

### 2. 代理配置 (config/proxies.txt)

添加您的代理服务器列表：

```
http://proxy1.example.com:8080
https://proxy2.example.com:3128
socks5://proxy3.example.com:1080
```

### 3. User-Agent配置 (config/user_agents.txt)

系统会自动轮换使用不同的User-Agent。

## 使用方法

### 基本使用

```python
from src.main import FacebookVideoCrawler

# 创建爬虫实例
crawler = FacebookVideoCrawler()

# 搜索并爬取视频
videos = await crawler.search_videos(
    keyword="美食制作",
    max_results=50,
    region="US"
)

# 下载视频
for video in videos:
    await crawler.download_video(video)
```

### 命令行使用

```bash
# 基本搜索
python run.py search --keyword "美食制作" --max-results 50 --region US

# 批量下载
python run.py download --keyword "美食制作" --max-results 100

# 查看状态
python run.py status
```

## 数据字段说明

系统会提取以下视频信息：

- **基本信息**: 标题、描述、作者、发布时间
- **统计数据**: 播放量、点赞数、评论数、收藏数、转发数
- **分类信息**: 标签、分类、地区
- **技术信息**: 视频质量、时长、文件大小
- **元数据**: 原始URL、爬取时间、状态信息

## 反检测策略

### 1. 浏览器指纹伪造
- Canvas指纹随机化
- WebGL参数伪造
- 字体指纹管理
- 屏幕分辨率随机化

### 2. 代理IP管理
- 住宅代理支持
- 地理位置匹配
- 健康状态监控
- 智能轮换策略

### 3. 行为模拟
- 鼠标轨迹生成
- 点击行为模拟
- 滚动行为模拟
- 页面停留时间随机化

### 4. 请求伪装
- User-Agent轮换
- 请求头随机化
- 请求时序控制
- 频率限制绕过

## 性能指标

- **成功率**: 目标95%+
- **并发能力**: 支持多浏览器实例
- **处理速度**: 每分钟可处理10-20个视频
- **资源使用**: 内存使用<2GB，CPU使用<80%

## 注意事项

### ⚠️ 合规性警告
- 请确保遵守Facebook的服务条款
- 注意遵守当地的数据保护法规
- 建议控制爬取频率，避免对目标网站造成压力

### 🔒 安全建议
- 定期更新代理IP池
- 监控系统日志，及时发现异常
- 备份重要数据和配置

## 故障排除

### 常见问题

1. **代理连接失败**
   - 检查代理服务器状态
   - 验证代理配置格式
   - 测试网络连接

2. **反检测触发**
   - 降低爬取频率
   - 更新浏览器指纹
   - 更换代理IP

3. **数据提取失败**
   - 检查页面结构变化
   - 更新选择器规则
   - 验证网络连接

### 日志查看

```bash
# 查看实时日志
tail -f data/logs/crawler.log

# 查看错误日志
grep "ERROR" data/logs/crawler.log
```

## 开发指南

### 项目结构
```
src/
├── core/           # 核心模块
├── anti_detection/ # 反检测模块
├── data/           # 数据层
└── utils/          # 工具模块
```

### 添加新功能
1. 在相应模块中创建新类
2. 更新`__init__.py`文件
3. 添加配置文件选项
4. 编写测试用例
5. 更新文档

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_crawler.py

# 生成覆盖率报告
pytest --cov=src tests/
```

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和网站服务条款。

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**免责声明**: 使用本系统进行网络爬取时，请确保遵守相关法律法规和网站服务条款。开发者不对使用本系统产生的任何后果承担责任。
