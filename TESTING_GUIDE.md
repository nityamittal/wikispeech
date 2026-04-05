# Quick Test Guide - Article Download Feature

## Prerequisites
```bash
# Install dependencies
pip3 install -r requirements.txt

# Install ffmpeg (for MP3 conversion)
brew install ffmpeg  # macOS
# OR
sudo apt install ffmpeg  # Linux

# Create required directories
mkdir -p wikispeech_server/tmp
mkdir -p wikispeech_server/downloads/files
```

## Start Server
```bash
cd /path/to/wikispeech
python3 bin/wikispeech
```

Server will start on: `http://localhost:10000`

## Test the UI
1. Open browser to: `http://localhost:10000/download`
2. Try the "Text Input" tab:
   - Title: "Test Article"
   - Text: "This is a test. It has multiple sentences."
   - Language: en
   - Voice: (select from dropdown)
   - Click "Check for Existing Download"
   - Click "Request New Download"

## Test via Command Line

### Check API
```bash
curl http://localhost:10000/ping
# Should return: wikispeech
```

### Check Languages
```bash
curl http://localhost:10000/languages
```

### Check Voices
```bash
curl http://localhost:10000/synthesis/voices
```

### Request Download
```bash
curl -X POST http://localhost:10000/api/download/request \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is a test article with some text.",
    "title": "Test Article",
    "params": {
      "lang": "en",
      "voice": "cmu-slt-flite",
      "speed": 1.0,
      "pitch": 1.0,
      "volume": 1.0
    }
  }'
```

### Download File
```bash
# Get download ID from above response, then:
curl -O -J http://localhost:10000/download/<download_id>
```

## Expected File Structure After Testing
```
wikispeech_server/
├── downloads/
│   ├── metadata.json
│   └── files/
│       └── <hash>.mp3
└── tmp/
    └── (temporary files during processing)
```

## Common Issues

**Problem**: TTS synthesis errors  
**Cause**: Voice engines (flite, marytts) not working  
**Note**: This is expected - focus on testing the download infrastructure

**Problem**: "ffmpeg not found"  
**Solution**: Install ffmpeg (see prerequisites)

**Problem**: "No such file or directory: wikispeech_server/tmp"  
**Solution**: `mkdir -p wikispeech_server/tmp wikispeech_server/downloads/files`

## What to Test

1. ✅ UI loads at `/download`
2. ✅ Language dropdown populates
3. ✅ Voice dropdown updates when language changes
4. ✅ Can submit text input
5. ✅ Can submit URL input (if Wikipedia API accessible)
6. ✅ API endpoints return proper JSON
7. ✅ Downloads are stored in `wikispeech_server/downloads/`
8. ✅ Duplicate detection works (same content returns existing download)
9. ✅ MP3 files are playable
10. ✅ Download link serves file with correct filename

## Success!
If the API returns proper JSON responses and the UI renders correctly, the implementation is working. Audio synthesis errors are expected if TTS engines aren't configured.
