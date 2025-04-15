// SNS Poster App - Main JavaScript

// APIエンドポイント
const API_URL = {
    PLATFORMS: '/api/platforms',
    CHARACTER_LIMITS: '/api/character_limits',
    POST: '/api/post'
};

// グローバル変数
let platforms = {}; // 利用可能なプラットフォーム
let characterLimits = {}; // 文字数制限
let postMode = 'unified'; // 投稿モード (unified or individual)

// DOMが読み込まれた後に実行
document.addEventListener('DOMContentLoaded', function() {
    // 初期化
    initApp();

    // モード切り替えボタンのイベントリスナー
    document.getElementById('unified-mode-btn').addEventListener('click', () => switchMode('unified'));
    document.getElementById('individual-mode-btn').addEventListener('click', () => switchMode('individual'));

    // 投稿ボタンのイベントリスナー
    document.getElementById('post-button').addEventListener('click', handlePost);
});

// アプリ初期化
async function initApp() {
    try {
        // 利用可能なプラットフォームを取得
        platforms = await fetchPlatforms();

        // 文字数制限を取得
        characterLimits = await fetchCharacterLimits();

        // プラットフォーム選択UIを生成
        renderPlatformSelectors();

        // 一括投稿モードの文字数カウント設定
        setupUnifiedModeCounters();

        // 初期状態は一括投稿モード
        switchMode('unified');
    } catch (error) {
        showError('アプリの初期化中にエラーが発生しました: ' + error.message);
    }
}

// プラットフォーム情報を取得
async function fetchPlatforms() {
    const response = await fetch(API_URL.PLATFORMS);
    if (!response.ok) {
        throw new Error(`プラットフォーム情報の取得に失敗しました: ${response.status}`);
    }
    return await response.json();
}

// 文字数制限を取得
async function fetchCharacterLimits() {
    const response = await fetch(API_URL.CHARACTER_LIMITS);
    if (!response.ok) {
        throw new Error(`文字数制限の取得に失敗しました: ${response.status}`);
    }
    return await response.json();
}

// プラットフォーム選択UIの生成
function renderPlatformSelectors() {
    const container = document.getElementById('platforms-container');
    container.innerHTML = '';

    Object.keys(platforms).forEach(platform => {
        const platformInfo = platforms[platform];
        const card = document.createElement('div');
        card.className = `platform-card ${platformInfo.enabled ? 'enabled' : 'disabled'}`;
        card.dataset.platform = platform;

        if (platformInfo.enabled) {
            card.addEventListener('click', () => togglePlatformSelection(card));
        }

        // プラットフォーム名（先頭を大文字に）
        const displayName = platform.charAt(0).toUpperCase() + platform.slice(1);

        card.innerHTML = `
            <div class="platform-name">${displayName}</div>
            <div class="platform-status">${platformInfo.enabled ? '連携済み' : '未連携'}</div>
            <div class="platform-limit">最大 ${platformInfo.limit} 文字</div>
        `;

        container.appendChild(card);
    });
}

// プラットフォーム選択の切り替え
function togglePlatformSelection(card) {
    // 無効化されたプラットフォームは選択不可
    if (card.classList.contains('disabled')) {
        return;
    }

    // 選択/非選択を切り替え
    card.classList.toggle('selected');

    // 選択状態に基づいて個別投稿モードのUIを更新
    updateIndividualPosts();
}

// 一括投稿モードの文字数カウンター設定
function setupUnifiedModeCounters() {
    const textarea = document.getElementById('unified-content');
    const counter = document.getElementById('unified-character-count');

    // 最も小さい文字数制限を見つける
    const minLimit = Math.min(...Object.values(characterLimits));
    textarea.setAttribute('maxlength', minLimit);

    // テキスト入力時のカウント更新
    textarea.addEventListener('input', function() {
        const length = this.value.length;
        counter.textContent = `${length} / ${minLimit}`;

        // 文字数が多い場合は警告表示
        if (length > minLimit * 0.9) {
            counter.style.color = '#e74c3c';
        } else {
            counter.style.color = '#666';
        }
    });
}

// 個別投稿モードのUI更新
function updateIndividualPosts() {
    const container = document.getElementById('individual-posts-container');
    container.innerHTML = '';

    // 選択されたプラットフォームのみ表示
    const selectedPlatforms = Array.from(document.querySelectorAll('.platform-card.selected'))
        .map(card => card.dataset.platform);

    if (selectedPlatforms.length === 0) {
        container.innerHTML = '<p>投稿先のSNSを選択してください</p>';
        return;
    }

    // 統一モードのテキストを取得（あれば）
    const unifiedText = document.getElementById('unified-content').value;

    selectedPlatforms.forEach(platform => {
        const limit = characterLimits[platform];
        const displayName = platform.charAt(0).toUpperCase() + platform.slice(1);

        const postDiv = document.createElement('div');
        postDiv.className = 'individual-post';
        postDiv.dataset.platform = platform;

        postDiv.innerHTML = `
            <div class="individual-post-header">
                <div class="individual-post-platform">${displayName}</div>
                <div class="platform-limit">最大 ${limit} 文字</div>
            </div>
            <div class="textarea-container">
                <textarea class="individual-content" data-platform="${platform}" placeholder="${displayName}に投稿する内容を入力..." maxlength="${limit}">${unifiedText}</textarea>
                <div class="character-count">${unifiedText.length} / ${limit}</div>
            </div>
        `;

        container.appendChild(postDiv);
    });

    // 個別の文字数カウンター設定
    setupIndividualCounters();
}

