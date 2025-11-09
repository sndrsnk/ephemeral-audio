# Ephemeral Audio API - Project Context

## What This Is

A Flask-based API that serves audio files with a unique twist: the audio degrades permanently as people listen to it. Each 0.5-second segment of audio deteriorates when played, creating an ephemeral listening experience.

## Current State

The API is **production-ready** and separated from the main 11ty website. The frontend player now lives in the 11ty site at `/ephemeral-audio`, and this repo contains only the backend API.

## Architecture

**Backend (this repo):**
- Flask API with gunicorn for production
- Streams WAV files with range request support (for seeking)
- Tracks segment play counts in JSON metadata files
- Applies progressive audio degradation using numpy/scipy
- Thread-safe segment locking to prevent race conditions

**Frontend (separate 11ty site):**
- Tone.js-based audio player
- Waveform visualization with canvas
- Real-time degradation tracking
- Calls this API at `https://api.yourdomain.com`

## Key Files

- `app.py` - Main Flask application with all endpoints
- `degradation.py` - Audio degradation algorithms (dropout effect)
- `streaming.py` - Audio streaming service (currently unused, kept for reference)
- `streaming_readonly.py` - Read-only streaming (currently unused)
- `metadata.py` - Manages track metadata and play counts
- `lock_manager.py` - Thread-safe segment locking
- `wav_handler.py` - WAV file reading/writing utilities
- `pyproject.toml` - Python dependencies (Flask, numpy, scipy, gunicorn, flask-cors)
- `Procfile` - Gunicorn production startup command

## API Endpoints

- `GET /` - Health check
- `GET /tracks` - List all tracks with degradation stats
- `GET /stream/<filename>` - Stream audio with range support
- `POST /degrade/<filename>` - Degrade a specific segment
- `GET /stats/<filename>` - Detailed track statistics

## How Degradation Works

1. Audio files are divided into 0.5-second segments
2. Each segment has a play count stored in metadata
3. When a segment is played, the API:
   - Reads the segment from the WAV file
   - Applies dropout based on play count (1% per play by default)
   - Writes the degraded audio back to the file
   - Increments the play count
4. The degradation is **permanent** - the file is modified on disk

## Environment Variables

```env
PORT=5000
CORS_ORIGIN=https://yourdomain.com
AUDIO_DIR=/app/audio
METADATA_DIR=/app/metadata
SEGMENT_DURATION=0.5
DEGRADATION_RATE=1.0
FLASK_DEBUG=False
```

## Deployment (Coolify)

Ready to deploy on Coolify/Hetzner VPS:

1. **Application Type:** Python
2. **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app`
3. **Domain:** `api.yourdomain.com`
4. **Persistent Volumes:**
   - `/app/audio` - Audio files storage
   - `/app/metadata` - Degradation metadata (JSON files)

See `README.coolify.md` for detailed deployment instructions.

## Next Steps / TODO

### Immediate
- [ ] Deploy to Coolify on Hetzner VPS
- [ ] Upload audio files to persistent volume
- [ ] Test with production frontend

### Future Enhancements
- [ ] Add authentication/rate limiting
- [ ] Support for more audio formats (MP3, FLAC)
- [ ] Admin interface for uploading/managing tracks
- [ ] Analytics dashboard (play counts, degradation over time)
- [ ] Backup/restore functionality for audio files
- [ ] WebSocket support for real-time degradation updates
- [ ] Option to "reset" a track (restore from backup)

### Performance Considerations
- Current implementation modifies files on disk (I/O intensive)
- For high traffic, consider:
  - Caching degraded segments in memory
  - Queue-based degradation processing
  - Read replicas for streaming
  - CDN for static audio delivery (though this defeats the purpose!)

## Testing

```bash
# Install dependencies
uv sync

# Run tests
pytest

# Run locally
python app.py

# Test endpoints
curl http://localhost:5000/tracks
curl http://localhost:5000/stream/your-audio.wav
```

## Migration Notes

This code was originally in the `/ephemeral-audio` directory of the main 11ty site repo. It has been separated into its own repository for:
- Independent deployment cycles
- Clearer separation of concerns
- Easier API versioning
- Potential reuse in other projects

The frontend player was moved to `src/content/ephemeral-audio.njk` in the 11ty site and updated to call this API.

## Technical Decisions

**Why Flask?** Lightweight, simple for this use case, good streaming support.

**Why modify files on disk?** Simplest implementation for permanent degradation. Could be optimized later.

**Why 0.5-second segments?** Balance between granularity and file I/O overhead.

**Why JSON metadata?** Simple, human-readable, no database overhead for small scale.

**Why gunicorn?** Production-ready WSGI server, handles concurrent requests well.

## Known Issues / Limitations

- No authentication - anyone can degrade tracks
- No rate limiting - could be abused
- File I/O on every segment play (performance bottleneck at scale)
- No backup/restore mechanism
- Metadata files can get out of sync if audio files are replaced manually
- No support for stereo degradation (currently mixes to mono)

## Questions for Future Development

1. Should we add authentication? (API keys, OAuth, etc.)
2. Should degradation be reversible? (Keep original files as backups)
3. Should we support different degradation algorithms? (pitch shift, reverb, etc.)
4. Should we add a web admin interface?
5. Should we track listener analytics? (geographic, time-based, etc.)

---

**Last Updated:** 2024-11-09
**Status:** Production-ready, awaiting deployment
**Deployment Target:** Coolify on Hetzner VPS (CPX11, Falkenstein)
