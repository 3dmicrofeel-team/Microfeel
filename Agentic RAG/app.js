// 配置管理
const config = {
    model: 'gpt-4.1',
    temperature: 0.7,
    maxTokens: 4000,
    topP: 0.9,
    frequencyPenalty: 0.0,
    presencePenalty: 0.0,
    agentMode: 'standard',
    maxIterations: 3,
    apiKey: '', // API密钥
    generationMode: 'map' // 生成模式：map或encounter
};

// 从URL参数获取后端端口，或使用localStorage，默认5000
function getBackendPort() {
    const urlParams = new URLSearchParams(window.location.search);
    const portFromUrl = urlParams.get('backendPort');
    if (portFromUrl) {
        localStorage.setItem('backendPort', portFromUrl);
        return portFromUrl;
    }
    return localStorage.getItem('backendPort') || '5000';
}

// DOM元素
const elements = {
    apiKey: document.getElementById('api-key'),
    saveApiKeyBtn: document.getElementById('save-api-key-btn'),
    clearApiKeyBtn: document.getElementById('clear-api-key-btn'),
    toggleApiKeyBtn: document.getElementById('toggle-api-key-btn'),
    apiKeyStatus: document.getElementById('api-key-status'),
    generationMode: document.getElementById('generation-mode'),
    npcTagsGroup: document.getElementById('npc-tags-group'),
    npcTags: document.getElementById('npc-tags'),
    modelSelect: document.getElementById('model-select'),
    temperature: document.getElementById('temperature'),
    maxTokens: document.getElementById('max-tokens'),
    topP: document.getElementById('top-p'),
    frequencyPenalty: document.getElementById('frequency-penalty'),
    presencePenalty: document.getElementById('presence-penalty'),
    agentMode: document.getElementById('agent-mode'),
    maxIterations: document.getElementById('max-iterations'),
    userInput: document.getElementById('user-input'),
    generateBtn: document.getElementById('generate-btn'),
    clearBtn: document.getElementById('clear-btn'),
    exampleBtn: document.getElementById('example-btn'),
    outputContainer: document.getElementById('output-container'),
    copyBtn: document.getElementById('copy-btn'),
    downloadBtn: document.getElementById('download-btn'),
    formatBtn: document.getElementById('format-btn'),
    statusBar: document.getElementById('status-bar'),
    progressFill: document.getElementById('progress-fill'),
    tempValue: document.getElementById('temp-value'),
    tokensValue: document.getElementById('tokens-value'),
    toppValue: document.getElementById('topp-value'),
    freqValue: document.getElementById('freq-value'),
    presValue: document.getElementById('pres-value'),
    iterValue: document.getElementById('iter-value')
};

// 示例输入（地图模式）
const exampleInputMap = `创建一个新手村地图，包含：

- 中央有一个中世纪风格的村庄，包含：
  * 一个两层楼的酒馆，有自动装饰
  * 一个商店，出售一般物品
  * 一个铁匠铺，面向东方
  * 一个任务发布NPC，位于村庄中心
  * 一口水井和公告板
  * 玩家出生点

- 村庄北边是一片迷雾森林，包含：
  * 8只狼和5只哥布林作为敌人
  * 一个隐藏的宝箱
  * 一些可采集的草药节点

- 村庄东南角有一个废弃矿洞入口，包含：
  * 需要完成特定任务才能进入（检查Player:HasFlag('Mine_Unlocked')）
  * 3-8级的怪物等级

- 村庄东边有一个训练场

- 西北角有一个湖泊，湖边有渔夫小屋

- 地形特征：
  * 中央略微隆起
  * 东南角有小山
  * 西北角有湖泊
  * 需要平滑地形

- 连接：
  * 村庄到训练场：石路
  * 村庄到森林：土路
  * 村庄到矿洞：土路
  * 村庄到湖边小屋：小径

- 氛围设置：
  * 上午10点，晴天
  * 自然和平的音效
  * 森林有神秘的氛围光效`;

// 示例输入（奇遇模式）
const exampleInputEncounter = `我想要一个在酒馆发生的偷窃事件，玩家可以选择介入、旁观或离开。`;

// 当前示例输入（已废弃，使用exampleInputMap和exampleInputEncounter）

// API Key管理
function loadApiKey() {
    const savedKey = localStorage.getItem('openai_api_key');
    if (savedKey) {
        config.apiKey = savedKey;
        // 显示部分密钥（前8个字符 + ...）
        const maskedKey = savedKey.substring(0, 8) + '...' + savedKey.substring(savedKey.length - 4);
        elements.apiKey.value = maskedKey;
        elements.apiKeyStatus.textContent = '已保存API Key: ' + maskedKey;
        elements.apiKeyStatus.className = 'api-key-status saved';
    }
}

