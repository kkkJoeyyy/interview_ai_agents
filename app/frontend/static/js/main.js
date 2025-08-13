// 初始化
let currentKB = '';
const chatContainer = document.getElementById('chat-container');
const kbModal = new bootstrap.Modal('#kb-modal');
const uploadModal = new bootstrap.Modal('#upload-modal');

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
    
    // 如果没有知识库，设置默认选中第一个
    if (kbs.length > 0 && !currentKB) {
        currentKB = kbs[0];
    }
    
    list.innerHTML = kbs.map(kb => `
        <li class="list-group-item d-flex justify-content-between align-items-center
            ${kb === currentKB ? 'active' : ''}"
            data-kb="${kb}">
            ${kb.charAt(0).toUpperCase() + kb.slice(1)}
            <button class="btn btn-sm btn-danger" onclick="deleteKB('${kb}')">
                <i class="bi bi-trash"></i>
            </button>
        </li>
    `).join('');
    
    // 如果没有知识库，显示提示
    if (kbs.length === 0) {
        list.innerHTML = '<li class="list-group-item text-muted">暂无知识库，请创建新知识库</li>';
    }
    
    // 添加点击事件
    document.querySelectorAll('#kb-list .list-group-item').forEach(item => {
        if (item.dataset.kb) {
            item.addEventListener('click', () => selectKB(item.dataset.kb));
        }
    });
    
    // 更新当前知识库显示
    updateCurrentKBDisplay();
}

// 选择知识库
function selectKB(kb) {
    currentKB = kb;
    loadKnowledgeBases();
    clearChat();
    
    updateCurrentKBDisplay();
}

// 删除知识库
async function deleteKB(kb) {
    if (!confirm(`确定删除知识库 "${kb}" 吗？此操作不可恢复！`)) return;
    
    try {
        const response = await axios.delete(`/delete_kb/${kb}`);
        
        if (response.data.status === 'success') {
            showSuccess(response.data.message);
                    // 如果删除的是当前选中的知识库，重新选择
        if (currentKB === kb) {
            currentKB = '';
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
            // 传递元数据给前端显示
            const metadata = {
                confidence: response.data.confidence,
                matched_kbs: response.data.matched_kbs,
                context_length: response.data.context_length
            };
            addMessage(response.data.answer, false, metadata);
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

// 简单的Markdown转HTML函数
function markdownToHtml(text) {
    if (!text) return '';
    
    let html = text
        // 代码块
        .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        // 行内代码
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // 标题
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        // 加粗
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // 斜体
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // 有序列表
        .replace(/^\d+\.\s(.*)$/gm, '<li>$1</li>')
        // 无序列表
        .replace(/^[-*+]\s(.*)$/gm, '<li>$1</li>')
        // 换行
        .replace(/\n/g, '<br>');
    
    // 包装连续的列表项
    html = html.replace(/(<li>.*?<\/li>(<br>)*)+/gs, function(match) {
        return '<ul>' + match.replace(/<br>/g, '') + '</ul>';
    });
    
    return html;
}

// 添加消息
function addMessage(text, isUser, metadata = {}) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${isUser ? 'user-bubble' : 'bot-bubble'}`;
    
    if (isUser) {
        bubble.textContent = text;
    } else {
        // 对AI回答进行Markdown渲染
        const formattedContent = markdownToHtml(text);
        bubble.innerHTML = formattedContent;
        
        // 添加元数据信息
        if (metadata.confidence && metadata.matched_kbs) {
            const metadataDiv = document.createElement('div');
            metadataDiv.className = 'answer-metadata';
            metadataDiv.innerHTML = `
                <small class="text-muted mt-2 d-block">
                    <i class="bi bi-info-circle"></i>
                    置信度: ${(metadata.confidence * 100).toFixed(1)}% | 
                    知识库: ${metadata.matched_kbs.join(', ')} |
                    上下文: ${metadata.context_length || 0}字符
                </small>
            `;
            bubble.appendChild(metadataDiv);
        }
    }
    
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

// 更新当前知识库显示
function updateCurrentKBDisplay() {
    const currentKBElement = document.getElementById('current-kb-name');
    const targetKBElement = document.getElementById('target-kb');
    
    if (currentKB) {
        const displayName = currentKB.charAt(0).toUpperCase() + currentKB.slice(1);
        if (currentKBElement) {
            currentKBElement.textContent = displayName;
        }
        if (targetKBElement) {
            targetKBElement.textContent = displayName;
        }
    } else {
        if (currentKBElement) {
            currentKBElement.textContent = '请选择知识库';
        }
        if (targetKBElement) {
            targetKBElement.textContent = '请选择知识库';
        }
    }
}

// 显示上传进度
function showUploadProgress(percent) {
    const progressContainer = document.getElementById('upload-progress');
    const progressBar = progressContainer.querySelector('.progress-bar');
    
    progressContainer.style.display = 'block';
    progressBar.style.width = percent + '%';
    progressBar.textContent = percent + '%';
    
    // 禁用上传按钮
    const uploadBtn = document.getElementById('btn-upload-file');
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> 上传中...';
}

// 隐藏上传进度
function hideUploadProgress() {
    const progressContainer = document.getElementById('upload-progress');
    progressContainer.style.display = 'none';
    
    // 恢复上传按钮
    const uploadBtn = document.getElementById('btn-upload-file');
    uploadBtn.disabled = false;
    uploadBtn.innerHTML = '上传';
}



// 事件监听
document.getElementById('btn-send').addEventListener('click', submitQuestion);
document.getElementById('question-input').addEventListener('keypress', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitQuestion();
    }
});

// PDF上传功能
async function uploadPDF() {
    const fileInput = document.getElementById('pdf-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('请选择PDF文件');
        return;
    }
    
    if (!currentKB) {
        showError('请先选择知识库');
        return;
    }
    
    if (file.type !== 'application/pdf') {
        showError('请选择PDF格式的文件');
        return;
    }
    
    if (file.size > 50 * 1024 * 1024) { // 50MB
        showError('文件大小不能超过50MB');
        return;
    }

    try {
        // 显示上传进度
        showUploadProgress(0);
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('knowledge_base_name', currentKB);
        
        const response = await axios.post('/upload_pdf/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            },
            onUploadProgress: (progressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                showUploadProgress(percentCompleted);
            }
        });
        
        hideUploadProgress();
        
        if (response.data.status === 'success') {
            showSuccess(response.data.message);
            fileInput.value = '';
            uploadModal.hide();
        } else {
            showError(response.data.message);
        }
    } catch (error) {
        hideUploadProgress();
        console.error('上传PDF失败:', error);
        showError('上传PDF失败: ' + (error.response?.data?.message || error.message));
    }
}

document.getElementById('btn-new-kb').addEventListener('click', () => kbModal.show());
document.getElementById('btn-upload-pdf').addEventListener('click', () => {
    // 更新模态框显示的目标知识库
    const targetKBElement = document.getElementById('target-kb');
    if (targetKBElement) {
        targetKBElement.textContent = currentKB.charAt(0).toUpperCase() + currentKB.slice(1);
    }
    uploadModal.show();
});

document.getElementById('btn-upload-file').addEventListener('click', uploadPDF);

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