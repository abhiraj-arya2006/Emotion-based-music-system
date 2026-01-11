"""
Music Recommendation Engine with YouTube Data API v3 Integration
Recommends music videos from YouTube based on detected emotion with multi-language support.
"""

import os
from typing import List, Dict, Optional
from youtube_client import YouTubeClient

class MusicRecommender:
    """
    Music recommendation system that matches YouTube music videos to emotions.
    Uses emotion → mood keyword mapping and searches YouTube for music videos.
    """
    
    # Emotion to Mood Keyword Mapping
    EMOTION_MOOD_MAP = {
        'Happy': 'happy',
        'Sad': 'sad',
        'Angry': 'energetic',
        'Neutral': 'calm',
        'Surprise': 'exciting',
        'Fear': 'dark',
        'Disgust': 'intense'
    }
    
    # Supported languages
    SUPPORTED_LANGUAGES = ['English', 'Hindi', 'Punjabi', 'Tamil', 'Telugu', 'Korean', 'Spanish']
    
    def __init__(self):
        """
        Initialize the recommender with YouTube integration.
        YouTube API key is required.
        """
        # Initialize YouTube client - required
        try:
            self.youtube_client = YouTubeClient()
            print("[OK] YouTube client initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize YouTube client: {e}\n"
            error_msg += "YouTube integration is required for this application.\n"
            error_msg += "Please check your YouTube API key in .env file:\n"
            error_msg += "- YOUTUBE_API_KEY"
            raise RuntimeError(error_msg)
    
    def get_mood_for_emotion(self, emotion: str) -> str:
        """
        Get mood keyword for a given emotion.
        
        Args:
            emotion: Detected emotion
            
        Returns:
            Mood keyword string
        """
        return self.EMOTION_MOOD_MAP.get(emotion, 'happy')  # Default to happy
    
    def get_recommendations(self, emotion: str, confidence: float = 1.0, 
                          top_n: int = 5, language: Optional[str] = None) -> List[Dict]:
        """
        Get music recommendations based on detected emotion.
        Uses YouTube API to fetch real, multilingual music videos.
        
        Args:
            emotion: Detected emotion (Happy, Sad, Angry, etc.)
            confidence: Confidence score of emotion detection
            top_n: Number of recommendations to return (default 5)
            language: Optional language filter (not strictly enforced for diversity)
            
        Returns:
            List of song dictionaries with YouTube metadata
        """
        if not self.youtube_client:
            raise RuntimeError("YouTube client not initialized. YouTube integration is required.")
        
        return self._get_youtube_recommendations(emotion, confidence, top_n, language)
    
    def _get_youtube_recommendations(self, emotion: str, confidence: float,
                                   top_n: int, language: Optional[str]) -> List[Dict]:
        """
        Get recommendations from YouTube API.
        
        Args:
            emotion: Detected emotion
            confidence: Confidence score
            top_n: Number of recommendations
            language: Optional language filter
            
        Returns:
            List of track dictionaries
        """
        # Get mood keyword for emotion
        mood = self.get_mood_for_emotion(emotion)
        
        # Determine which languages to search
        if language:
            # Search requested language + a few others for diversity
            languages_to_search = [language] + [lang for lang in self.SUPPORTED_LANGUAGES 
                                                 if lang != language][:2]
        else:
            # Search all supported languages for maximum diversity
            languages_to_search = self.SUPPORTED_LANGUAGES
        
        # Fetch videos from multiple languages (10 per language)
        all_videos = self.youtube_client.get_multilingual_music(
            mood=mood,
            languages=languages_to_search,
            max_per_language=10
        )
        
        if not all_videos or len(all_videos) == 0:
            print(f"[WARNING] No videos found for emotion: {emotion}, mood: {mood}")
            return []
        
        # Add emotion and confidence to each video
        for video in all_videos:
            video['emotion'] = emotion
            video['mood_match_score'] = confidence
        
        # Filter by language if specified (but prioritize diversity)
        if language:
            # Try to get at least 2 tracks in requested language, but ensure diversity
            language_videos = [v for v in all_videos if v['language'].lower() == language.lower()]
            other_videos = [v for v in all_videos if v['language'].lower() != language.lower()]
            
            # Combine: prefer requested language but ensure diversity
            if len(language_videos) >= 2:
                selected = language_videos[:2] + other_videos[:top_n - 2]
            else:
                selected = language_videos + other_videos[:top_n - len(language_videos)]
        else:
            selected = all_videos
        
        # Ensure at least 3 different languages in output
        selected = self._ensure_language_diversity(selected, top_n)
        
        # Rank by view count (popularity) and mood match score
        selected.sort(key=lambda x: (x.get('view_count', 0) * x['mood_match_score']), reverse=True)
        
        # Take top N
        recommendations = selected[:top_n]
        
        # Format for frontend
        formatted_recommendations = []
        for video in recommendations:
            # Extract artist name from channel title or title
            artist = self._extract_artist(video)
            
            formatted_video = {
                'song_name': video['title'],
                'artist': artist,
                'language': video['language'],
                'emotion': video['emotion'],
                'genre': 'Music',  # All are music videos
                'youtube_id': video['id'],
                'youtube_url': video['watch_url'],
                'embed_url': video['embed_url'],
                'thumbnail': video['thumbnail'],
                'view_count': video.get('view_count', 0),
                'like_count': video.get('like_count', 0),
                'recommendation_score': video['mood_match_score'] * (video.get('view_count', 0) / 1000000.0),
                'channel_title': video.get('channel_title', 'Unknown')
            }
            formatted_recommendations.append(formatted_video)
        
        return formatted_recommendations
    
    def _extract_artist(self, video: Dict) -> str:
        """
        Extract artist name from video metadata.
        
        Args:
            video: Video dictionary
            
        Returns:
            Artist name string
        """
        # Try channel title first (usually the artist)
        channel_title = video.get('channel_title', '')
        if channel_title:
            # Remove common suffixes
            artist = channel_title.replace(' - Topic', '').replace('VEVO', '').strip()
            if artist:
                return artist
        
        # Fallback to parsing title
        title = video.get('title', '')
        if ' - ' in title:
            # Format: "Song Name - Artist Name"
            parts = title.split(' - ', 1)
            if len(parts) > 1:
                return parts[1].strip()
        
        return channel_title or 'Unknown Artist'
    
    def _ensure_language_diversity(self, videos: List[Dict], target_count: int) -> List[Dict]:
        """
        Ensure at least 3 different languages in recommendations.
        
        Args:
            videos: List of video dictionaries
            target_count: Target number of recommendations
            
        Returns:
            List with language diversity
        """
        if len(videos) < 3:
            return videos[:target_count]
        
        # Group by language
        by_language = {}
        for video in videos:
            lang = video['language']
            if lang not in by_language:
                by_language[lang] = []
            by_language[lang].append(video)
        
        # If we already have 3+ languages, return top videos
        if len(by_language) >= 3:
            return videos[:target_count]
        
        # Otherwise, try to get more diverse videos
        # Sort languages by video count
        sorted_langs = sorted(by_language.items(), key=lambda x: len(x[1]), reverse=True)
        
        selected = []
        # Take at least 1 from each available language
        for lang, lang_videos in sorted_langs:
            if lang_videos:
                selected.append(lang_videos[0])
        
        # Fill remaining slots with top videos
        remaining_slots = target_count - len(selected)
        all_remaining = [v for v in videos if v not in selected]
        all_remaining.sort(key=lambda x: x.get('view_count', 0), reverse=True)
        selected.extend(all_remaining[:remaining_slots])
        
        return selected[:target_count]
    
    def get_all_languages(self) -> List[str]:
        """Get list of all available languages from YouTube."""
        return self.SUPPORTED_LANGUAGES
    
    def get_song_count_by_emotion(self) -> Dict[str, int]:
        """Get count of songs for each emotion (for stats)."""
        # Return estimated counts (YouTube has millions of music videos)
        return {
            'Happy': 10000000,
            'Sad': 10000000,
            'Angry': 10000000,
            'Neutral': 10000000,
            'Surprise': 10000000,
            'Fear': 10000000,
            'Disgust': 10000000
        }
