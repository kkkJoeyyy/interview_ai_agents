// 初始化
let currentKB = 'global';
const chatContainer = document.getElementById('chat-container');
const kbModal = new bootstrap.Modal('#kb-modal');

// 加载知识库列表
async function loadKnowledgeBases() {
    try {
        const response = await axios.get('/knowledge_bases');
        if (response.data.status === 'success') {
            renderKBList(response.data.data);
        } else {
            showError(response.data.message || '加载知识库失败');
        }
    } catch (error) {
        console.error('加载知识库失败:', error);
        showError('加载知识库失败');
    }
}

// 渲染知识库列表
function renderKBList(kbs) {
    const list = document.getElementById('kb-list');
    list.innerHTML = kbs.map(kb => `
        <li class="list-group-item d-flex justify-content-between align-items-center
            ${kb === currentKB ? 'active' : ''}"
            data-kb="${kb}">
            ${kb}
            ${kb !== 'global' ? 
                `<button class="btn btn-sm btn-danger" onclick="deleteKB('${kb}')">
                    <i class="bi bi-trash"></i>
                </button>` : ''
            }
        </li>
    `).join('');
    
    // 添加点击事件
    document.querySelectorAll('#kb-list .list-group-item').forEach(item => {
        item.addEventListener('click', () => selectKB(item.dataset.kb));
    });
}

// 选择知识库
function selectKB(kb) {
    currentKB = kb;
    loadKnowledgeBases();
    clearChat();
}

// 删除知识库
async function deleteKB(kb) {
    if (!confirm(`确定删除知识库 "${kb}" 吗？此操作不可恢复！`)) return;
    
    try {
        const response = await axios.delete(`/delete_kb/${kb}`);
        
        if (response.data.status === 'success') {
            showSuccess(response.data.message);
            // 如果删除的是当前选中的知识库，切换到global
            if (currentKB === kb) {
                currentKB = 'global';
                clearChat();
            }
            loadKnowledgeBases();
        } else {
            showError(response.data.message);
        }
    } catch (error) {
        console.error('删除知识库失败:', error);
        showError('删除知识库失败');
    }
}

// 修改submitQuestion函数
async function submitQuestion() {
    const input = document.getElementById('question-input');
    const question = input.value.trim();
    
    if (!question) return;
    
    addMessage(question, true);
    input.value = '';
    showLoading();

    try {
        const response = await axios.get(`/ask/`, {
            params: { 
                question: encodeURIComponent(question),
                kb: currentKB 
            }
        });

        if (response.data?.answer) {
            addMessage(response.data.answer, false);
        } else if (response.data?.status === 'error') {
            addMessage(`系统错误：${response.data.message}`, false);
        } else {
            addMessage("未获取到有效回答，请尝试重新表述问题", false);
        }
    } catch (error) {
        console.error('请求失败:', error);
        addMessage("网络请求失败，请检查连接后重试", false); 
    } finally {
        hideLoading();
    }
}

// 添加消息
function addMessage(text, isUser) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${isUser ? 'user-bubble' : 'bot-bubble'}`;
    bubble.textContent = text;
    chatContainer.appendChild(bubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 清空聊天
function clearChat() {
    chatContainer.innerHTML = '';
}

// 错误处理
function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger position-fixed top-0 end-0 m-3';
    alert.innerHTML = `<strong>错误：</strong>${message}`;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}

// 成功提示
function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success position-fixed top-0 end-0 m-3';
    alert.innerHTML = `<strong>成功：</strong>${message}`;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 3000);
}

// 加载状态
function showLoading() {
    const loading = document.createElement('div');
    loading.id = 'loading-indicator';
    loading.className = 'text-center p-3';
    loading.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div>';
    chatContainer.appendChild(loading);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function hideLoading() {
    const loading = document.getElementById('loading-indicator');
    if (loading) loading.remove();
}



// 事件监听
document.getElementById('btn-send').addEventListener('click', submitQuestion);
document.getElementById('question-input').addEventListener('keypress', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitQuestion();
    }
});

document.getElementById('btn-new-kb').addEventListener('click', () => kbModal.show());
document.getElementById('btn-create-kb').addEventListener('click', async () => {
    const kbName = document.getElementById('kb-name').value.trim();
    if (!kbName) {
        showError('请输入知识库名称');
        return;
    }

    try {
        const response = await axios.post('/create_kb', { name: kbName });
        
        if (response.data.status === 'success') {
            showSuccess(response.data.message);
            document.getElementById('kb-name').value = '';
            kbModal.hide();
            loadKnowledgeBases();
        } else {
            showError(response.data.message);
        }
    } catch (error) {
        console.error('创建知识库失败:', error);
        showError('创建知识库失败');
    }
});

// 初始化
loadKnowledgeBases();