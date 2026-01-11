# 🎵 YouTube Data API v3 Setup Guide

## Overview

The Emotion-Based Music Recommendation System uses **YouTube Data API v3** to fetch real, multilingual music videos based on detected emotions.

## Prerequisites

1. A Google account
2. Python 3.8+
3. Internet connection

## Step 1: Get YouTube Data API Key

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Log in with your Google account

2. **Create a New Project** (or select existing)
   - Click the project dropdown at the top
   - Click "New Project"
   - Enter project name: `Emotion Music Player`
   - Click "Create"

3. **Enable YouTube Data API v3**
   - Go to: https://console.cloud.google.com/apis/library
   - Search for "YouTube Data API v3"
   - Click on it and click "Enable"

4. **Create API Key**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Click "Create Credentials" → "API Key"
   - Copy your API key
   - (Optional) Click "Restrict Key" to limit usage:
     - Under "API restrictions", select "Restrict key"
     - Choose "YouTube Data API v3"
     - Click "Save"

## Step 2: Configure Environment Variables

1. **Create `.env` file** in your project root directory

2. **Add your YouTube API key**:
   ```env
   YOUTUBE_API_KEY=your_actual_api_key_here
   ```

3. **Replace** `your_actual_api_key_here` with your actual API key from Step 1

## Step 3: Install Dependencies

All required packages should already be installed:
```bash
pip install -r requirements.txt
```

Required packages:
- `requests` - For API calls
- `python-dotenv` - For loading `.env` file

## Step 4: Test the Integration

1. **Start the server**
   ```bash
   python app.py
   ```

2. **Check the console**
   - You should see: `[OK] YouTube client initialized successfully`
   - If you see an error, check your API key in `.env`

3. **Test emotion detection**
   - Upload an image or use webcam
   - Click "Detect Emotion"
   - You should see YouTube music video recommendations!

## API Quota & Limits

- **Free Tier**: 10,000 units per day
- **Search Request**: 100 units
- **Video Details Request**: 1 unit per video

**Daily Limit**: ~100 search requests per day (with video details)

The app uses caching to reduce API calls and stay within limits.

## Troubleshooting

### "YouTube API key not found"
- Make sure `.env` file exists in project root
- Check that `YOUTUBE_API_KEY` is set correctly
- No spaces around the `=` sign

### "YouTube API request failed"
- Check your internet connection
- Verify API key is correct
- Check if YouTube Data API v3 is enabled in Google Cloud Console
- Check API quota hasn't been exceeded

### "No videos found"
- Try a different emotion
- Check if the search query is valid
- Some languages may have fewer results

### Rate Limiting
- The app uses caching (1 hour TTL) to reduce API calls
- If you hit rate limits, wait a few minutes and try again
- Consider upgrading to a paid Google Cloud plan for higher quotas

## Features

✅ **Multilingual Support**: Searches across 7 languages
✅ **Emotion Mapping**: Maps emotions to mood keywords
✅ **Smart Filtering**: Only music category videos (Category ID: 10)
✅ **Language Diversity**: Ensures at least 3 different languages in results
✅ **Caching**: Reduces API calls with 1-hour cache
✅ **YouTube Embeds**: Direct video playback in the app

## Supported Languages

- English
- Hindi
- Punjabi
- Tamil
- Telugu
- Korean
- Spanish

## Emotion → Mood Mapping

- **Happy** → "happy"
- **Sad** → "sad"
- **Angry** → "energetic"
- **Neutral** → "calm"
- **Surprise** → "exciting"
- **Fear** → "dark"
- **Disgust** → "intense"

You can edit this mapping in `recommender.py` → `EMOTION_MOOD_MAP`

---

**Ready to go!** 🎵

