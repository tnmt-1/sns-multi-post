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
let isDarkMode = false; // ダークモード状態
let selectedImageFiles = []; // 選択中の画像ファイル（最大2つ）

// DOMが読み込まれた後に実行
document.addEventListener('DOMContentLoaded', function() {
    // ダークモードの初期設定
    initDarkMode();
    
    // 初期化
    initApp();

    // モード切り替えボタンのイベントリスナー
    document.getElementById('unified-mode-btn').addEventListener('click', () => switchMode('unified'));
    document.getElementById('individual-mode-btn').addEventListener('click', () => switchMode('individual'));

    // 投稿ボタンのイベントリスナー
    document.getElementById('post-button').addEventListener('click', handlePost);
    
    // ダークモード切り替えボタンのイベントリスナー
    document.getElementById('dark-mode-toggle').addEventListener('click', toggleDarkMode);

    // Ctrl+Enterで投稿
    setupCtrlEnterPost();

    // 投稿先モーダルの開閉
    const modal = document.getElementById('platforms-modal');
    const openBtn = document.getElementById('toggle-platforms-btn');
    const closeBtn = document.getElementById('close-platforms-modal');
    openBtn.addEventListener('click', function() {
        modal.classList.remove('hidden');
    });
    closeBtn.addEventListener('click', function() {
        modal.classList.add('hidden');
    });
    // モーダル外クリックで閉じる
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });

    // ページ表示時に投稿テキストエリアへ自動フォーカス
    setTimeout(function() {
        const textarea = document.getElementById('unified-content');
        if (textarea) textarea.focus();
    }, 100);

    // 画像アップロード初期化
    setupImageUpload();
});

// ダークモード初期設定
function initDarkMode() {
    // ローカルストレージからダークモード設定を取得
    const savedMode = localStorage.getItem('darkMode');
    isDarkMode = savedMode === 'true';
    
    // ダークモードボタンのテキスト更新
    updateDarkModeButtonText();
    
    // ダークモード適用
    applyDarkMode(isDarkMode);
}

// ダークモードの切り替え
function toggleDarkMode() {
    isDarkMode = !isDarkMode;
    
    // ローカルストレージに設定を保存
    localStorage.setItem('darkMode', isDarkMode);
    
    // ダークモードボタンのテキスト更新
    updateDarkModeButtonText();
    
    // ダークモード適用
    applyDarkMode(isDarkMode);
}

// ダークモードボタンのテキスト更新
function updateDarkModeButtonText() {
    const button = document.getElementById('dark-mode-toggle');
    // button.textContent = isDarkMode ? 'ライトモードへ切替' : 'ダークモードへ切替';
}

// ダークモードの適用
function applyDarkMode(enable) {
    const lightStylesheet = document.querySelector('link[title="light"]');
    const darkStylesheet = document.querySelector('link[title="dark"]');
    
    if (enable) {
        lightStylesheet.disabled = true;
        darkStylesheet.disabled = false;
    } else {
        lightStylesheet.disabled = false;
        darkStylesheet.disabled = true;
    }
}

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
        updateUnifiedCharLimit(); // 初期表示時にカウンター更新

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
            // デフォルトでON（選択状態）にする
            card.classList.add('selected');
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
    
    // 個別投稿モードの場合はUIを更新
    if (postMode === 'individual') {
        updateIndividualPosts();
    }
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
    updateUnifiedCharLimit(); // 投稿先変更時にカウンター更新
}

// 一括投稿モードの文字数カウンター設定
function setupUnifiedModeCounters() {
    const textarea = document.getElementById('unified-content');
    const counter = document.getElementById('unified-character-count');
    updateUnifiedCharLimit();
    textarea.addEventListener('input', function() {
        const limit = getUnifiedCharLimit();
        counter.textContent = `${textarea.value.length} / ${limit}`;
    });
}

// 選択中の投稿先の中で一番少ない文字数制限を取得
function getUnifiedCharLimit() {
    const selected = Array.from(document.querySelectorAll('.platform-card.selected'));
    if (selected.length === 0) return 3000;
    let min = 3000;
    selected.forEach(card => {
        const platform = card.dataset.platform;
        if (characterLimits[platform] && characterLimits[platform] < min) {
            min = characterLimits[platform];
        }
    });
    return min;
}