function saveApiKey() {
    const apiKey = elements.apiKey.value.trim();
    if (!apiKey) {
        elements.apiKeyStatus.textContent = '请输入API Key';
        elements.apiKeyStatus.className = 'api-key-status warning';
        setTimeout(() => {
            elements.apiKeyStatus.className = 'api-key-status';
            elements.apiKeyStatus.style.display = 'none';
        }, 3000);
        return;
    }
    
    // 如果输入的是掩码格式，不保存
    if (apiKey.includes('...') && apiKey.length < 20) {
        elements.apiKeyStatus.textContent = '请输入完整的API Key';
        elements.apiKeyStatus.className = 'api-key-status warning';
        setTimeout(() => {
            elements.apiKeyStatus.className = 'api-key-status';
            elements.apiKeyStatus.style.display = 'none';
        }, 3000);
        return;
    }
    
    localStorage.setItem('openai_api_key', apiKey);
    config.apiKey = apiKey;
    
    const maskedKey = apiKey.substring(0, 8) + '...' + apiKey.substring(apiKey.length - 4);
    elements.apiKey.value = maskedKey;
    elements.apiKey.type = 'password';
    elements.toggleApiKeyBtn.textContent = '👁️ 显示';
    
    elements.apiKeyStatus.textContent = 'API Key已保存';
    elements.apiKeyStatus.className = 'api-key-status saved';
    setTimeout(() => {
        elements.apiKeyStatus.style.display = 'none';
    }, 3000);
}

function clearApiKey() {
    localStorage.removeItem('openai_api_key');
    config.apiKey = '';
    elements.apiKey.value = '';
    elements.apiKeyStatus.textContent = 'API Key已清除';
    elements.apiKeyStatus.className = 'api-key-status cleared';
    setTimeout(() => {
        elements.apiKeyStatus.style.display = 'none';
    }, 3000);
}

function toggleApiKeyVisibility() {
    const currentType = elements.apiKey.type;
    const currentValue = elements.apiKey.value;
    
    if (currentType === 'password') {
        // 如果是掩码格式，显示完整密钥
        if (currentValue.includes('...')) {
            const savedKey = localStorage.getItem('openai_api_key');
            if (savedKey) {
                elements.apiKey.value = savedKey;
            }
        }
        elements.apiKey.type = 'text';
        elements.toggleApiKeyBtn.textContent = '🙈 隐藏';
    } else {
        // 隐藏时，如果已保存则显示掩码
        const savedKey = localStorage.getItem('openai_api_key');
        if (savedKey && currentValue === savedKey) {
            const maskedKey = savedKey.substring(0, 8) + '...' + savedKey.substring(savedKey.length - 4);
            elements.apiKey.value = maskedKey;
        }
        elements.apiKey.type = 'password';
        elements.toggleApiKeyBtn.textContent = '👁️ 显示';
    }
}

// 初始化
function init() {
    // 加载保存的API Key
    loadApiKey();
    
    // API Key相关事件
    elements.saveApiKeyBtn.addEventListener('click', saveApiKey);
    elements.clearApiKeyBtn.addEventListener('click', clearApiKey);
    elements.toggleApiKeyBtn.addEventListener('click', toggleApiKeyVisibility);
    
    // API Key输入框回车保存
    elements.apiKey.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            saveApiKey();
        }
    });
    
    // 绑定事件监听器
    elements.modelSelect.addEventListener('change', (e) => {
        config.model = e.target.value;
    });

    elements.temperature.addEventListener('input', (e) => {
        config.temperature = parseFloat(e.target.value);
        elements.tempValue.textContent = config.temperature.toFixed(1);
    });

    elements.maxTokens.addEventListener('input', (e) => {
        config.maxTokens = parseInt(e.target.value);
        elements.tokensValue.textContent = config.maxTokens;
    });

    elements.topP.addEventListener('input', (e) => {
        config.topP = parseFloat(e.target.value);
        elements.toppValue.textContent = config.topP.toFixed(2);
    });

    elements.frequencyPenalty.addEventListener('input', (e) => {
        config.frequencyPenalty = parseFloat(e.target.value);
        elements.freqValue.textContent = config.frequencyPenalty.toFixed(1);
    });

    elements.presencePenalty.addEventListener('input', (e) => {
        config.presencePenalty = parseFloat(e.target.value);
        elements.presValue.textContent = config.presencePenalty.toFixed(1);
    });

    elements.agentMode.addEventListener('change', (e) => {
        config.agentMode = e.target.value;
    });

    elements.maxIterations.addEventListener('input', (e) => {
        config.maxIterations = parseInt(e.target.value);
        elements.iterValue.textContent = config.maxIterations;
    });

    // 生成模式切换
    elements.generationMode.addEventListener('change', (e) => {
        const mode = e.target.value;
        config.generationMode = mode;
        
        // 显示/隐藏NPC标签输入
        if (mode === 'encounter') {
            elements.npcTagsGroup.style.display = 'block';
            elements.userInput.placeholder = '请输入你对奇遇的要求，例如：我想要一个在酒馆发生的偷窃事件，玩家可以选择介入、旁观或离开。';
        } else {
            elements.npcTagsGroup.style.display = 'none';
            elements.userInput.placeholder = '请输入你对地图的要求，例如：创建一个新手村地图，包含村庄、森林、矿洞等区域...';
        }
    });
    
    // 初始化模式显示
    const initialMode = elements.generationMode.value || 'map';
    if (initialMode === 'encounter') {
        elements.npcTagsGroup.style.display = 'block';
        elements.userInput.placeholder = '请输入你对奇遇的要求，例如：我想要一个在酒馆发生的偷窃事件，玩家可以选择介入、旁观或离开。';
    } else {
        elements.userInput.placeholder = '请输入你对地图的要求，例如：创建一个新手村地图，包含村庄、森林、矿洞等区域...';
    }

    elements.generateBtn.addEventListener('click', handleGenerate);
    elements.clearBtn.addEventListener('click', handleClear);
    elements.exampleBtn.addEventListener('click', handleLoadExample);
    elements.copyBtn.addEventListener('click', handleCopy);
    elements.downloadBtn.addEventListener('click', handleDownload);
    elements.formatBtn.addEventListener('click', handleFormat);
}

