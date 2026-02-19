# AI看手相工具 API 文档

本文档提供了AI看手相工具的API接口说明，帮助开发者集成和使用相关功能。

## 基础信息

- **API基础URL**: `http://localhost:3000/api`
- **请求方法**: POST, GET
- **内容类型**: JSON, multipart/form-data

## 接口列表

### 1. 手相分析接口

**接口路径**: `/analyze`
**请求方法**: POST
**内容类型**: multipart/form-data

#### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| handImage | file | 是 | 手相图像文件 (支持JPG, PNG, WEBP等格式) |

#### 响应格式

```json
{
  "success": true,
  "result": {
    "love": ["感情分析1", "感情分析2", "感情分析3"],
    "career": ["事业分析1", "事业分析2", "事业分析3"],
    "wealth": ["财运分析1", "财运分析2", "财运分析3"],
    "health": ["健康分析1", "健康分析2", "健康分析3"]
  }
}
```

#### 响应字段说明

| 字段名 | 类型 | 描述 |
|-------|------|------|
| success | boolean | 请求是否成功 |
| result | object | 分析结果 |
| result.love | array | 感情方面的分析结果 (来自三个AI模型) |
| result.career | array | 事业方面的分析结果 (来自三个AI模型) |
| result.wealth | array | 财运方面的分析结果 (来自三个AI模型) |
| result.health | array | 健康方面的分析结果 (来自三个AI模型) |

#### 错误响应

```json
{
  "error": "错误信息"
}
```

### 2. 健康检查接口

**接口路径**: `/health`
**请求方法**: GET
**内容类型**: JSON

#### 响应格式

```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## 使用示例

### 使用curl上传并分析手相

```bash
curl -X POST http://localhost:3000/api/analyze \
  -F "handImage=@path/to/hand.jpg"
```

### 使用JavaScript上传并分析手相

```javascript
const formData = new FormData();
formData.append('handImage', file);

fetch('http://localhost:3000/api/analyze', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('分析结果:', data.result);
    } else {
        console.error('分析失败:', data.error);
    }
})
.catch(error => {
    console.error('请求失败:', error);
});
```

### 使用Python上传并分析手相

```python
import requests

url = 'http://localhost:3000/api/analyze'
files = {'handImage': open('path/to/hand.jpg', 'rb')}

response = requests.post(url, files=files)
print(response.json())
```

## 注意事项

1. **图像要求**: 上传的手相图像应清晰可见，手掌张开，光线充足，建议分辨率不低于800x600
2. **文件大小**: 单个图像文件大小建议不超过5MB
3. **请求频率**: 为避免API调用过于频繁，建议对同一用户的请求进行限流
4. **API密钥**: 请确保在服务器端正确配置了deepseek、千问、智谱三家API的密钥
5. **隐私保护**: 系统会自动清理临时上传的图像文件，确保用户隐私安全

## 错误代码

| 错误代码 | 描述 | 解决方案 |
|---------|------|---------|
| 400 | 请上传手相照片 | 确保上传了有效的图像文件 |
| 500 | 分析失败，请重试 | 检查API密钥配置，确保网络连接正常 |
| 413 | 请求实体过大 | 减小图像文件大小 |
| 415 | 不支持的媒体类型 | 确保上传的是有效的图像文件 |

## 性能优化建议

1. **客户端优化**: 在上传前对图像进行压缩，减少传输时间
2. **服务器端优化**: 使用缓存机制，避免重复分析相同的图像
3. **并发处理**: 对多个API调用使用并发处理，减少分析时间
4. **错误处理**: 实现优雅的错误处理机制，提高系统稳定性

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0.0 | 2024-01-01 | 初始版本，实现基本的手相分析功能 |

## 联系我们

如有API相关问题或建议，请联系我们的技术支持团队：

- Email: support@ai-hand-palm-reader.com
- GitHub: https://github.com/your-username/ai-hand-palm-reader
