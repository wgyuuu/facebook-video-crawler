# Facebook 登录设置指南

## 概述

Facebook 视频爬虫系统现在支持登录功能，这可以解决大部分访问限制问题。

## 配置登录

### 1. 编辑配置文件

打开 `config/config.yaml` 文件，找到 Facebook 登录配置部分：

```yaml
facebook:
  login:
    enabled: true           # 启用登录功能
    email: "your_email@example.com"    # 你的Facebook邮箱
    password: "your_password"           # 你的Facebook密码
    session_persistence: true           # 保持会话
```

### 2. 安全注意事项

⚠️ **重要安全提醒**：
- 不要在代码中硬编码密码
- 考虑使用环境变量或加密的凭据文件
- 定期更改密码
- 使用专用的测试账户

### 3. 使用环境变量（推荐）

创建 `.env` 文件：

```bash
# .env
FACEBOOK_EMAIL=your_email@example.com
FACEBOOK_PASSWORD=your_password
```

然后修改配置文件：

```yaml
facebook:
  login:
    enabled: true
    email: ${FACEBOOK_EMAIL}
    password: ${FACEBOOK_PASSWORD}
```

## 运行爬虫

配置完成后，正常运行爬虫：

```bash
python run.py search "美食制作" --max-results 20 --region US
```

系统会自动：
1. 尝试直接搜索
2. 如果失败，检测是否需要登录
3. 如果登录已启用，自动进行身份验证
4. 登录成功后重试搜索

## 故障排除

### 登录失败
- 检查邮箱和密码是否正确
- 确认Facebook账户没有被锁定
- 检查是否有双因素认证

### 仍然无法搜索
- 确认登录成功（查看日志）
- 检查Facebook是否有新的反爬虫措施
- 尝试使用不同的搜索关键词

## 禁用登录

如果不需要登录功能，在配置文件中设置：

```yaml
facebook:
  login:
    enabled: false
```

## 支持

如果遇到问题，请检查日志文件或联系技术支持。
