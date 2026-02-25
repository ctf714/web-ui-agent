import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const [task, setTask] = useState('')
  const [messages, setMessages] = useState([])
  const [status, setStatus] = useState('idle')
  const [currentThought, setCurrentThought] = useState('')
  const [isAsking, setIsAsking] = useState(false)
  const [askMessage, setAskMessage] = useState('')
  const historyRef = useRef(null)

  // 1. 同步后台状态
  const syncState = () => {
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
      chrome.runtime.sendMessage({ action: 'GET_STATE' }, (state) => {
        if (state) {
          setMessages(state.messages || []);
          setStatus(state.status || 'idle');
          setCurrentThought(state.currentThought || '');
          setIsAsking(state.isAsking || false);
          setAskMessage(state.askMessage || '');
        }
      });
    }
  };

  useEffect(() => {
    syncState();

    const listener = (request) => {
      if (request.action === 'STATE_UPDATED') {
        const { state } = request;
        setMessages(state.messages || []);
        setStatus(state.status || 'idle');
        setCurrentThought(state.currentThought || '');
        setIsAsking(state.isAsking || false);
        setAskMessage(state.askMessage || '');
      }
    };

    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
      chrome.runtime.onMessage.addListener(listener);
      return () => chrome.runtime.onMessage.removeListener(listener);
    }
  }, []);

  useEffect(() => {
    if (historyRef.current) {
      historyRef.current.scrollTop = historyRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = () => {
    if (!task) return;
    if (typeof chrome !== 'undefined' && chrome.runtime?.sendMessage) {
      chrome.runtime.sendMessage({ action: 'START_TASK', task }, () => {
        setTask('');
        syncState();
      });
    }
  };

  const handleStop = () => {
    if (typeof chrome !== 'undefined' && chrome.runtime?.sendMessage) {
      chrome.runtime.sendMessage({ action: 'STOP_TASK' }, () => {
        syncState();
      });
    }
  };

  const handleResume = () => {
    if (typeof chrome !== 'undefined' && chrome.runtime?.sendMessage) {
      chrome.runtime.sendMessage({ action: 'RESUME_TASK' }, () => {
        syncState();
      });
    }
  };

  const isExecuting = status === 'running' && !isAsking;

  return (
    <div className="popup-container">
      <div className={`glass-dialog modern ${isAsking ? 'asking' : ''}`}>
        <div className="chat-header">
          <div className="header-info">
            <span className="logo-spark">✨</span>
            <span className="logo-text">Aether Agent</span>
            <div className={`status-pill ${status}`}>{status.toUpperCase()}</div>
          </div>
        </div>

        {/* 实时思维条 */}
        {status === 'running' && currentThought && (
          <div className="inline-thought">
            <div className="loader-mini"></div>
            <span>{currentThought}</span>
          </div>
        )}

        <div className="main-content">
          <div className="chat-history" ref={historyRef}>
            {messages.length === 0 && (
              <div className="welcome-guide">
                <div className="guide-title">准备好开始了吗？</div>
                <div className="guide-steps">
                  <div className="step-item">
                    <span className="step-num">1</span>
                    <p>在下方输入指令操控当前网页</p>
                  </div>
                  <div className="step-item">
                    <span className="step-num">2</span>
                    <p>Agent 将在后台持续运行，即使关闭此窗口</p>
                  </div>
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`message-modern ${m.type} ${m.isThought ? 'thought-msg' : ''}`}>
                {m.text}
              </div>
            ))}

            {isAsking && (
              <div className="ask-box">
                <div className="ask-header">AI 需要您的协助</div>
                <div className="ask-text">{askMessage}</div>
                <button className="resume-btn" onClick={handleResume}>我已处理，继续</button>
              </div>
            )}
          </div>
        </div>

        <div className="chat-input-area-modern">
          <input
            type="text"
            placeholder={isAsking ? "请先完成 AI 的协助请求..." : "输入指令..."}
            value={task}
            onChange={(e) => setTask(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isExecuting && handleSend()}
            disabled={isExecuting}
            autoFocus
          />
          {status === 'running' ? (
            <button onClick={handleStop} className="send-btn-modern stop">
              中断
            </button>
          ) : (
            <button onClick={handleSend} disabled={!task} className="send-btn-modern">
              启动
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
