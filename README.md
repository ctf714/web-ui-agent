# AI看手相小工具

一个基于AI技术的手相分析工具，集成了deepseek、千问、智谱三家API，支持手相图像分析、结果展示和分享到小红书等功能。

## 功能特性

- 📷 手相图像采集和上传
- 🖼️ 图像预处理和优化
- 🤖 多AI模型联合分析
- 📊 详细的手相分析报告
- 📱 支持分享到小红书
- 💰 内置变现功能

## 技术架构

- **前端**: HTML5, CSS3, JavaScript
- **后端**: Node.js, Express
- **AI接口**: deepseek, 千问, 智谱
- **图像处理**: Sharp
- **文件上传**: Multer

## 项目结构

```
ai-hand-palm-reader/
├── frontend/           # 前端代码
│   └── index.html      # 主页面
├── backend/            # 后端代码
│   ├── server.js       # 服务器入口
│   ├── api/            # API接口
│   ├── services/       # 业务逻辑
│   ├── utils/          # 工具函数
│   └── uploads/        # 临时上传目录
├── package.json        # 项目配置
└── README.md           # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置API密钥

在 `backend/server.js` 文件中配置你的API密钥：

```javascript
const API_KEYS = {
    deepseek: 'your-deepseek-api-key',
    qwen: 'your-qwen-api-key',
    zhipu: 'your-zhipu-api-key'
};
```

### 3. 启动服务器

```bash
npm start
```

或使用开发模式：

```bash
npm run dev
```

### 4. 访问应用

打开浏览器，访问 `http://localhost:3000`

## 使用方法

1. **上传手相照片**: 点击 "点击上传手相照片" 按钮，选择一张清晰的手相照片
2. **预览图像**: 确认上传的图像是否清晰可见
3. **开始分析**: 点击 "开始分析" 按钮，系统会自动处理图像并调用AI模型进行分析
4. **查看结果**: 分析完成后，会显示详细的手相分析报告
5. **分享结果**: 可以选择分享到小红书或保存分析结果

## 小红书变现策略

1. **免费基础分析**: 提供基础的手相分析功能，吸引用户
2. **付费详细报告**: 提供更详细、深入的手相分析报告
3. **会员订阅**: 推出会员服务，享受无限次分析和专属功能
4. **广告合作**: 与相关品牌合作，在应用中展示广告
5. ** affiliate marketing**: 推荐相关产品，获得佣金

## API文档

详细的API文档请参考 [API.md](./API.md) 文件，包含：

- 接口列表和参数说明
- 请求和响应格式
- 多种编程语言的使用示例
- 错误代码和解决方案
- 性能优化建议

### 主要接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/analyze` | POST | 上传手相图像并进行分析 |
| `/api/health` | GET | 检查系统健康状态 |

## 注意事项

1. 请确保上传的手相照片清晰可见，手掌张开，光线充足
2. 本工具仅供娱乐参考，不构成专业的命理咨询
3. 请遵守相关法律法规，不要利用本工具进行违法活动
4. 保护用户隐私，不要存储或分享用户的手相照片

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request，一起完善这个项目！

## 联系方式

如有问题或建议，请通过以下方式联系：

- Email: your-email@example.com
- GitHub: your-github-username
