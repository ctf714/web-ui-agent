// Bridge script injected into the webpage
console.log("Aether Bridge Active");

const getDOMSnapshot = () => {
    const interactiveSelectors = [
        'button', 'input', 'select', 'textarea', 'a',
        '[role="button"]', '[role="link"]', '[role="checkbox"]', '[role="tab"]',
        '[role="menuitem"]', '[role="option"]', '[role="searchbox"]',
        '[onclick]', '[onmousedown]', '[onmouseup]',
        '[tabindex]:not([tabindex="-1"])',
        '.btn', '.button', '.clickable', '[class*="btn"]', '[class*="button"]',
        'label[for]', 'summary', 'details',
        '[data-action]', '[data-click]', '[data-toggle]',
        'svg', 'img[alt]', 'i[class*="icon"]'
    ];

    const elements = Array.from(document.querySelectorAll(interactiveSelectors.join(',')))
        .filter(el => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width > 2 && rect.height > 2 &&
                rect.top < window.innerHeight + 100 && rect.left < window.innerWidth + 100 &&
                rect.bottom > -100 && rect.right > -100 &&
                style.visibility !== 'hidden' &&
                style.display !== 'none' &&
                style.opacity !== '0' &&
                !el.closest('[aria-hidden="true"]');
        });

    const uniqueElements = [];
    const seenElements = new Set();
    
    for (const el of elements) {
        if (seenElements.has(el)) continue;
        seenElements.add(el);
        
        let parentText = '';
        let parentEl = el.parentElement;
        for (let i = 0; i < 3 && parentEl; i++) {
            if (parentEl.innerText && parentEl.innerText.length < 50) {
                parentText = parentEl.innerText.trim();
                break;
            }
            parentEl = parentEl.parentElement;
        }

        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        const tagName = el.tagName.toLowerCase();
        
        let text = '';
        if (tagName === 'input' || tagName === 'textarea') {
            text = el.placeholder || el.value || el.getAttribute('aria-label') || '';
        } else if (tagName === 'img') {
            text = el.alt || el.title || '';
        } else if (tagName === 'svg') {
            const titleEl = el.querySelector('title');
            text = titleEl ? titleEl.textContent : el.getAttribute('aria-label') || '';
        } else {
            text = (el.innerText || el.textContent || '').trim().slice(0, 60);
            if (!text) {
                text = el.getAttribute('aria-label') || el.title || el.getAttribute('alt') || '';
            }
        }
        text = text.trim().slice(0, 60);

        const inputType = el.type ? el.type.toLowerCase() : null;
        const isHiddenInput = tagName === 'input' && (inputType === 'hidden' || inputType === 'submit' || inputType === 'reset');
        if (isHiddenInput) continue;

        const centerX = Math.round(((rect.left + rect.width / 2) / window.innerWidth) * 1000);
        const centerY = Math.round(((rect.top + rect.height / 2) / window.innerHeight) * 1000);

        const elementInfo = {
            id: uniqueElements.length,
            tag: tagName,
            type: inputType || null,
            role: el.getAttribute('role') || null,
            text: text,
            name: el.name || el.id || null,
            placeholder: el.placeholder || null,
            ariaLabel: el.getAttribute('aria-label') || null,
            title: el.title || null,
            href: tagName === 'a' ? el.href : null,
            disabled: el.disabled || el.getAttribute('aria-disabled') === 'true' || el.classList.contains('disabled'),
            visible: rect.top >= 0 && rect.left >= 0 && rect.bottom <= window.innerHeight && rect.right <= window.innerWidth,
            x: centerX,
            y: centerY,
            width: Math.round(rect.width),
            height: Math.round(rect.height),
            parentText: parentText || null,
            className: el.className && typeof el.className === 'string' ? el.className.split(' ').slice(0, 3).join(' ') : null
        };

        uniqueElements.push(elementInfo);
    }

    return uniqueElements;
};

