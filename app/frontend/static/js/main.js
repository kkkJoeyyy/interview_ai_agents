// 初始化
let currentKB = 'global';
const chatContainer = document.getElementById('chat-container');
const kbModal = new bootstrap.Modal('#kb-modal');

// 加载知识库列表
async function loadKnowledgeBases() {
    try {
        const { data } = await axios.get('/knowledge_bases');
        renderKBList(data);
    } catch (error) {
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
    if (!confirm(`确定删除知识库 "${kb}" 吗？`)) return;
    
    try {
        await axios.delete(`/delete_kb/${kb}`);
        loadKnowledgeBases();
    } catch (error) {
        showError('删除知识库失败');
    }
}

// 修改submitQuestion函数
async function submitQuestion() {
    const input = document.getElementById('question-input');
    const question = input.value.trim(); // 确保在这里定义question
    
    if (!question) return;
    showLoading();

    try {
        addMessage(question, true);
        input.value = ''; // 清空输入框

        const response = await axios.get(`/ask/`, {
            params: { 
                question: encodeURIComponent(question), // 显式编码
                kb: currentKB 
            }
        });

        if (response.data?.answer) {
            addMessage(response.data.answer, false);
        } else {
            addMessage("未获取到有效回答", false);
        }
    } catch (error) {
        console.error('请求失败:', error);
        // 修复错误引用，使用固定提示
        addMessage("请求失败，请检查网络连接", false); 
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
    alert.textContent = message;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 3000);
}

// 添加加载动画
function showLoading() {
    const loading = document.createElement('div');
    loading.id = 'loading';
    loading.innerHTML = '<div class="spinner-border text-primary"></div>';
    chatContainer.appendChild(loading);
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
    if (!kbName) return;

    try {
        await axios.post('/create_kb', { name: kbName });
        kbModal.hide();
        loadKnowledgeBases();
    } catch (error) {
        showError('创建知识库失败');
    }
});

// 初始化
loadKnowledgeBases();