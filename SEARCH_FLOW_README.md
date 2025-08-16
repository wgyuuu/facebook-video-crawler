# Facebook Video Crawler - 修改后的搜索流程

## 概述

根据测试发现，Facebook需要先登录才能进行搜索操作。因此，我们修改了 `search_videos` 方法的流程，现在它会：

1. 首先打开 Facebook 首页
2. 检查是否需要登录
3. 如果需要登录，则执行登录流程
4. 登录成功后，找到搜索框并输入关键词进行搜索
5. 提取搜索结果中的视频信息

## 主要修改

### 1. 新的搜索流程 (`search_videos` 方法)

```python
async def search_videos(self, keyword: str, max_results: Optional[int] = None, 
                       region: Optional[str] = None) -> List[VideoMetadata]:
```

**流程步骤：**
- **步骤 1**: 导航到 Facebook 首页 (`https://www.facebook.com/`)
- **步骤 2**: 检查登录状态，如果需要则执行登录
- **步骤 3**: 查找搜索功能并执行搜索
- **步骤 4**: 等待搜索结果加载并提取视频 URL

### 2. 新增的辅助方法

#### `_check_login_required()`
- 检查 Facebook 页面是否需要登录
- 通过查找登录表单元素和已登录指示器来判断

#### `_perform_login()`
- 执行 Facebook 登录流程
- 使用配置文件中的凭据
- 支持高级行为模拟（如果启用）
- 处理安全检查点

#### `_perform_search()`
- 在 Facebook 页面上查找搜索框
- 输入搜索关键词并执行搜索
- 支持多种语言（英文、中文、西班牙语等）

## 配置要求

确保在 `config/config.yaml` 中正确配置登录信息：

```yaml
facebook:
  login:
    enabled: true
    email: "your_email@example.com"
    password: "your_password"
    session_persistence: true
```

## 使用方法

### 基本使用

```python
from src.main import FacebookVideoCrawler

async def main():
    async with FacebookVideoCrawler() as crawler:
        # 搜索视频
        videos = await crawler.search_videos("美食制作", max_results=10)
        
        # 处理结果
        for video in videos:
            print(f"标题: {video.title}")
            print(f"状态: {video.status}")
            print(f"URL: {video.url}")

# 运行
asyncio.run(main())
```

### 测试修改后的流程

运行测试脚本：

```bash
python test_search_flow.py
```

## 错误处理

新的流程包含完善的错误处理：

- 如果无法导航到 Facebook 首页，返回错误信息
- 如果登录失败，返回详细的失败原因
- 如果搜索失败，返回相应的错误信息
- 所有错误都会记录在日志中

## 日志输出

流程执行过程中会输出详细的日志信息：

```
INFO: Step 1: Navigating to Facebook homepage...
INFO: Successfully navigated to Facebook homepage
INFO: Step 2: Checking login status...
INFO: Login required, attempting to authenticate...
INFO: Login successful, waiting for page to load...
INFO: Step 3: Looking for search functionality...
INFO: Found search box with selector: input[placeholder*='Search']
INFO: Search performed successfully
INFO: Step 4: Waiting for search results to load...
```

## 注意事项

1. **登录凭据**: 确保配置文件中的 Facebook 登录凭据正确
2. **网络环境**: 确保网络环境能够访问 Facebook
3. **反检测**: 如果启用高级反检测功能，登录过程会更自然
4. **安全检查点**: 系统会自动处理常见的安全检查点

## 兼容性

- 支持多种语言的 Facebook 界面
- 兼容不同的 Facebook 页面布局
- 支持高级反检测功能（如果启用）

## 故障排除

### 常见问题

1. **登录失败**
   - 检查配置文件中的凭据
   - 确认账户没有被锁定
   - 检查是否需要验证码

2. **搜索框未找到**
   - Facebook 可能更新了页面结构
   - 检查是否成功登录
   - 查看日志中的详细错误信息

3. **搜索结果为空**
   - 确认搜索关键词正确
   - 检查网络连接
   - 查看是否有地区限制

### 调试模式

启用调试日志以获取更多信息：

```yaml
storage:
  logging:
    level: "DEBUG"
```

## 更新日志

- **v1.1.0**: 重构搜索流程，添加登录步骤
- **v1.1.1**: 改进错误处理和日志记录
- **v1.1.2**: 添加多语言搜索框支持
