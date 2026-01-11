"""
YouTube Data API v3 Client
Handles authentication, search queries, and video metadata retrieval.
Uses API key authentication with request caching.
"""

import os
import requests
import time
from typing import Dict, List, Optional
from functools import lru_cache
import hashlib
import json

class YouTubeClient:
    """
    YouTube Data API v3 client with caching and error handling.
    """
    
    # YouTube API endpoints
    SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
    VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
    
    # Supported languages for search
    LANGUAGE_KEYWORDS = {
        'English': 'english',
        'Hindi': 'hindi',
        'Punjabi': 'punjabi',
        'Tamil': 'tamil',
        'Telugu': 'telugu',
        'Korean': 'korean',
        'Spanish': 'spanish'
    }
    
    def __init__(self):
        """Initialize YouTube client with API key from environment variables."""
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "YouTube API key not found. Please set YOUTUBE_API_KEY environment variable."
            )
        
        # Simple in-memory cache (can be enhanced with Redis/file cache)
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
        
        print("[OK] YouTube client initialized successfully")
    
    def _get_cache_key(self, query: str, language: str) -> str:
        """Generate cache key for query."""
        cache_str = f"{query}_{language}"
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Get data from cache if not expired."""
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            else:
                del self._cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, data: List[Dict]):
        """Save data to cache."""
        self._cache[cache_key] = (data, time.time())
    
    def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        """
        Make authenticated request to YouTube API.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            JSON response or None if error
        """
        params['key'] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] YouTube API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    print(f"   Error message: {error_msg}")
                    print(f"   Status code: {e.response.status_code}")
                except:
                    print(f"   Status code: {e.response.status_code}")
            return None
    
    def search_music_videos(self, mood: str, language: str, max_results: int = 10) -> List[Dict]:
        """
        Search for music videos on YouTube.
        
        Args:
            mood: Mood keyword (e.g., "happy", "sad", "energetic")
            language: Language keyword (e.g., "hindi", "english")
            max_results: Maximum number of results (default 10)
            
        Returns:
            List of video dictionaries with metadata
        """
        # Check cache first
        cache_key = self._get_cache_key(mood, language)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            print(f"[CACHE] Using cached results for {mood} {language}")
            return cached_result[:max_results]
        
        # Build search query: mood + "song" + language
        language_keyword = self.LANGUAGE_KEYWORDS.get(language, language.lower())
        query = f"{mood} {language_keyword} song"
        
        # Search parameters
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'videoCategoryId': '10',  # Music category
            'maxResults': min(max_results, 50),  # YouTube max is 50
            'order': 'relevance',
            'safeSearch': 'none'
        }
        
        response = self._make_request(self.SEARCH_URL, params)
        
        if not response or 'items' not in response:
            print(f"[WARNING] No search results for query: {query}")
            return []
        
        # Get video IDs
        video_ids = [item['id']['videoId'] for item in response['items']]
        
        if not video_ids:
            return []
        
        # Get detailed video information
        videos = self.get_video_details(video_ids)
        
        # Filter to ensure they're music videos (category 10)
        music_videos = [v for v in videos if v.get('category_id') == '10']
        
        # Save to cache
        self._save_to_cache(cache_key, music_videos)
        
        return music_videos[:max_results]
    
    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """
        Get detailed information for video IDs.
        
        Args:
            video_ids: List of YouTube video IDs
            
        Returns:
            List of video dictionaries with full metadata
        """
        if not video_ids:
            return []
        
        # YouTube API allows up to 50 IDs per request
        all_videos = []
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            params = {
                'part': 'snippet,statistics,contentDetails',
                'id': ','.join(batch_ids)
            }
            
            response = self._make_request(self.VIDEO_URL, params)
            
            if response and 'items' in response:
                for item in response['items']:
                    video_info = {
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet'].get('description', ''),
                        'channel_title': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                        'view_count': int(item['statistics'].get('viewCount', 0)),
                        'like_count': int(item['statistics'].get('likeCount', 0)),
                        'duration': item['contentDetails'].get('duration', ''),
                        'category_id': item['snippet'].get('categoryId', ''),
                        'embed_url': f"https://www.youtube.com/embed/{item['id']}",
                        'watch_url': f"https://www.youtube.com/watch?v={item['id']}"
                    }
                    all_videos.append(video_info)
        
        return all_videos
    
    def infer_language(self, video: Dict) -> str:
        """
        Infer language from video metadata.
        
        Args:
            video: Video dictionary with title, description, etc.
            
        Returns:
            Inferred language name
        """
        title = video.get('title', '').lower()
        description = video.get('description', '').lower()
        channel = video.get('channel_title', '').lower()
        
        text = f"{title} {description} {channel}"
        
        # Language detection based on keywords
        if any(keyword in text for keyword in ['hindi', 'bollywood', 'hindi song']):
            return 'Hindi'
        elif any(keyword in text for keyword in ['punjabi', 'punjab', 'bhangra']):
            return 'Punjabi'
        elif any(keyword in text for keyword in ['tamil', 'kollywood', 'tamil song']):
            return 'Tamil'
        elif any(keyword in text for keyword in ['telugu', 'tollywood', 'telugu song']):
            return 'Telugu'
        elif any(keyword in text for keyword in ['korean', 'k-pop', 'kpop', 'korean song']):
            return 'Korean'
        elif any(keyword in text for keyword in ['spanish', 'español', 'latino', 'spanish song']):
            return 'Spanish'
        else:
            return 'English'  # Default
    
    def get_multilingual_music(self, mood: str, languages: List[str], 
                              max_per_language: int = 10) -> List[Dict]:
        """
        Get music videos from multiple languages.
        
        Args:
            mood: Mood keyword
            languages: List of language names
            max_per_language: Maximum videos per language
            
        Returns:
            Combined list of videos from all languages
        """
        all_videos = []
        
        for language in languages:
            try:
                videos = self.search_music_videos(mood, language, max_per_language)
                # Add language info to each video
                for video in videos:
                    video['searched_language'] = language
                    video['language'] = self.infer_language(video)
                all_videos.extend(videos)
                # Small delay to avoid rate limiting
                time.sleep(0.1)
            except Exception as e:
                print(f"[WARNING] Error searching {language} videos: {e}")
                continue
        
        # Remove duplicates (same video ID)
        seen_ids = set()
        unique_videos = []
        for video in all_videos:
            if video['id'] not in seen_ids:
                seen_ids.add(video['id'])
                unique_videos.append(video)
        
        # Sort by view count (popularity)
        unique_videos.sort(key=lambda x: x.get('view_count', 0), reverse=True)
        
        return unique_videos