// 处理生成
async function handleGenerate() {
    const userInput = elements.userInput.value.trim();
    const generationMode = elements.generationMode.value || 'map';
    
    if (!userInput) {
        alert(generationMode === 'encounter' ? '请输入奇遇描述！' : '请输入地图描述！');
        return;
    }

    // 显示状态栏
    elements.statusBar.classList.remove('hidden');
    elements.generateBtn.disabled = true;
    elements.generateBtn.innerHTML = '<span class="btn-icon">⏳</span> 生成中...';

    // 模拟进度
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        elements.progressFill.style.width = progress + '%';
    }, 500);

    try {
        // 调用后端API（自动检测后端端口）
        const backendPort = getBackendPort();
        const apiUrl = `http://localhost:${backendPort}/api/generate`;
        
        // 准备请求数据（包含API Key）
        // 始终从localStorage获取真实密钥（如果已保存）
        const savedApiKey = localStorage.getItem('openai_api_key') || '';
        
        // 解析NPC标签（奇遇模式）
        let npcTags = null;
        if (generationMode === 'encounter') {
            const npcTagsInput = elements.npcTags.value.trim();
            if (npcTagsInput) {
                npcTags = npcTagsInput.split(',').map(tag => tag.trim()).filter(tag => tag);
            }
        }
        
        const requestData = {
            input: userInput,
            mode: generationMode,
            npcTags: npcTags,
            config: {
                model: config.model,
                temperature: config.temperature,
                maxTokens: config.maxTokens,
                topP: config.topP,
                frequencyPenalty: config.frequencyPenalty,
                presencePenalty: config.presencePenalty,
                agentMode: config.agentMode,
                maxIterations: config.maxIterations,
                apiKey: savedApiKey || null  // 如果未设置则为null，后端会使用环境变量或模拟数据
            }
        };
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // 完成进度
        clearInterval(progressInterval);
        elements.progressFill.style.width = '100%';

        // 显示结果
        setTimeout(() => {
            displayResult(data.luaScript || data.error || '生成失败，请重试');
            elements.statusBar.classList.add('hidden');
            elements.generateBtn.disabled = false;
            elements.generateBtn.innerHTML = '<span class="btn-icon">🚀</span> 生成LUA脚本';
        }, 500);

    } catch (error) {
        console.error('Error:', error);
        
        // 显示错误或使用模拟数据
        clearInterval(progressInterval);
        elements.progressFill.style.width = '100%';
        
        setTimeout(() => {
            // 如果后端未实现，使用模拟数据
            const mockScript = generateMockScript(userInput);
            displayResult(mockScript);
            elements.statusBar.classList.add('hidden');
            elements.generateBtn.disabled = false;
            elements.generateBtn.innerHTML = '<span class="btn-icon">🚀</span> 生成LUA脚本';
            
            // 显示提示
            showNotification('注意：当前使用模拟数据。请配置后端API以使用真实的Agentic RAG系统。', 'info');
        }, 500);
    }
}

