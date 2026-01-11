// Emotion-Based Music Recommendation System - Main JavaScript

let currentImageData = null;
let currentEmotion = null;
let currentConfidence = null;
let webcamStream = null;
let selectedLanguage = '';

// Emotion icon mapping
const emotionIcons = {
    'Happy': '😊',
    'Sad': '😢',
    'Angry': '😠',
    'Neutral': '😐',
    'Surprise': '😲',
    'Fear': '😨',
    'Disgust': '🤢'
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeUpload();
    loadLanguages();
    initializeTheme();
});

// Theme Toggle Functionality
function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const themeIcon = themeToggle.querySelector('.theme-icon');
    
    // Check for saved theme preference or default to light mode
    const savedTheme = localStorage.getItem('theme') || 'light';
    body.classList.toggle('dark-theme', savedTheme === 'dark');
    updateThemeIcon(savedTheme);
    
    // Theme toggle event
    themeToggle.addEventListener('click', function() {
        body.classList.toggle('dark-theme');
        const currentTheme = body.classList.contains('dark-theme') ? 'dark' : 'light';
        localStorage.setItem('theme', currentTheme);
        updateThemeIcon(currentTheme);
        
        // Add ripple effect
        createRipple(themeToggle, event);
    });
}

function updateThemeIcon(theme) {
    const themeIcon = document.querySelector('.theme-icon');
    if (theme === 'dark') {
        themeIcon.textContent = '☀️';
    } else {
        themeIcon.textContent = '🌙';
    }
}

function createRipple(element, event) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');
    
    element.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// Initialize image upload
function initializeUpload() {
    const uploadArea = document.getElementById('upload-area');
    const imageInput = document.getElementById('image-input');
    
    uploadArea.addEventListener('click', () => imageInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    
    imageInput.addEventListener('change', handleImageSelect);
}

// Handle drag and drop
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.style.borderColor = 'var(--accent-primary)';
    e.currentTarget.style.transform = 'scale(1.02)';
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.style.borderColor = 'var(--glass-border)';
    e.currentTarget.style.transform = 'scale(1)';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleImageSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
        alert('File size must be less than 5MB');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        displayImagePreview(e.target.result);
        currentImageData = e.target.result;
        document.getElementById('detect-btn').disabled = false;
    };
    reader.readAsDataURL(file);
}

function displayImagePreview(imageSrc) {
    const preview = document.getElementById('image-preview');
    const img = document.getElementById('preview-img');
    const uploadArea = document.getElementById('upload-area');
    
    img.src = imageSrc;
    preview.style.display = 'block';
    uploadArea.style.display = 'none';
}

function removeImage() {
    currentImageData = null;
    document.getElementById('image-preview').style.display = 'none';
    document.getElementById('upload-area').style.display = 'block';
    document.getElementById('image-input').value = '';
    document.getElementById('detect-btn').disabled = true;
}

// Tab switching
function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    if (tab === 'upload') {
        document.getElementById('upload-tab').classList.add('active');
        stopWebcam();
    } else {
        document.getElementById('webcam-tab').classList.add('active');
    }
}

// Webcam functions
async function startWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'user',
                width: { ideal: 640 },
                height: { ideal: 480 }
            } 
        });
        
        webcamStream = stream;
        const video = document.getElementById('webcam-video');
        video.srcObject = stream;
        video.style.display = 'block';
        
        document.getElementById('webcam-placeholder').style.display = 'none';
        document.getElementById('start-webcam-btn').style.display = 'none';
        document.getElementById('capture-btn').style.display = 'inline-block';
        document.getElementById('stop-webcam-btn').style.display = 'inline-block';
    } catch (error) {
        console.error('Error accessing webcam:', error);
        alert('Could not access webcam. Please check permissions.');
    }
}

function captureWebcam() {
    const video = document.getElementById('webcam-video');
    const canvas = document.getElementById('webcam-canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    
    currentImageData = canvas.toDataURL('image/jpeg');
    document.getElementById('detect-btn').disabled = false;
    
    // Show preview
    displayImagePreview(currentImageData);
    
    alert('Photo captured! Click "Detect Emotion" to analyze.');
}

function stopWebcam() {
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }
    
    const video = document.getElementById('webcam-video');
    video.srcObject = null;
    video.style.display = 'none';
    
    document.getElementById('webcam-placeholder').style.display = 'block';
    document.getElementById('start-webcam-btn').style.display = 'inline-block';
    document.getElementById('capture-btn').style.display = 'none';
    document.getElementById('stop-webcam-btn').style.display = 'none';
}

