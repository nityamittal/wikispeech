#!/usr/bin/env python3
"""
Test script for article download functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wikispeech_server.download_manager import DownloadManager
from wikispeech_server.article_fetcher import ArticleFetcher

def test_download_manager():
    """Test DownloadManager functionality"""
    print("Testing DownloadManager...")
    
    # Create manager with temp directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        dm = DownloadManager(tmpdir)
        
        # Test hash generation
        content = "This is a test article."
        params = {"lang": "en", "voice": "test_voice", "speed": 1.0}
        hash1 = dm.generate_hash(content, params)
        hash2 = dm.generate_hash(content, params)
        
        assert hash1 == hash2, "Same content should generate same hash"
        print("  ✓ Hash generation works")
        
        # Test adding download
        download = dm.add_download(
            title="Test Article",
            content_hash=hash1,
            params=params,
            file_path="files/test.mp3",
            size_bytes=1024
        )
        
        assert download['title'] == "Test Article"
        assert download['hash'] == hash1
        print("  ✓ Adding download works")
        
        # Test finding download
        found = dm.find_download(hash1)
        assert found is not None
        assert found['title'] == "Test Article"
        print("  ✓ Finding download works")
        
        # Test search
        results = dm.search_downloads(title="Test")
        assert len(results) == 1
        print("  ✓ Searching downloads works")
        
        # Test stats
        stats = dm.get_stats()
        assert stats['total_downloads'] == 1
        assert stats['total_size_bytes'] == 1024
        print("  ✓ Stats calculation works")
    
    print("✓ DownloadManager tests passed!\n")

def test_article_fetcher():
    """Test ArticleFetcher functionality"""
    print("Testing ArticleFetcher...")
    
    fetcher = ArticleFetcher()
    
    # Test URL validation
    valid_urls = [
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://en.wikipedia.org/w/index.php?title=Python",
    ]
    
    for url in valid_urls:
        assert fetcher.validate_url(url), f"Should validate: {url}"
    print("  ✓ URL validation works")
    
    # Test title extraction
    url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    title = fetcher._extract_title_from_url(url)
    assert title == "Python_(programming_language)"
    print("  ✓ Title extraction works")
    
    # Test text cleaning
    dirty_text = "Text   with    spaces\n\n\n\nand lines"
    clean = fetcher._clean_text(dirty_text)
    assert "   " not in clean
    assert "\n\n\n" not in clean
    print("  ✓ Text cleaning works")
    
    print("✓ ArticleFetcher tests passed!\n")

def test_audio_conversion():
    """Test audio conversion functions"""
    print("Testing audio conversion...")
    
    # Check if ffmpeg is available
    import subprocess
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        print("  ✓ ffmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ✗ ffmpeg is not available (required for MP3 conversion)")
        return
    
    print("✓ Audio conversion prerequisites met!\n")

if __name__ == '__main__':
    print("=" * 60)
    print("Article Download Feature Tests")
    print("=" * 60 + "\n")
    
    try:
        test_download_manager()
        test_article_fetcher()
        test_audio_conversion()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
