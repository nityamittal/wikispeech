"""
Download Manager for Wikispeech Article Downloads

Manages metadata and file storage for article audio downloads.
Uses JSON file for metadata and filesystem for MP3 files.
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
import threading


class DownloadManager:
    """Manages article download metadata and file storage."""
    
    def __init__(self, storage_dir):
        """
        Initialize the download manager.
        
        Args:
            storage_dir: Base directory for download storage
        """
        self.storage_dir = Path(storage_dir)
        self.files_dir = self.storage_dir / "files"
        self.metadata_file = self.storage_dir / "metadata.json"
        self._lock = threading.Lock()
        
        # Ensure directories exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(exist_ok=True)
        
        # Initialize metadata file if it doesn't exist
        if not self.metadata_file.exists():
            self._save_metadata({"downloads": []})
    
    def _load_metadata(self):
        """Load metadata from JSON file."""
        with self._lock:
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {"downloads": []}
    
    def _save_metadata(self, metadata):
        """Save metadata to JSON file."""
        with self._lock:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def generate_hash(self, content, params):
        """
        Generate unique hash for download based on content and parameters.
        
        Args:
            content: Article text content
            params: Dict of synthesis parameters (lang, voice, speed, pitch, volume)
            
        Returns:
            Hash string (sha256)
        """
        # Create deterministic string from content and params
        param_str = json.dumps(params, sort_keys=True)
        combined = f"{content}|{param_str}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def find_download(self, content_hash):
        """
        Find download by hash.
        
        Args:
            content_hash: Hash to search for
            
        Returns:
            Download metadata dict or None if not found
        """
        metadata = self._load_metadata()
        for download in metadata["downloads"]:
            if download["hash"] == content_hash:
                return download
        return None
    
    def search_downloads(self, title=None, lang=None, voice=None, limit=None):
        """
        Search downloads by criteria.
        
        Args:
            title: Article title to match (partial match)
            lang: Language code to match
            voice: Voice name to match
            limit: Maximum number of results
            
        Returns:
            List of download metadata dicts
        """
        metadata = self._load_metadata()
        results = metadata["downloads"]
        
        if title:
            title_lower = title.lower()
            results = [d for d in results if title_lower in d.get("title", "").lower()]
        
        if lang:
            results = [d for d in results if d.get("params", {}).get("lang") == lang]
        
        if voice:
            results = [d for d in results if d.get("params", {}).get("voice") == voice]
        
        # Sort by creation date (newest first)
        results.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        if limit:
            results = results[:limit]
        
        return results
    
    def add_download(self, title, content_hash, params, file_path, size_bytes):
        """
        Add a new download to metadata.
        
        Args:
            title: Article title
            content_hash: Hash of content + params
            params: Dict of synthesis parameters
            file_path: Relative path to MP3 file (from storage_dir)
            size_bytes: File size in bytes
            
        Returns:
            Download metadata dict with generated ID
        """
        download_id = content_hash[:16]  # Use first 16 chars of hash as ID
        
        download = {
            "id": download_id,
            "title": title,
            "hash": content_hash,
            "params": params,
            "created": datetime.utcnow().isoformat() + "Z",
            "file": file_path,
            "size_bytes": size_bytes
        }
        
        metadata = self._load_metadata()
        
        # Check if already exists (by hash)
        existing = self.find_download(content_hash)
        if existing:
            return existing
        
        metadata["downloads"].append(download)
        self._save_metadata(metadata)
        
        return download
    
    def get_file_path(self, download_id):
        """
        Get absolute file path for a download.
        
        Args:
            download_id: Download ID
            
        Returns:
            Absolute Path object or None if not found
        """
        metadata = self._load_metadata()
        for download in metadata["downloads"]:
            if download["id"] == download_id:
                return self.storage_dir / download["file"]
        return None
    
    def delete_download(self, download_id):
        """
        Delete a download and its file.
        
        Args:
            download_id: Download ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        metadata = self._load_metadata()
        
        # Find and remove from metadata
        download = None
        for i, d in enumerate(metadata["downloads"]):
            if d["id"] == download_id:
                download = metadata["downloads"].pop(i)
                break
        
        if not download:
            return False
        
        # Delete file
        file_path = self.storage_dir / download["file"]
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError:
            pass  # File already deleted or inaccessible
        
        self._save_metadata(metadata)
        return True
    
    def cleanup_old_downloads(self, max_age_days):
        """
        Delete downloads older than specified days.
        
        Args:
            max_age_days: Maximum age in days
            
        Returns:
            Number of downloads deleted
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        metadata = self._load_metadata()
        
        to_delete = []
        for download in metadata["downloads"]:
            created_str = download.get("created", "")
            try:
                # Parse ISO format datetime
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                if created < cutoff:
                    to_delete.append(download["id"])
            except (ValueError, AttributeError):
                continue
        
        count = 0
        for download_id in to_delete:
            if self.delete_download(download_id):
                count += 1
        
        return count
    
    def get_stats(self):
        """
        Get storage statistics.
        
        Returns:
            Dict with total_downloads, total_size_bytes
        """
        metadata = self._load_metadata()
        downloads = metadata["downloads"]
        
        return {
            "total_downloads": len(downloads),
            "total_size_bytes": sum(d.get("size_bytes", 0) for d in downloads)
        }