// Detect emotion
async function detectEmotion() {
    if (!currentImageData) {
        alert('Please select or capture an image first');
        return;
    }
    
    const detectBtn = document.getElementById('detect-btn');
    detectBtn.disabled = true;
    detectBtn.innerHTML = '<span class="loading"></span><span>Detecting...</span>';
    
    try {
        const response = await fetch('/api/detect-and-recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_data: currentImageData,
                language: selectedLanguage || null,
                top_n: 5
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayEmotionResult(data);
            displayRecommendations(data.recommendations);
        } else {
            const errorMsg = data.error || 'Could not detect emotion';
            const errorType = data.error_type ? ` (${data.error_type})` : '';
            console.error('Emotion detection error:', data);
            alert('Error: ' + errorMsg + errorType + '\n\nCheck the browser console (F12) for more details.');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    } finally {
        detectBtn.disabled = false;
        detectBtn.innerHTML = '<span class="btn-icon">🔍</span><span>Detect Emotion</span>';
    }
}

// Display emotion result
function displayEmotionResult(data) {
    currentEmotion = data.emotion;
    currentConfidence = data.confidence;
    
    // Update emotion display
    document.getElementById('emotion-icon').textContent = emotionIcons[data.emotion] || '😐';
    document.getElementById('emotion-name').textContent = data.emotion;
    document.getElementById('confidence-score').textContent = (data.confidence * 100).toFixed(1) + '%';
    
    // Display all emotions
    const allEmotionsDiv = document.getElementById('all-emotions');
    allEmotionsDiv.innerHTML = '';
    
    Object.entries(data.all_emotions).forEach(([emotion, score]) => {
        const emotionBar = document.createElement('div');
        emotionBar.className = 'emotion-bar';
        emotionBar.innerHTML = `
            <div class="emotion-bar-label">${emotion} ${emotionIcons[emotion] || ''}</div>
            <div class="emotion-bar-fill" style="width: ${score * 100}%"></div>
            <div style="margin-top: 5px; font-size: 0.9em; color: #666;">${(score * 100).toFixed(1)}%</div>
        `;
        allEmotionsDiv.appendChild(emotionBar);
    });
    
    // Show result section
    document.getElementById('emotion-result').style.display = 'block';
    document.getElementById('language-section').style.display = 'block';
    document.getElementById('recommendations-section').style.display = 'block';
}

// Display recommendations
function displayRecommendations(recommendations) {
    const recommendationsList = document.getElementById('recommendations-list');
    recommendationsList.innerHTML = '';
    
    if (!recommendations || recommendations.length === 0) {
        recommendationsList.innerHTML = `
            <div class="glass-card inner-glass" style="padding: 30px; text-align: center;">
                <p style="font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 15px;">
                    ⚠️ No recommendations found
                </p>
                <p style="color: var(--text-secondary);">
                    This might be due to:<br>
                    • YouTube API connection issue<br>
                    • No videos found for this emotion/mood<br>
                    • Network connectivity problem
                </p>
                <p style="color: var(--text-secondary); margin-top: 15px; font-size: 0.9rem;">
                    Please try again or check the server console for details.
                </p>
            </div>
        `;
        return;
    }
    
    recommendations.forEach((song, index) => {
        const songCard = document.createElement('div');
        songCard.className = 'song-card';
        
        // Check if this is a YouTube video
        const isYouTube = song.youtube_id || song.youtube_url;
        
        // Thumbnail or placeholder
        const thumbnail = song.thumbnail || 'https://via.placeholder.com/150?text=No+Image';
        
        songCard.innerHTML = `
            <div class="song-number">#${index + 1}</div>
            <div class="song-album-art">
                <img src="${thumbnail}" alt="${song.song_name}" onerror="this.src='https://via.placeholder.com/150?text=No+Image'">
            </div>
            <div class="song-info">
                <div class="song-title">${song.song_name}</div>
                <div class="song-artist">🎤 ${song.artist || song.channel_title || 'Unknown Artist'}</div>
                <div class="song-meta">
                    <span class="meta-badge badge-language">🌍 ${song.language}</span>
                    <span class="meta-badge badge-emotion">${emotionIcons[song.emotion] || ''} ${song.emotion}</span>
                    <span class="meta-badge badge-genre">🎵 ${song.genre || 'Music'}</span>
                    ${song.view_count ? `<span class="meta-badge" style="background: var(--glass-bg); border: 1px solid var(--glass-border);">👁️ ${(song.view_count / 1000000).toFixed(1)}M views</span>` : ''}
                </div>
                ${isYouTube ? `
                    <div class="youtube-actions">
                        <a href="${song.youtube_url}" target="_blank" class="youtube-button">
                            <span style="color: #FF0000;">▶</span> Watch on YouTube
                        </a>
                    </div>
                ` : ''}
            </div>
            <div class="youtube-player">
                ${isYouTube && song.youtube_id ? 
                    `<iframe 
                        src="https://www.youtube.com/embed/${song.youtube_id}?rel=0&modestbranding=1" 
                        width="100%" 
                        height="315" 
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen
                        style="border-radius: 12px; min-height: 315px;">
                    </iframe>` 
                    : '<p style="color: #999; font-size: 0.9em;">Video not available</p>'
                }
            </div>
        `;
        
        recommendationsList.appendChild(songCard);
    });
    
    // Add YouTube attribution
    if (recommendations.some(s => s.youtube_url)) {
        const attribution = document.createElement('div');
        attribution.className = 'youtube-attribution';
        attribution.innerHTML = '<p>Powered by <a href="https://www.youtube.com" target="_blank">YouTube</a> Data API v3</p>';
        recommendationsList.appendChild(attribution);
    }
}

// Load available languages
async function loadLanguages() {
    try {
        const response = await fetch('/api/languages');
        const data = await response.json();
        
        if (data.success) {
            const languageSelect = document.getElementById('language-filter');
            data.languages.forEach(lang => {
                const option = document.createElement('option');
                option.value = lang;
                option.textContent = lang;
                languageSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading languages:', error);
    }
}

// Filter by language
function filterByLanguage() {
    selectedLanguage = document.getElementById('language-filter').value;
    
    if (currentEmotion && currentConfidence) {
        // Re-fetch recommendations with language filter
        fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                emotion: currentEmotion,
                confidence: currentConfidence,
                language: selectedLanguage || null,
                top_n: 5
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayRecommendations(data.recommendations);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}

