// Background Service Worker - Aether Agent Core
let state = {
    messages: [],
    status: 'idle', // 'idle', 'running'
    currentThought: '',
    isAsking: false,
    askMessage: '',
    history: [],
    currentTask: ''
};

const notifyPopup = () => {
    chrome.runtime.sendMessage({ action: 'STATE_UPDATED', state }).catch(() => {
    });
};

const updateState = (patch) => {
    state = { ...state, ...patch };
    notifyPopup();
};

const captureScreenshot = async () => {
    try {
        const tab = await getActiveTab();
        if (!tab) return null;

        console.log("开始捕获截图和DOM快照...，标签页ID:", tab.id, "URL:", tab.url);

        const dataUrl = await new Promise((resolve) => {
            chrome.tabs.captureVisibleTab(null, { format: 'png' }, (url) => {
                resolve(url);
            });
        });

        const domSnapshot = await new Promise((resolve) => {
            chrome.tabs.sendMessage(tab.id, { action: 'GET_DOM_SNAPSHOT' }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error("GET_DOM_SNAPSHOT错误:", chrome.runtime.lastError);
                    resolve([]);
                } else {
                    console.log("GET_DOM_SNAPSHOT响应:", response);
                    resolve(response?.snapshot || []);
                }
            });
        });

        console.log("DOM快照元素数量:", domSnapshot.length);

        return { dataUrl, domSnapshot };
    } catch (e) {
        console.error("Capture failure:", e);
        return null;
    }
};

const getActiveTab = async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab;
};

const performAction = async (action) => {
    const { action_type, params } = action;

    if (action_type === 'ask_user') {
        updateState({ isAsking: true, askMessage: params.message });
        return "等待用户协助...";
    }

    try {
        const tab = await getActiveTab();
        if (!tab) throw new Error("未找到活动标签页");

        if (action_type === 'navigate') {
            let url = params.url;
            if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
                url = `https://${url}`;
            }
            
            return new Promise((resolve) => {
                const targetUrl = url;
                const tabId = tab.id;
                let resolved = false;
                
                const onUpdated = (updatedTabId, changeInfo, updatedTab) => {
                    if (updatedTabId === tabId && changeInfo.status === 'complete') {
                        chrome.tabs.onUpdated.removeListener(onUpdated);
                        if (!resolved) {
                            resolved = true;
                            resolve(`导航成功: ${targetUrl}`);
                        }
                    }
                };
                
                const onErrorOccurred = (details) => {
                    if (details.tabId === tabId) {
                        chrome.webNavigation.onErrorOccurred.removeListener(onErrorOccurred);
                        if (!resolved) {
                            resolved = true;
                            resolve(`导航失败: ${details.error || '未知错误'}`);
                        }
                    }
                };
                
                const timeout = setTimeout(() => {
                    chrome.tabs.onUpdated.removeListener(onUpdated);
                    if (!resolved) {
                        resolved = true;
                        resolve(`导航超时: ${targetUrl}`);
                    }
                }, 30000);
                
                chrome.tabs.onUpdated.addListener(onUpdated);
                
                chrome.tabs.sendMessage(tabId, {
                    action: 'PERFORM_DOM_ACTION',
                    data: { action_type, params: { ...params, url } }
                }, (response) => {
                });
            });
        }

        return new Promise((resolve) => {
            console.log("发送动作到bridge.js:", action_type, params);
            chrome.tabs.sendMessage(tab.id, {
                action: 'PERFORM_DOM_ACTION',
                data: { action_type, params }
            }, (response) => {
                console.log("bridge.js响应:", response);
                if (response?.status === 'success') {
                    resolve(response.result || "操作成功");
                } else {
                    resolve(`执行失败: ${response?.message || '未知错误'}`);
                }
            });
        });
    } catch (e) {
        return `通讯失败: ${e.message}`;
    }
};

const runLoop = async (taskText) => {
    console.log("Starting background runLoop for task:", taskText);
    updateState({
        status: 'running',
        currentTask: taskText,
        messages: [{ text: taskText, type: 'user' }],
        history: [],
        currentThought: '正在准备环境...',
        isAsking: false
    });

    let stepCount = 0;
    const maxSteps = 15;

    while (state.status === 'running' && stepCount < maxSteps) {
        if (state.isAsking) {
            await new Promise(r => setTimeout(r, 1000));
            continue;
        }

        stepCount++;
        console.log(`Executing step ${stepCount}...`);
        const captured = await captureScreenshot();

        if (state.status !== 'running') break;

        if (!captured) {
            updateState({ status: 'idle', currentThought: '截图捕获失败' });
            break;
        }

        const { dataUrl: imgData, domSnapshot } = captured;

        try {
            const res = await fetch('http://localhost:5000/api/plan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task: state.currentTask,
                    image: imgData,
                    history: state.history,
                    dom_snapshot: domSnapshot
                })
            });

            if (state.status !== 'running') break;

            const data = await res.json();
            if (data.error) throw new Error(data.error);

            const action = data.action;
            console.log("Planned action:", action.action_type);

            let newMessages = [...state.messages];
            if (action.thought) {
                newMessages.push({ text: action.thought, type: 'agent', isThought: true });
            }

            if (action.action_type === 'complete') {
                newMessages.push({ text: `✅ ${action.params.message || '任务完成'}`, type: 'agent' });
                updateState({ messages: newMessages, status: 'idle', currentThought: '任务成功完成' });
                break;
            }

            updateState({ messages: newMessages, currentThought: action.thought || '逻辑分析中...' });

            const result = await performAction(action);

            if (action.action_type !== 'ask_user') {
                const newHistory = [...state.history, { step: stepCount, action, result }];
                updateState({ history: newHistory });
            }

        } catch (e) {
            console.error("RunLoop Error:", e);
            updateState({
                messages: [...state.messages, { text: `❌ 系统异常: ${e.message}`, type: 'agent' }],
                status: 'idle',
                currentThought: ''
            });
            break;
        }

        await new Promise(r => setTimeout(r, 2000));
    }

    console.log("Background runLoop finished.");
    if (state.status === 'running') {
        updateState({ status: 'idle', currentThought: '' });
    }
};

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'capture_tab') {
        captureScreenshot().then(dataUrl => sendResponse({ dataUrl }));
        return true;
    }

    if (request.action === 'START_TASK') {
        runLoop(request.task);
        sendResponse({ status: 'started' });
        return true;
    }

    if (request.action === 'STOP_TASK') {
        console.log("Received STOP_TASK request");
        updateState({ status: 'idle', currentThought: '用户已手动停止任务' });
        sendResponse({ status: 'stopped' });
        return true;
    }

    if (request.action === 'GET_STATE') {
        sendResponse(state);
        return true;
    }

    if (request.action === 'RESUME_TASK') {
        updateState({ isAsking: false, askMessage: '' });
        sendResponse({ status: 'resumed' });
        return true;
    }
});
