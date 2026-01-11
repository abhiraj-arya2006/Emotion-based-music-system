"""
Spotify Web API Client
Handles authentication, token management, and API requests.
Uses Client Credentials Flow for server-to-server authentication.
"""

import os
import requests
import time
from typing import Dict, List, Optional
import base64

class SpotifyClient:
    """
    Spotify Web API client with token caching and error handling.
    """
    
    # Spotify API endpoints
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    SEARCH_URL = "https://api.spotify.com/v1/search"
    
    # Supported markets for multilingual content
    MARKETS = ['US', 'IN', 'ES', 'MX', 'KR']  # English, Hindi, Spanish, Korean
    
    def __init__(self):
        """Initialize Spotify client with credentials from environment variables."""
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Spotify credentials not found. Please set SPOTIFY_CLIENT_ID and "
                "SPOTIFY_CLIENT_SECRET environment variables."
            )
        
        self.access_token = None
        self.token_expires_at = 0
        self._get_access_token()
    
    def _get_access_token(self) -> str:
        """
        Get or refresh Spotify access token.
        Uses Client Credentials Flow (no user authentication required).
        
        Returns:
            Access token string
        """
        # Check if current token is still valid (with 60s buffer)
        if self.access_token and time.time() < self.token_expires_at - 60:
            return self.access_token
        
        # Prepare credentials for Client Credentials Flow
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(self.TOKEN_URL, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
            self.token_expires_at = time.time() + expires_in
            
            print("✅ Spotify access token obtained successfully")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting Spotify token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            raise
    
    def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        """
        Make authenticated request to Spotify API.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            JSON response or None if error
        """
        # Ensure we have a valid token
        self._get_access_token()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Spotify API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    print(f"   Error message: {error_msg}")
                    print(f"   Status code: {e.response.status_code}")
                except:
                    print(f"   Status code: {e.response.status_code}")
                    print(f"   Response text: {e.response.text[:200]}")
            else:
                print(f"   Connection error - check internet connection")
            return None
    
    def search_tracks(self, query: str, genre: Optional[str] = None, 
                     market: str = 'US', limit: int = 20) -> List[Dict]:
        """
        Search for tracks on Spotify.
        
        Args:
            query: Search query (can include artist, track name, etc.)
            genre: Optional genre filter
            market: Market code (US, IN, ES, MX, KR)
            limit: Number of results (max 50)
            
        Returns:
            List of track dictionaries
        """
        # Build search query
        search_query = query
        if genre:
            search_query = f"{query} genre:{genre}"
        
        params = {
            'q': search_query,
            'type': 'track',
            'market': market,
            'limit': min(limit, 50),  # Spotify max is 50
            'offset': 0
        }
        
        response = self._make_request(self.SEARCH_URL, params)
        
        if not response or 'tracks' not in response:
            return []
        
        tracks = []
        for item in response['tracks'].get('items', []):
            track_info = {
                'id': item['id'],
                'name': item['name'],
                'artist': ', '.join([artist['name'] for artist in item['artists']]),
                'artist_ids': [artist['id'] for artist in item['artists']],
                'album': item['album']['name'],
                'album_art': item['album']['images'][0]['url'] if item['album']['images'] else None,
                'preview_url': item.get('preview_url'),
                'external_url': item['external_urls']['spotify'],
                'popularity': item.get('popularity', 0),
                'duration_ms': item.get('duration_ms', 0),
                'market': market
            }
            tracks.append(track_info)
        
        return tracks
    
    def search_by_genre(self, genres: List[str], market: str = 'US', 
                      limit: int = 20, min_popularity: int = 30) -> List[Dict]:
        """
        Search for tracks by genre(s).
        
        Args:
            genres: List of genre names
            market: Market code
            limit: Number of results
            min_popularity: Minimum popularity score (0-100)
            
        Returns:
            List of track dictionaries, sorted by popularity
        """
        # Build genre query
        genre_query = ' OR '.join([f'genre:"{genre}"' for genre in genres])
        
        params = {
            'q': genre_query,
            'type': 'track',
            'market': market,
            'limit': min(limit, 50),
            'offset': 0
        }
        
        response = self._make_request(self.SEARCH_URL, params)
        
        if not response or 'tracks' not in response:
            return []
        
        tracks = []
        for item in response['tracks'].get('items', []):
            popularity = item.get('popularity', 0)
            if popularity >= min_popularity:
                track_info = {
                    'id': item['id'],
                    'name': item['name'],
                    'artist': ', '.join([artist['name'] for artist in item['artists']]),
                    'artist_ids': [artist['id'] for artist in item['artists']],
                    'album': item['album']['name'],
                    'album_art': item['album']['images'][0]['url'] if item['album']['images'] else None,
                    'preview_url': item.get('preview_url'),
                    'external_url': item['external_urls']['spotify'],
                    'popularity': popularity,
                    'duration_ms': item.get('duration_ms', 0),
                    'market': market
                }
                tracks.append(track_info)
        
        # Sort by popularity (descending)
        tracks.sort(key=lambda x: x['popularity'], reverse=True)
        
        return tracks
    
    def get_multilingual_tracks(self, genres: List[str], limit_per_market: int = 10) -> List[Dict]:
        """
        Get tracks from multiple markets for multilingual diversity.
        
        Args:
            genres: List of genres to search
            limit_per_market: Number of tracks per market
            
        Returns:
            Combined list of tracks from all markets
        """
        all_tracks = []
        
        for market in self.MARKETS:
            tracks = self.search_by_genre(
                genres=genres,
                market=market,
                limit=limit_per_market,
                min_popularity=20  # Lower threshold for diversity
            )
            all_tracks.extend(tracks)
        
        # Remove duplicates (same track ID)
        seen_ids = set()
        unique_tracks = []
        for track in all_tracks:
            if track['id'] not in seen_ids:
                seen_ids.add(track['id'])
                unique_tracks.append(track)
        
        # Sort by popularity
        unique_tracks.sort(key=lambda x: x['popularity'], reverse=True)
        
        return unique_tracks
    
    def get_playlist_tracks(self, playlist_id: str, market: str = 'US', limit: int = 50) -> List[Dict]:
        """
        Get tracks from a Spotify playlist.
        
        Args:
            playlist_id: Spotify playlist ID
            market: Market code for track availability
            limit: Maximum number of tracks to return
            
        Returns:
            List of track dictionaries
        """
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        
        params = {
            'market': market,
            'limit': min(limit, 100),  # Spotify max is 100
            'offset': 0
        }
        
        response = self._make_request(url, params)
        
        if not response or 'items' not in response:
            return []
        
        tracks = []
        for item in response['items']:
            if 'track' in item and item['track']:
                track = item['track']
                track_info = {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'artist_ids': [artist['id'] for artist in track['artists']],
                    'album': track['album']['name'],
                    'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    'preview_url': track.get('preview_url'),
                    'external_url': track['external_urls']['spotify'],
                    'popularity': track.get('popularity', 0),
                    'duration_ms': track.get('duration_ms', 0),
                    'market': market,
                    'playlist_id': playlist_id
                }
                tracks.append(track_info)
        
        return tracks
    
    def infer_language(self, track: Dict) -> str:
        """
        Infer language from track metadata.
        Uses market, artist name, and track name as hints.
        
        Args:
            track: Track dictionary
            
        Returns:
            Inferred language name
        """
        market = track.get('market', 'US')
        artist = track.get('artist', '').lower()
        track_name = track.get('name', '').lower()
        
        # Market-based inference
        market_lang_map = {
            'US': 'English',
            'IN': 'Hindi',  # Could be Hindi, Punjabi, Tamil, etc.
            'ES': 'Spanish',
            'MX': 'Spanish',
            'KR': 'Korean'
        }
        
        # Check for language indicators in text
        if any(word in artist or word in track_name for word in ['punjabi', 'punjab']):
            return 'Punjabi'
        if any(word in artist or word in track_name for word in ['hindi', 'bollywood']):
            return 'Hindi'
        if any(word in artist or word in track_name for word in ['tamil', 'kollywood']):
            return 'Tamil'
        if any(word in artist or word in track_name for word in ['telugu', 'tollywood']):
            return 'Telugu'
        if any(word in artist or word in track_name for word in ['korean', 'k-pop', 'kpop']):
            return 'Korean'
        if any(word in artist or word in track_name for word in ['spanish', 'español', 'latino']):
            return 'Spanish'
        
        # Default to market language
        return market_lang_map.get(market, 'English')

