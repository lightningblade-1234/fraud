// ===== DOM Elements =====
const uploadArea = document.getElementById('uploadArea');
const audioFileInput = document.getElementById('audioFile');
const browseBtn = document.getElementById('browseBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeFile = document.getElementById('removeFile');
const analyzeBtn = document.getElementById('analyzeBtn');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');
const retryBtn = document.getElementById('retryBtn');

// ===== State =====
let selectedFile = null;

// ===== API Configuration =====
const API_KEY = 'sk_test_123456789';
const API_URL = '/api/voice-detection';

// ===== Event Listeners =====
browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    audioFileInput.click();
});

uploadArea.addEventListener('click', () => {
    audioFileInput.click();
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

audioFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

removeFile.addEventListener('click', () => {
    clearFile();
});

analyzeBtn.addEventListener('click', () => {
    analyzeVoice();
});

newAnalysisBtn.addEventListener('click', () => {
    resetUI();
});

retryBtn.addEventListener('click', () => {
    resetUI();
});

// ===== File Handling =====
function handleFileSelect(file) {
    // Validate file type
    if (!file.type.includes('audio') && !file.name.endsWith('.mp3')) {
        showError('Please select an MP3 audio file.');
        return;
    }

    selectedFile = file;

    // Update UI
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
    analyzeBtn.disabled = false;
}

function clearFile() {
    selectedFile = null;
    audioFileInput.value = '';
    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    analyzeBtn.disabled = true;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ===== API Call =====
async function analyzeVoice() {
    if (!selectedFile) return;

    // Get selected language
    const language = document.querySelector('input[name="language"]:checked').value;

    // Show loading state
    const btnText = document.querySelector('.btn-text');
    const btnLoader = document.querySelector('.btn-loader');
    btnText.style.display = 'none';
    btnLoader.style.display = 'flex';
    analyzeBtn.disabled = true;

    try {
        // Convert file to Base64
        const base64Audio = await fileToBase64(selectedFile);

        // Make API request
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': API_KEY
            },
            body: JSON.stringify({
                language: language,
                audioFormat: 'mp3',
                audioBase64: base64Audio
            })
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            showResult(data);
        } else {
            showError(data.message || data.detail?.message || 'Analysis failed. Please try again.');
        }

    } catch (error) {
        console.error('Error:', error);
        showError('Network error. Please check your connection and try again.');
    } finally {
        // Reset button state
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        analyzeBtn.disabled = false;
    }
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            // Remove the data URL prefix (e.g., "data:audio/mp3;base64,")
            const base64 = reader.result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = error => reject(error);
    });
}

// ===== Display Results =====
function showResult(data) {
    // Hide upload section
    document.querySelector('.upload-section').style.display = 'none';
    errorSection.style.display = 'none';
    resultSection.style.display = 'block';

    // Determine if AI or Human
    const isHuman = data.classification === 'HUMAN';

    // Update result icon
    const resultIcon = document.getElementById('resultIcon');
    resultIcon.className = 'result-icon ' + (isHuman ? 'human' : 'ai');
    resultIcon.innerHTML = isHuman ? '👤' : '🤖';

    // Update title
    const resultTitle = document.getElementById('resultTitle');
    resultTitle.className = 'result-title ' + (isHuman ? 'human' : 'ai');
    resultTitle.textContent = isHuman ? 'Human Voice Detected' : 'AI-Generated Voice Detected';

    // Update confidence
    const confidencePercent = Math.round(data.confidenceScore * 100);
    document.getElementById('confidenceValue').textContent = confidencePercent + '%';
    document.getElementById('confidenceFill').style.width = confidencePercent + '%';

    // Update explanation
    document.getElementById('explanationText').textContent = data.explanation;

    // Update language
    document.getElementById('languageValue').textContent = data.language;
}

function showError(message) {
    document.querySelector('.upload-section').style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
}

function resetUI() {
    clearFile();
    document.querySelector('.upload-section').style.display = 'flex';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
}