// カウンター表示を更新
function updateUnifiedCharLimit() {
    const textarea = document.getElementById('unified-content');
    const counter = document.getElementById('unified-character-count');
    const limit = getUnifiedCharLimit();
    counter.textContent = `${textarea.value.length} / ${limit}`;
    textarea.maxLength = limit;
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
                counter.style.color = isDarkMode ? '#f87171' : '#e74c3c';
            } else {
                counter.style.color = isDarkMode ? '#aaa' : '#666';
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
        let postDataPerPlatform = {};
        if (postMode === 'unified') {
            // 一括投稿モードの場合
            const content = document.getElementById('unified-content').value;
            if (!content.trim()) {
                throw new Error('投稿内容を入力してください');
            }
            selectedPlatforms.forEach(platform => {
                postDataPerPlatform[platform] = content;
            });
        } else {
            // 個別投稿モードの場合
            selectedPlatforms.forEach(platform => {
                const textarea = document.querySelector(`.individual-content[data-platform="${platform}"]`);
                const content = textarea ? textarea.value : '';
                if (!content.trim()) {
                    throw new Error(`${platform.charAt(0).toUpperCase() + platform.slice(1)}の投稿内容を入力してください`);
                }
                postDataPerPlatform[platform] = content;
            });
        }

        // SNSごとにリクエストを作成
        const fetchPromises = selectedPlatforms.map(platform => {
            // 画像が選択されている場合はmultipart/form-dataで送信
            if (selectedImageFiles.length > 0) {
                const formData = new FormData();
                selectedImageFiles.forEach((file, idx) => {
                    formData.append('image' + (idx + 1), file);
                });
                // SNSごとにpostDataを分けて送信
                const singlePostData = {};
                singlePostData[platform] = {
                    selected: true,
                    content: postDataPerPlatform[platform]
                };
                formData.append('postData', JSON.stringify(singlePostData));
                return fetch(API_URL.POST, {
                    method: 'POST',
                    body: formData
                }).then(async response => {
                    const result = await response.json();
                    return { platform, success: response.ok, ...result };
                }).catch(e => ({ platform, success: false, error: e.message }));
            } else {
                // 画像なしの場合はJSONで送信
                const singlePostData = {};
                singlePostData[platform] = {
                    selected: true,
                    content: postDataPerPlatform[platform ]
                };
                return fetch(API_URL.POST, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(singlePostData)
                }).then(async response => {
                    const result = await response.json();
                    return { platform, success: response.ok, ...result };
                }).catch(e => ({ platform, success: false, error: e.message }));
            }
        });

        // 並行リクエストを待つ
        const results = await Promise.all(fetchPromises);
        // 結果をまとめる
        const resultSummary = {
            success: results.every(r => r.success),
            results: {}
        };
        results.forEach(r => {
            resultSummary.results[r.platform] = {
                success: r.success,
                error: r.error || r.message || null
            };
        });
        showPostResult(resultSummary);
    } catch (error) {
        showError(error.message);
    } finally {
        // 投稿ボタンを再有効化
        postButton.disabled = false;
        postButton.textContent = '投稿する';
    }
}

// トースト通知表示
function showToast(message, type = 'success', duration = 4000) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 400);
    }, duration);
}

