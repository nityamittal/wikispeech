"""
Article Fetcher for Wikispeech

Fetches article text from Wikipedia/MediaWiki URLs and extracts clean text.
"""

import re
import requests
from urllib.parse import urlparse, parse_qs
import html


class ArticleFetcher:
    """Fetches and parses article text from Wikipedia/MediaWiki."""
    
    def __init__(self, timeout=10):
        """
        Initialize the article fetcher.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Wikispeech/1.0 (Text-to-Speech service)'
        })
    
    def fetch_article(self, url):
        """
        Fetch article from URL and extract text.
        
        Args:
            url: Wikipedia/MediaWiki article URL
            
        Returns:
            Dict with 'title' and 'text' keys
            
        Raises:
            ValueError: If URL is invalid or not a MediaWiki site
            requests.RequestException: If request fails
        """
        # Parse URL to determine the API endpoint
        parsed = urlparse(url)
        
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")
        
        # Extract article title from URL
        title = self._extract_title_from_url(url)
        
        if not title:
            raise ValueError(f"Could not extract article title from URL: {url}")
        
        # Construct API URL
        api_url = f"{parsed.scheme}://{parsed.netloc}/w/api.php"
        
        # Fetch article using MediaWiki API
        params = {
            'action': 'query',
            'format': 'json',
            'titles': title,
            'prop': 'extracts',
            'explaintext': True,  # Get plain text
            'exsectionformat': 'plain'
        }
        
        response = self.session.get(api_url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract page content
        pages = data.get('query', {}).get('pages', {})
        
        if not pages:
            raise ValueError(f"No content found for article: {title}")
        
        # Get first page (should be only one)
        page = next(iter(pages.values()))
        
        if 'missing' in page:
            raise ValueError(f"Article not found: {title}")
        
        article_title = page.get('title', title)
        extract = page.get('extract', '')
        
        if not extract:
            raise ValueError(f"Article has no text content: {title}")
        
        # Clean up the text
        text = self._clean_text(extract)
        
        return {
            'title': article_title,
            'text': text
        }
    
    def _extract_title_from_url(self, url):
        """
        Extract article title from Wikipedia/MediaWiki URL.
        
        Supports formats:
        - /wiki/Article_Name
        - /w/index.php?title=Article_Name
        - Special URL encoded characters
        """
        parsed = urlparse(url)
        path = parsed.path
        
        # Check for /wiki/ format
        wiki_match = re.match(r'/wiki/(.+)', path)
        if wiki_match:
            title = wiki_match.group(1)
            # URL decode
            from urllib.parse import unquote
            return unquote(title)
        
        # Check for query parameter format
        query_params = parse_qs(parsed.query)
        if 'title' in query_params:
            return query_params['title'][0]
        
        return None
    
    def _clean_text(self, text):
        """
        Clean extracted text.
        
        Removes excessive whitespace, formatting artifacts, etc.
        """
        # Unescape HTML entities
        text = html.unescape(text)
        
        # Remove multiple newlines (keep paragraph breaks)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove excessive spaces
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove empty lines at start and end
        text = text.strip()
        
        return text
    
    def validate_url(self, url):
        """
        Validate if URL looks like a Wikipedia/MediaWiki URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Check if it looks like a wiki URL
            path = parsed.path.lower()
            if '/wiki/' in path or '/w/index.php' in path:
                return True
            
            # Check for common wiki domains
            netloc_lower = parsed.netloc.lower()
            if 'wikipedia.org' in netloc_lower or 'mediawiki.org' in netloc_lower:
                return True
            
            return False
            
        except Exception:
            return False