const findElementByCoords = (x, y, actionType) => {
    let candidate = document.elementFromPoint(x, y);
    
    if (actionType === 'type') {
        const NON_TYPEABLE = ['submit', 'button', 'reset', 'image', 'checkbox', 'radio', 'file', 'range', 'color', 'hidden'];
        const isTypeable = (el) => {
            if (!el) return false;
            if (el.tagName === 'TEXTAREA') return true;
            if (el.tagName === 'INPUT' && !NON_TYPEABLE.includes(el.type?.toLowerCase())) return true;
            if (el.isContentEditable) return true;
            if (el.getAttribute('contenteditable') === 'true') return true;
            return false;
        };

        if (!isTypeable(candidate)) {
            const offsets = [[-30, 0], [30, 0], [0, -30], [0, 30], [-60, 0], [0, -60], [30, 30], [-30, -30]];
            for (const [dx, dy] of offsets) {
                const nearby = document.elementFromPoint(x + dx, y + dy);
                if (isTypeable(nearby)) {
                    candidate = nearby;
                    break;
                }
            }
            if (!isTypeable(candidate)) {
                candidate = document.querySelector('input:not([type="submit"]):not([type="button"]):not([type="reset"]):not([type="image"]):not([type="hidden"]), textarea, [contenteditable="true"]');
            }
        }
    } else if (actionType === 'click') {
        if (candidate) {
            const clickableParents = ['A', 'BUTTON', 'LABEL', 'SUMMARY'];
            let current = candidate;
            for (let i = 0; i < 3 && current; i++) {
                if (clickableParents.includes(current.tagName) || 
                    current.onclick || 
                    current.getAttribute('role') === 'button' ||
                    current.classList.contains('btn') ||
                    current.classList.contains('button')) {
                    candidate = current;
                    break;
                }
                current = current.parentElement;
            }
        }
    }
    
    return candidate;
};

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'GET_DOM_SNAPSHOT') {
        const snapshot = getDOMSnapshot();
        sendResponse({ status: 'success', snapshot });
        return true;
    } else if (request.action === 'PERFORM_DOM_ACTION') {
        const { action_type, params } = request.data;
        console.log("Bridge收到动作:", action_type, params);

        try {
            let result = "操作成功";
            let element = null;

            if (params.x !== undefined && params.y !== undefined) {
                let x, y;
                if (params.x <= 1 && params.y <= 1) {
                    x = params.x * window.innerWidth;
                    y = params.y * window.innerHeight;
                } else if (params.x <= 1000 && params.y <= 1000) {
                    x = (params.x / 1000) * window.innerWidth;
                    y = (params.y / 1000) * window.innerHeight;
                } else {
                    x = params.x;
                    y = params.y;
                }
                console.log(`通过坐标查找元素: 原始(${params.x}, ${params.y}) -> 计算(${x}, ${y})`);
                element = findElementByCoords(x, y, action_type);
            }

            console.log("执行动作:", action_type, "元素:", element);
            
            if (action_type === 'click') {
                if (element) {
                    element.focus?.();
                    element.click();
                    element.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                    console.log("点击元素成功:", element.tagName, element.className);
                } else {
                    result = "未找到要点击的元素";
                    console.log("点击失败：未找到元素");
                }
            } else if (action_type === 'type') {
                if (element) {
                    element.focus();
                    const text = params.text || '';
                    
                    if (element.tagName === 'TEXTAREA' || (element.tagName === 'INPUT' && !['submit', 'button', 'reset', 'image'].includes(element.type?.toLowerCase()))) {
                        element.value = '';
                        element.value = text;
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                        element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
                    } else if (element.isContentEditable || element.getAttribute('contenteditable') === 'true') {
                        element.innerText = text;
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                    } else {
                        result = '目标元素不是可输入元素';
                    }
                    console.log("输入文本成功:", text);
                } else {
                    result = "未找到要输入的元素";
                }
            } else if (action_type === 'scroll') {
                const distance = params.direction === 'down' ? 500 : -500;
                window.scrollBy({ top: distance, behavior: 'smooth' });
            } else if (action_type === 'navigate') {
                let url = params.url;
                if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
                    url = `https://${url}`;
                }
                window.location.href = url;
            } else if (action_type === 'backtrack') {
                window.history.back();
            } else {
                result = "未知动作类型: " + action_type;
            }

            setTimeout(() => {
                sendResponse({ status: "success", result });
            }, 600);

        } catch (e) {
            console.error("Bridge failure:", e);
            sendResponse({ status: "error", message: e.message });
        }
        return true;
    }
});