// 個別投稿モードの文字数カウンター設定
function setupIndividualCounters() {
    const textareas = document.querySelectorAll('.individual-content');

    textareas.forEach(textarea => {
        const platform = textarea.dataset.platform;
        const limit = characterLimits[platform];
        const counter = textarea.parentElement.querySelector('.character-count');

        textarea.addEventListener('input', function() {
            const length = this.value.length;
            counter.textContent = `${length} / ${limit}`;

            // 文字数が多い場合は警告表示
            if (length > limit * 0.9) {
                counter.style.color = '#e74c3c';
            } else {
                counter.style.color = '#666';
            }
        });
    });
}

// 投稿モードの切り替え
function switchMode(mode) {
    postMode = mode;

    // ボタンの状態更新
    document.getElementById('unified-mode-btn').classList.toggle('active', mode === 'unified');
    document.getElementById('individual-mode-btn').classList.toggle('active', mode === 'individual');

    // モードに応じたUI表示切り替え
    document.getElementById('unified-mode').classList.toggle('hidden', mode !== 'unified');
    document.getElementById('individual-mode').classList.toggle('hidden', mode !== 'individual');

    // 個別投稿モードの場合、UIを更新
    if (mode === 'individual') {
        updateIndividualPosts();
    }
}

// 投稿処理
async function handlePost() {
    // 投稿ボタンを無効化
    const postButton = document.getElementById('post-button');
    postButton.disabled = true;
    postButton.textContent = '投稿中...';

    try {
        // 選択されたプラットフォームを取得
        const selectedPlatforms = Array.from(document.querySelectorAll('.platform-card.selected'))
            .map(card => card.dataset.platform);

        if (selectedPlatforms.length === 0) {
            throw new Error('投稿先のSNSを選択してください');
        }

        // 投稿データの準備
        const postData = {};

        if (postMode === 'unified') {
            // 一括投稿モードの場合
            const content = document.getElementById('unified-content').value;

            if (!content.trim()) {
                throw new Error('投稿内容を入力してください');
            }

            // 全選択プラットフォームに同じ内容を設定
            selectedPlatforms.forEach(platform => {
                postData[platform] = {
                    selected: true,
                    content: content
                };
            });
        } else {
            // 個別投稿モードの場合
            selectedPlatforms.forEach(platform => {
                const textarea = document.querySelector(`.individual-content[data-platform="${platform}"]`);
                const content = textarea ? textarea.value : '';

                postData[platform] = {
                    selected: true,
                    content: content
                };

                // 内容が空の場合はエラー
                if (!content.trim()) {
                    throw new Error(`${platform.charAt(0).toUpperCase() + platform.slice(1)}の投稿内容を入力してください`);
                }
            });
        }

        // APIに投稿リクエスト送信
        const response = await fetch(API_URL.POST, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(postData)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || '投稿に失敗しました');
        }

        // 投稿結果の表示
        showPostResult(result);

    } catch (error) {
        showError(error.message);
    } finally {
        // 投稿ボタンを再有効化
        postButton.disabled = false;
        postButton.textContent = '投稿する';
    }
}

// 投稿結果の表示
function showPostResult(result) {
    const statusContainer = document.getElementById('status-container');
    statusContainer.innerHTML = '';
    statusContainer.classList.remove('hidden');

    // 全体の成功/失敗に応じたメッセージ
    const statusMessage = document.createElement('div');
    statusMessage.className = `status-message ${result.success ? 'status-success' : 'status-error'}`;
    statusMessage.textContent = result.success ? '投稿に成功しました！' : '一部のプラットフォームへの投稿に失敗しました。';

    statusContainer.appendChild(statusMessage);

    // 各プラットフォームの結果表示
    if (result.results) {
        Object.keys(result.results).forEach(platform => {
            const platformResult = result.results[platform];
            const resultDiv = document.createElement('div');
            resultDiv.className = 'platform-result';

            const displayName = platform.charAt(0).toUpperCase() + platform.slice(1);
            resultDiv.innerHTML = `
                <strong>${displayName}:</strong> ${platformResult.success ? '成功' : `失敗 (${platformResult.error})`}
            `;

            statusContainer.appendChild(resultDiv);
        });
    }
}

// エラーメッセージの表示
function showError(message) {
    const statusContainer = document.getElementById('status-container');
    statusContainer.innerHTML = '';
    statusContainer.classList.remove('hidden');

    const errorDiv = document.createElement('div');
    errorDiv.className = 'status-message status-error';
    errorDiv.textContent = message;

    statusContainer.appendChild(errorDiv);
}