// 投稿結果の表示（トースト通知に変更）
function showPostResult(result) {
    // 全体の成功/失敗に応じたメッセージ
    let msg = '';
    if (result.success) {
        msg = '投稿に成功しました！';
    } else {
        msg = '一部のプラットフォームへの投稿に失敗しました。';
    }
    // 各プラットフォームの詳細も表示
    if (result.results) {
        msg += '\n';
        Object.keys(result.results).forEach(platform => {
            const platformResult = result.results[platform];
            const displayName = platform.charAt(0).toUpperCase() + platform.slice(1);
            msg += `${displayName}: ${platformResult.success ? '成功' : `失敗 (${platformResult.error || 'エラー'}`}` + `)\n`;
        });
    }
    showToast(msg, result.success ? 'success' : 'error', 6000);
    // 投稿成功時にテキストエリアをクリア＆フォーカス
    if (result.success) {
        if (postMode === 'unified') {
            const unifiedTextarea = document.getElementById('unified-content');
            unifiedTextarea.value = '';
            unifiedTextarea.focus();
            // 文字数カウントもリセット
            const counter = document.getElementById('unified-character-count');
            if (counter) counter.textContent = `0 / ${unifiedTextarea.getAttribute('maxlength')}`;
        } else if (postMode === 'individual') {
            // 個別投稿モードの各テキストエリアをクリア＆最初のエリアにフォーカス
            const textareas = document.querySelectorAll('.individual-content');
            textareas.forEach((ta, idx) => {
                ta.value = '';
                // 文字数カウントもリセット
                const limit = ta.getAttribute('maxlength');
                const counter = ta.parentElement.querySelector('.character-count');
                if (counter) counter.textContent = `0 / ${limit}`;
                if (idx === 0) ta.focus();
            });
        }
        // 画像もリセット
        selectedImageFiles = [];
        // input要素の値もクリア
        const imageInput = document.getElementById('image-input');
        if (imageInput) imageInput.value = '';
        if (typeof updateImagePreview === 'function') {
            updateImagePreview();
        }
        // ファイル名表示もクリア
        const imageFilename = document.getElementById('image-filename');
        if (imageFilename) imageFilename.textContent = '';
    }
}

// エラーメッセージの表示（トースト通知に変更）
function showError(message) {
    showToast(message, 'error');
}

// Ctrl+Enterで投稿するイベント設定
function setupCtrlEnterPost() {
    // 一括投稿モード
    const unifiedTextarea = document.getElementById('unified-content');
    unifiedTextarea.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('post-button').click();
        }
    });

    // 個別投稿モード
    document.addEventListener('keydown', function(e) {
        if (postMode === 'individual' && e.ctrlKey && e.key === 'Enter') {
            // フォーカスが個別テキストエリアの場合のみ
            const active = document.activeElement;
            if (active && active.classList.contains('individual-content')) {
                e.preventDefault();
                document.getElementById('post-button').click();
            }
        }
    });
}

// 画像アップロード・ペースト・プレビュー処理
function setupImageUpload() {
    const imageInput = document.getElementById('image-input');
    const imageUploadBtn = document.getElementById('image-upload-btn');
    const imageFilename = document.getElementById('image-filename');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const textarea = document.getElementById('unified-content');
    // const imageRemoveBtn = document.getElementById('image-remove-btn'); // 削除

    // ファイル選択ボタン
    imageUploadBtn.addEventListener('click', () => imageInput.click());

    // ファイル選択時
    imageInput.addEventListener('change', (e) => {
        if (e.target.files) {
            for (const file of e.target.files) {
                if (selectedImageFiles.length < 2) {
                    addImageFile(file);
                }
            }
            imageInput.value = '';
        }
    });

    // クリップボードからのペースト
    textarea.addEventListener('paste', (e) => {
        if (e.clipboardData && e.clipboardData.items) {
            for (const item of e.clipboardData.items) {
                if (item.type.startsWith('image/')) {
                    const file = item.getAsFile();
                    if (selectedImageFiles.length < 2) {
                        addImageFile(file);
                    }
                    e.preventDefault();
                    break;
                }
            }
        }
    });

    // 画像ファイルを追加＆プレビュー
    function addImageFile(file) {
        if (!file || selectedImageFiles.length >= 2) return;
        selectedImageFiles.push(file);
        updateImagePreview();
    }

    // 画像ファイルを削除
    function removeImageFile(idx) {
        selectedImageFiles.splice(idx, 1);
        updateImagePreview();
    }

    // プレビュー表示＋削除ボタン
    function updateImagePreview() {
        imagePreviewContainer.innerHTML = '';
        imagePreviewContainer.classList.toggle('active', selectedImageFiles.length > 0);
        imageFilename.textContent = selectedImageFiles.map(f => f.name).join(', ');
        if (selectedImageFiles.length > 0) {
            imageFilename.classList.add('active');
        } else {
            imageFilename.classList.remove('active');
        }
        selectedImageFiles.forEach((file, idx) => {
            const reader = new FileReader();
            reader.onload = function(ev) {
                const wrapper = document.createElement('div');
                wrapper.className = 'image-preview-item';
                wrapper.innerHTML = `<img src="${ev.target.result}" alt="preview${idx+1}" />` +
                    `<button type="button" class="image-remove-btn" aria-label="画像を削除" data-idx="${idx}">✕</button>`;
                imagePreviewContainer.appendChild(wrapper);
                // 削除ボタンイベント
                wrapper.querySelector('.image-remove-btn').addEventListener('click', () => removeImageFile(idx));
            };
            reader.readAsDataURL(file);
        });
    }

    // 初期状態でファイル名・プレビューを非表示に
    selectedImageFiles = [];
    updateImagePreview();
}
