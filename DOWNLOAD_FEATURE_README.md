# Article Download Feature - Implementation Complete

## Overview
Implemented a complete UI and API system for downloading Wikipedia/MediaWiki articles as MP3 audio files.

## Files Created/Modified

### New Files
1. **`wikispeech_server/download_manager.py`** - Storage manager for download metadata and files
2. **`wikispeech_server/article_fetcher.py`** - Wikipedia/MediaWiki article fetcher
3. **`wikispeech_server/templates/download.html`** - Web UI for article downloads
4. **`test_download_feature.py`** - Unit tests for download functionality

### Modified Files
1. **`wikispeech_server/wikispeech.py`**
   - Added `convertToMP3()` function for MP3 conversion
   - Added `concatenateAudioFiles()` function for joining audio segments
   - Added 3 API endpoints: `/api/download/check`, `/api/download/request`, `/download/<id>`
   - Added UI route: `/download` and `/download.html`

2. **`wikispeech_server/default.conf`**
   - Added `[Downloads]` section with configuration options

3. **`wikispeech_server/config.py`**
   - Fixed Python 3 compatibility (`SafeConfigParser` → `ConfigParser`)

## Features Implemented

### 1. Download Storage Manager (`download_manager.py`)
- JSON-based metadata storage
- Hash-based duplicate detection
- File management for MP3s
- Search and filtering capabilities
- Automatic cleanup of old downloads

### 2. Article Fetcher (`article_fetcher.py`)
- Fetches articles from Wikipedia/MediaWiki URLs
- Extracts clean plain text via MediaWiki API
- URL validation
- Text cleaning and normalization

### 3. Audio Processing
- **MP3 Conversion**: Uses ffmpeg to convert audio to MP3 format
- **Audio Concatenation**: Combines multiple paragraph audio files into single download
- **Quality Settings**: High-quality MP3 encoding (VBR quality 2)

### 4. API Endpoints

#### POST `/api/download/check`
Check if a download already exists for given content and parameters.

**Request:**
```json
{
  "content": "article text" OR "url": "https://en.wikipedia.org/wiki/Article",
  "title": "Article Title",
  "params": {
    "lang": "en",
    "voice": "voice_name",
    "speed": 1.0,
    "pitch": 1.0,
    "volume": 1.0
  }
}
```

**Response:**
```json
{
  "exists": true,
  "download": {
    "id": "abc123",
    "title": "Article Title",
    "hash": "...",
    "params": {...},
    "created": "2026-04-04T12:00:00Z",
    "file": "files/abc123.mp3",
    "size_bytes": 1234567
  }
}
```

#### POST `/api/download/request`
Request a new article download (generates audio if not exists).

**Request:** Same as `/check`

**Response:**
```json
{
  "success": true,
  "download": { /* download metadata */ }
}
```

#### GET `/download/<download_id>`
Serve the MP3 file for download.

### 5. Web UI (`/download` or `/download.html`)

**Features:**
- Tab-based input: Text or URL
- Parameter controls: Language, Voice, Speed, Pitch, Volume
- Check for existing downloads
- Request new downloads
- Display existing downloads with download links
- Progress indication
- Responsive design

## Configuration

Added to `default.conf`:
```ini
[Downloads]
# Directory for storing article downloads
download_dir: wikispeech_server/downloads
# Maximum file size for downloads in MB (0 = unlimited)
max_download_size_mb: 100
# Retention period for downloads in days (0 = keep forever)
retention_days: 30
```

## Dependencies

### Python Packages (already in requirements.txt)
- `requests` - For fetching Wikipedia articles
- `flask` - Web framework
- `flask_cors` - CORS support

### System Requirements
- **ffmpeg** - Required for MP3 conversion
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: Download from https://ffmpeg.org/

## Testing the Feature

### 1. Unit Tests
Run the included unit tests:
```bash
python3 test_download_feature.py
```

This tests:
- Download manager hash generation, storage, and search
- Article fetcher URL validation and text cleaning
- Audio conversion prerequisites (ffmpeg availability)

### 2. Manual Testing via UI

1. Start the Wikispeech server:
   ```bash
   python3 bin/wikispeech
   ```

2. Open browser to: `http://localhost:10000/download`

3. Test scenarios:
   - **Text Input**: Paste article text, select language/voice, request download
   - **URL Input**: Enter Wikipedia URL (e.g., `https://en.wikipedia.org/wiki/Python_(programming_language)`), request download
   - **Check Existing**: Submit same content/params again to see existing download
   - **Parameter Variations**: Change speed/pitch/volume to create different versions