// 生成模拟脚本（用于演示）
function generateMockScript(userInput) {
    // 这是一个简化的模拟生成器，实际应该由后端Agentic RAG系统处理
    return `function CreateStarterZone()
    local map = Env.CreateMap(100, 100, 100)
    Env.SetMapName(map, "新手平原")
    Env.SetMapTheme(map, "Medieval")

    -- 根据用户输入生成的地图
    -- 输入: ${userInput.substring(0, 100)}...

    Env.RaiseTerrain(map, {X=50, Y=50}, 30, 200, 0.8)
    Env.SmoothTerrain(map, 3)

    local villageBlock = Env.AddBlock(map, "新手村", {X=35, Y=30}, {X=30, Y=25})
    Env.SetBlockType(villageBlock, "Village")
    Env.SetBlockProperty(villageBlock, "SafeZone", "true")

    Env.FlattenTerrain(map, {X=50, Y=42}, 12, 50)

    local inn = Env.AddBuilding(villageBlock, {X=5, Y=5}, {X=5, Y=4}, "Medieval", {Pitch=0, Yaw=0, Roll=0})
    Env.SetBuildingType(inn, "Tavern")
    Env.AddBuildingFloor(inn, 300)
    Env.AddBuildingFloor(inn, 300)
    Env.SetBuildingRoof(inn, "Pitched")
    Env.AutoFurnishBuilding(inn, "Tavern")

    Env.AddNPCSpawn(villageBlock, "NPC_QuestGiver", {X=1200, Y=400, Z=0}, {Pitch=0, Yaw=0, Roll=0})
    Env.AddSpawnPoint(villageBlock, "PlayerStart", {X=1000, Y=200, Z=0}, {Pitch=0, Yaw=0, Roll=0})

    local errors = Env.ValidateMap(map)
    if #errors > 0 then
        for _, err in ipairs(errors) do
            Log("[错误] " .. err)
        end
        return nil
    end

    Env.SaveMap(map, "StarterZone_v1")

    Env.BuildAsync(map, function(levelRoot)
        Log("关卡构建完成！")
        OnLevelReady(levelRoot)
    end)

    return map
end

function OnLevelReady(levelRoot)
    local spawnPos = World.GetSpawnPoint("PlayerStart")
    local player = World.SpawnPlayer(spawnPos)
end`;
}

// 显示结果
function displayResult(script) {
    elements.outputContainer.innerHTML = `<pre class="code-block"><code>${escapeHtml(script)}</code></pre>`;
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 清空输入
function handleClear() {
    elements.userInput.value = '';
    elements.outputContainer.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">📜</div>
            <p>生成的LUA脚本将显示在这里</p>
            <p class="empty-hint">输入你的地图需求，然后点击"生成LUA脚本"按钮</p>
        </div>
    `;
}

// 加载示例
function handleLoadExample() {
    const generationMode = elements.generationMode.value || 'map';
    if (generationMode === 'encounter') {
        elements.userInput.value = exampleInputEncounter;
    } else {
        elements.userInput.value = exampleInputMap;
    }
}

// 复制代码
function handleCopy() {
    const code = elements.outputContainer.querySelector('code');
    if (!code) {
        showNotification('没有可复制的内容', 'warning');
        return;
    }

    navigator.clipboard.writeText(code.textContent).then(() => {
        showNotification('代码已复制到剪贴板', 'success');
    }).catch(err => {
        console.error('复制失败:', err);
        showNotification('复制失败', 'error');
    });
}

// 下载文件
function handleDownload() {
    const code = elements.outputContainer.querySelector('code');
    if (!code) {
        showNotification('没有可下载的内容', 'warning');
        return;
    }

    const blob = new Blob([code.textContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `map_script_${Date.now()}.lua`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('文件已下载', 'success');
}

// 格式化代码
function handleFormat() {
    const code = elements.outputContainer.querySelector('code');
    if (!code) {
        showNotification('没有可格式化的内容', 'warning');
        return;
    }

    // 简单的格式化（实际可以使用更专业的格式化库）
    let formatted = code.textContent
        .replace(/\n{3,}/g, '\n\n')  // 移除多余空行
        .replace(/\s+$/gm, '')       // 移除行尾空格
        .trim();

    displayResult(formatted);
    showNotification('代码已格式化', 'success');
}

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#6366f1'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// 页面加载时检测后端端口
document.addEventListener('DOMContentLoaded', function() {
    // 从URL参数获取后端端口
    const urlParams = new URLSearchParams(window.location.search);
    const backendPort = urlParams.get('backendPort');
    if (backendPort) {
        localStorage.setItem('backendPort', backendPort);
        console.log('Backend port set to:', backendPort);
    }
    
    // 初始化应用
    init();
});
