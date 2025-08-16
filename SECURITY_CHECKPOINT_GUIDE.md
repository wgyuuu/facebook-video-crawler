# Facebook 安全检查点处理指南

## 概述

Facebook 安全检查点（Security Checkpoint）是Facebook的安全机制，用于验证用户身份。本系统现在支持自动处理多种类型的安全检查点。

## 检查点类型

### 1. 验证码检查点 (Verification Code)
- **触发条件**: 新设备登录、异常登录行为
- **处理方式**: 自动输入配置的验证码
- **配置要求**: 在配置文件中设置 `verification_code`

### 2. 安全问题检查点 (Security Questions)
- **触发条件**: 账户安全验证
- **处理方式**: 自动回答配置的安全问题
- **配置要求**: 在配置文件中设置 `security_answers`

### 3. 设备确认检查点 (Device Confirmation)
- **触发条件**: 新设备或位置登录
- **处理方式**: 自动点击"这是我"按钮
- **配置要求**: 设置 `auto_confirm_device: true`

### 4. 验证码检查点 (Captcha)
- **触发条件**: 机器人检测
- **处理方式**: 手动输入验证码答案
- **配置要求**: 在配置文件中设置 `captcha_solution`

## 配置方法

### 1. 编辑配置文件

打开 `config/config.yaml` 文件，找到登录配置部分：

```yaml
facebook:
  login:
    enabled: true
    email: "your_email@example.com"
    password: "your_password"
    
    # 安全检查点配置
    security_checkpoint:
      enabled: true                    # 启用自动处理
      max_attempts: 3                  # 最大尝试次数
      timeout: 60                      # 超时时间（秒）
      
      # 验证码（如果需要）
      verification_code: "123456"      # 短信/邮箱验证码
      
      # 安全问题答案
      security_answers:
        "What is your mother's maiden name?": "Smith"
        "What was your first pet's name?": "Buddy"
        "In what city were you born?": "Beijing"
      
      # 验证码答案（如果需要）
      captcha_solution: "ABC123"
      
      # 设备确认
      auto_confirm_device: true        # 自动确认设备
```

### 2. 获取验证码

#### 短信验证码
1. 登录Facebook时选择"通过短信发送验证码"
2. 输入收到的6位数字验证码到配置文件

#### 邮箱验证码
1. 登录Facebook时选择"通过邮箱发送验证码"
2. 检查邮箱并输入收到的验证码

### 3. 设置安全问题答案

1. 登录Facebook账户设置
2. 找到"安全和登录" > "安全问题"
3. 记录问题和答案
4. 在配置文件中设置对应的答案

## 使用建议

### 1. 安全考虑
- 不要在代码中硬编码敏感信息
- 考虑使用环境变量
- 定期更改密码和安全问题答案

### 2. 故障排除
- 如果验证码过期，重新获取并更新配置
- 如果安全问题答案错误，检查拼写和大小写
- 如果设备确认失败，可能需要手动处理

### 3. 最佳实践
- 使用专用的测试账户
- 在稳定的网络环境下运行
- 定期检查Facebook的安全设置

## 运行示例

配置完成后，正常运行爬虫：

```bash
python run.py search "美食制作" --max-results 20 --region US
```

系统会自动：
1. 检测安全检查点
2. 识别检查点类型
3. 使用配置的凭据自动处理
4. 继续执行搜索任务

## 支持

如果遇到问题：
1. 检查配置文件格式
2. 确认验证码是否有效
3. 查看日志文件了解详细错误信息
4. 必要时手动完成安全检查点