### 3. API Testing via curl

**Check for existing download:**
```bash
curl -X POST http://localhost:10000/api/download/check \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is a test article.",
    "title": "Test",
    "params": {
      "lang": "en",
      "voice": "cmu-slt-flite",
      "speed": 1.0,
      "pitch": 1.0,
      "volume": 1.0
    }
  }'
```

**Request new download:**
```bash
curl -X POST http://localhost:10000/api/download/request \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://en.wikipedia.org/wiki/Cat",
    "params": {
      "lang": "en",
      "voice": "cmu-slt-flite",
      "speed": 1.0,
      "pitch": 1.0,
      "volume": 1.0
    }
  }'
```

**Download file:**
```bash
curl -O -J http://localhost:10000/download/<download_id>
```

## How It Works

### Download Request Flow

1. **User submits article** (text or URL)
2. **System generates hash** from content + parameters
3. **Check for existing download** with same hash
4. **If exists**: Return existing download metadata
5. **If new**:
   - Split article into paragraphs
   - For each paragraph:
     - Convert text to markup (textproc)
     - Synthesize audio (existing TTS pipeline)
     - Save audio to temp file
   - Concatenate all audio files
   - Convert concatenated audio to MP3
   - Store MP3 file and metadata
   - Return download metadata

### Storage Structure
```
wikispeech_server/downloads/
├── metadata.json          # Index of all downloads
└── files/
    ├── abc123def456.mp3  # Generated audio files
    └── xyz789abc123.mp3
```

### Duplicate Detection
Downloads are uniquely identified by SHA256 hash of:
- Article content (full text)
- All parameters (lang, voice, speed, pitch, volume)

Same content + parameters = same hash = reuse existing download

## Known Issues & Notes

### TTS Engine Dependencies
The actual audio generation requires working TTS engines:
- **flite** - For English voices
- **MaryTTS** - For some other voices
- **espeak/mbrola** - For additional languages

If TTS engines have issues, the API will return errors during the synthesis step, but the download infrastructure is complete and functional.

### Audio Format
- Generated audio is initially in Opus format (from existing pipeline)
- Converted to MP3 for wider compatibility and smaller file sizes
- Uses VBR encoding with quality level 2 (high quality, ~170-210 kbps)

### Performance
- Long articles may take time to process (1 paragraph ≈ 2-5 seconds)
- Consider adding progress updates for very long articles
- Downloads are synchronous (request blocks until complete)
- For production, consider async processing with job queue

## Future Enhancements

Potential improvements not implemented:
1. **Async Processing**: Use Celery/RQ for background job processing
2. **Progress Updates**: WebSocket or SSE for real-time progress
3. **Batch Downloads**: Download multiple articles at once
4. **Format Options**: Support WAV, OGG, M4A in addition to MP3
5. **Quality Selector**: Let users choose audio quality/bitrate
6. **Admin Panel**: View all downloads, manage storage
7. **User Accounts**: Track downloads per user
8. **Download Statistics**: Track popular articles, usage metrics

## Code Quality

- All modules have docstrings
- Functions include parameter and return type documentation
- Error handling with try/except blocks
- Thread-safe metadata operations (using locks)
- Input validation on all API endpoints
- Proper HTTP status codes (200, 400, 404, 413, 500)
- Clean separation of concerns (storage, fetching, API, UI)

## Troubleshooting

### "ffmpeg not found" error
Install ffmpeg: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Linux)

### "Download not found" error
Check `wikispeech_server/downloads/` directory exists and has correct permissions

### "Text processing failed" error
Textprocessor for the language may not be loaded. Check available languages at `/languages`

### "Synthesis failed" error
Voice engine issues. Check that required TTS engines are running and accessible.

### Empty downloads list
This is normal on first run. Create a download to populate the list.

## Success Criteria ✓

All requirements from the original task have been implemented:

✅ Special page UI for specifying download parameters  
✅ Article input via text or URL  
✅ Parameter selection (language, voice, speed, pitch, volume)  
✅ Check if article already available for download  
✅ Show multiple versions if different parameters  
✅ Button to request new download  
✅ Link to download MP3 file  
✅ File storage and metadata tracking  
✅ Duplicate detection via hashing  

The feature is complete and ready for testing with working TTS engines!
