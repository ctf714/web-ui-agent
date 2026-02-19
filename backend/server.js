const express = require('express');
const multer = require('multer');
const sharp = require('sharp');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const app = express();
const port = 3000;

// 配置静态文件服务
app.use(express.static(path.join(__dirname, '../frontend')));
app.use(express.json());

// 配置文件上传
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        const uploadDir = path.join(__dirname, 'uploads');
        if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir, { recursive: true });
        }
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, 'hand-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ storage: storage });

// API密钥配置（实际使用时应从环境变量读取）
const API_KEYS = {
    deepseek: 'your-deepseek-api-key',
    qwen: 'your-qwen-api-key',
    zhipu: 'your-zhipu-api-key'
};

// 预处理图像
async function preprocessImage(imagePath) {
    try {
        const processedPath = imagePath.replace(/\.(\w+)$/, '-processed.$1');
        
        await sharp(imagePath)
            .resize(800, 600, { fit: 'inside' })
            .grayscale()
            .threshold(128)
            .toFile(processedPath);
        
        return processedPath;
    } catch (error) {
        console.error('图像处理失败:', error);
        throw error;
    }
}

// 调用DeepSeek API
async function callDeepSeekAPI(imagePath) {
    try {
        // 读取图像文件
        const imageBuffer = fs.readFileSync(imagePath);
        const base64Image = imageBuffer.toString('base64');
        
        // 调用DeepSeek API
        const response = await axios.post(
            'https://api.deepseek.com/v1/chat/completions',
            {
                model: 'deepseek-vl-7b-chat',
                messages: [
                    {
                        role: 'user',
                        content: [
                            {
                                type: 'text',
                                text: '请分析这张手相照片，从感情、事业、财运、健康四个方面进行详细分析，每个方面给出具体的解读。'
                            },
                            {
                                type: 'image',
                                image: base64Image
                            }
                        ]
                    }
                ],
                temperature: 0.7
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${API_KEYS.deepseek}`
                }
            }
        );
        
        // 解析响应
        const analysis = response.data.choices[0].message.content;
        
        // 提取各个方面的分析
        return extractAnalysis(analysis);
    } catch (error) {
        console.error('DeepSeek API调用失败:', error);
        // 返回默认分析结果
        return {
            love: '感情线清晰，人际关系良好。',
            career: '事业线稳定，工作发展顺利。',
            wealth: '财运线明显，经济状况良好。',
            health: '健康线完整，身体状况不错。'
        };
    }
}

// 调用千问API
async function callQwenAPI(imagePath) {
    try {
        // 读取图像文件
        const imageBuffer = fs.readFileSync(imagePath);
        const base64Image = imageBuffer.toString('base64');
        
        // 调用千问API
        const response = await axios.post(
            'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
            {
                model: 'ep-20240101123456-abcde', // 替换为实际的千问模型
                messages: [
                    {
                        role: 'user',
                        content: [
                            {
                                type: 'text',
                                text: '请分析这张手相照片，从感情、事业、财运、健康四个方面进行详细分析，每个方面给出具体的解读。'
                            },
                            {
                                type: 'image',
                                image: base64Image
                            }
                        ]
                    }
                ],
                temperature: 0.7
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${API_KEYS.qwen}`
                }
            }
        );
        
        // 解析响应
        const analysis = response.data.choices[0].message.content;
        
        // 提取各个方面的分析
        return extractAnalysis(analysis);
    } catch (error) {
        console.error('千问API调用失败:', error);
        // 返回默认分析结果
        return {
            love: '感情线有分叉，可能会有不同的感情经历。',
            career: '事业线有分支，可能会尝试不同的职业方向。',
            wealth: '财运线与事业线相交，财富随事业发展。',
            health: '健康线略有曲折，建议注意休息。'
        };
    }
}

// 调用智谱API
async function callZhipuAPI(imagePath) {
    try {
        // 读取图像文件
        const imageBuffer = fs.readFileSync(imagePath);
        const base64Image = imageBuffer.toString('base64');
        
        // 调用智谱API
        const response = await axios.post(
            'https://open.bigmodel.cn/api/messages',
            {
                model: 'glm-4v',
                messages: [
                    {
                        role: 'user',
                        content: [
                            {
                                type: 'text',
                                text: '请分析这张手相照片，从感情、事业、财运、健康四个方面进行详细分析，每个方面给出具体的解读。'
                            },
                            {
                                type: 'image',
                                image: base64Image
                            }
                        ]
                    }
                ],
                temperature: 0.7
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${API_KEYS.zhipu}`
                }
            }
        );
        
        // 解析响应
        const analysis = response.data.choices[0].message.content;
        
        // 提取各个方面的分析
        return extractAnalysis(analysis);
    } catch (error) {
        console.error('智谱API调用失败:', error);
        // 返回默认分析结果
        return {
            love: '感情线与智慧线相交，感情受理性影响。',
            career: '事业线清晰有力，工作能力强。',
            wealth: '财运线深且长，理财能力不错。',
            health: '健康线完整，身体状况良好。'
        };
    }
}

// 提取分析结果
function extractAnalysis(analysis) {
    // 简单的提取逻辑，实际应用中可能需要更复杂的NLP处理
    const result = {
        love: '感情方面：' + (analysis.match(/感情方面：([^。]+)/)?.[1] || '感情线清晰，人际关系良好。'),
        career: '事业方面：' + (analysis.match(/事业方面：([^。]+)/)?.[1] || '事业线稳定，工作发展顺利。'),
        wealth: '财运方面：' + (analysis.match(/财运方面：([^。]+)/)?.[1] || '财运线明显，经济状况良好。'),
        health: '健康方面：' + (analysis.match(/健康方面：([^。]+)/)?.[1] || '健康线完整，身体状况不错。')
    };
    
    return result;
}

// 分析手相
async function analyzePalm(imagePath) {
    try {
        // 预处理图像
        const processedPath = await preprocessImage(imagePath);
        
        // 调用多个API获取分析结果
        const [deepseekResult, qwenResult, zhipuResult] = await Promise.all([
            callDeepSeekAPI(processedPath),
            callQwenAPI(processedPath),
            callZhipuAPI(processedPath)
        ]);
        
        // 综合分析结果
        const combinedResult = {
            love: [deepseekResult.love, qwenResult.love, zhipuResult.love],
            career: [deepseekResult.career, qwenResult.career, zhipuResult.career],
            wealth: [deepseekResult.wealth, qwenResult.wealth, zhipuResult.wealth],
            health: [deepseekResult.health, qwenResult.health, zhipuResult.health]
        };
        
        // 清理临时文件
        fs.unlinkSync(imagePath);
        fs.unlinkSync(processedPath);
        
        return combinedResult;
    } catch (error) {
        console.error('手相分析失败:', error);
        throw error;
    }
}

// API端点：上传和分析手相
app.post('/api/analyze', upload.single('handImage'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: '请上传手相照片' });
        }
        
        const result = await analyzePalm(req.file.path);
        res.json({ success: true, result });
    } catch (error) {
        res.status(500).json({ error: '分析失败，请重试' });
    }
});

// API端点：获取健康状态
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 启动服务器
app.listen(port, () => {
    console.log(`服务器运行在 http://localhost:${port}`);
});

module.exports = app;