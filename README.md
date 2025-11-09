# Ephemeral Audio Decay System

A Flask server that streams WAV files while progressively degrading them through listener interaction. Each audio track deteriorates in real-time as it is played, with different sections degrading independently based on actual listening patterns.

## Features

- 🎵 Streams WAV audio files with real-time degradation
- 🔊 Segment-based degradation (0.5-second segments)
- 📊 Track play counts and degradation statistics
- 🔒 Concurrent access support with segment-level locking
- 🌐 CORS-enabled for embedding in web applications
- 📈 Progressive sample dropout (1% per play, up to 100%)

## Setup

### Prerequisites

- Python 3.9+
- `uv` package manager (recommended)

### Installation

1. **Install dependencies:**

   ```bash
   uv sync
   ```

2. **Configure environment:**

   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` to customize settings (optional).

3. **Generate requirements.txt (for deployment platforms):**

   Many deployment platforms still expect `requirements.txt`:
   ```bash
   uv pip compile pyproject.toml -o requirements.txt
   ```

4. **Add audio files:**

   Place WAV files in the `audio/` directory:
   ```bash
   cp your-track.wav audio/
   ```

   Metadata will be automatically created on first startup.

## Testing

### Automated Tests

Run the test suite to verify everything works:

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html
```

See `tests/README.md` for more details.

### Manual Testing

You can also test the API manually using curl:

1. **Create test audio files:**
   ```bash
   uv run python create_test_audio.py
   ```

2. **Start the server:**
   ```bash
   PORT=5001 uv run python app.py
   ```

3. **Test the endpoints:**

   ```bash
   # Health check
   curl http://localhost:5001/
   
   # List all tracks
   curl http://localhost:5001/tracks | python3 -m json.tool
   
   # Get detailed stats for a track
   curl http://localhost:5001/stats/test-track.wav | python3 -m json.tool
   
   # Stream a track (this will degrade it!)
   curl http://localhost:5001/stream/short-track.wav --output /tmp/test.wav
   
   # Check degradation after streaming
   curl http://localhost:5001/stats/short-track.wav | python3 -m json.tool
   
   # Stream from a specific position (only degrades from that point)
   curl "http://localhost:5001/stream/test-track.wav?start=5" --output /tmp/test-seek.wav
   
   # Verify only segments from 5s onward were degraded
   curl http://localhost:5001/stats/test-track.wav | python3 -m json.tool
   ```

4. **Test the waveform player:**
   
   Open your browser to `http://localhost:5001/player` to see the interactive waveform player in action.

## Running the Server

### Development

Using `uv`:
```bash
uv run python app.py
```

Or with virtual environment:
```bash
source .venv/bin/activate
python app.py
```

The server will start on `http://localhost:5001` (or the port specified in your `.env` file).

### Using the Waveform Player

Once the server is running, open your browser to:

```
http://localhost:5001/player
```

This will load the interactive waveform player with:
- Real-time waveform visualization
- Transport controls (play/pause, skip, rewind, fast-forward)
- Live degradation statistics
- Visual progress indicator

### Production

Set environment variables:
```bash
export FLASK_DEBUG=False
export PORT=5000
export CORS_ORIGIN=https://your-site.com
```

Run with a production WSGI server (e.g., Gunicorn):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### GET /tracks

List all available tracks with degradation stats.

**Response:**
```json
[
  {
    "filename": "track1.wav",
    "title": "track1",
    "duration": 180.5,
    "overall_degradation": 23.4,
    "total_streams": 12
  }
]
```

### GET /stream/<filename>

Stream audio file with real-time degradation.

**Query Parameters:**
- `start` (optional): Starting position in seconds (default: 0)

**Example:**
```
GET /stream/track1.wav?start=30
```

### GET /stats/<filename>

Get detailed degradation statistics for a track.

**Response:**
```json
{
  "filename": "track1.wav",
  "title": "track1",
  "duration": 180.5,
  "total_segments": 361,
  "segment_duration": 0.5,
  "segment_play_counts": [0, 1, 3, 5, ...],
  "overall_degradation": 23.4,
  "total_streams": 12
}
```

## Directory Structure

```
ephemeral-audio/
├── app.py                 # Flask application
├── degradation.py         # Sample dropout algorithm
├── wav_handler.py         # WAV file I/O operations
├── metadata.py            # Metadata management
├── lock_manager.py        # Segment locking
├── streaming.py           # Audio streaming service
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
├── audio/                 # WAV files (manually added)
└── metadata/              # Auto-generated metadata JSON files
```

## Configuration

Environment variables:

- `AUDIO_DIR`: Directory containing WAV files (default: `./audio`)
- `METADATA_DIR`: Directory for metadata files (default: `./metadata`)
- `SEGMENT_DURATION`: Segment duration in seconds (default: `0.5`)
- `DEGRADATION_RATE`: Percentage of dropout per play (default: `1.0` = 1% per play, fully degraded after 100 plays)
  - For faster testing, try `10.0` (10% per play, fully degraded after 10 plays)
  - For slower degradation, try `0.5` (0.5% per play, fully degraded after 200 plays)
- `CORS_ORIGIN`: Allowed CORS origin (default: `*`)
- `PORT`: Server port (default: `5000`)
- `FLASK_DEBUG`: Enable debug mode (default: `False`)

## Deployment

### Railway

1. Create a new project on [Railway](https://railway.app)
2. Connect your repository
3. Add environment variables in Railway dashboard
4. Railway will automatically detect and deploy the Flask app

### Render

1. Generate `requirements.txt`: `uv pip compile pyproject.toml -o requirements.txt`
2. Create a new Web Service on [Render](https://render.com)
3. Connect your repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
6. Add environment variables in Render dashboard

### Fly.io

1. Install Fly CLI: `brew install flyctl`
2. Login: `fly auth login`
3. Launch app: `fly launch`
4. Deploy: `fly deploy`

## How It Works

1. **Initialization**: On startup, the system scans the `audio/` directory and creates metadata for any new WAV files
2. **Streaming**: When a client requests a stream, the server reads audio in 0.5-second segments
3. **Degradation**: Each segment is degraded based on its play count (1% dropout per play)
4. **Persistence**: Degraded audio is written back to the file, making the degradation permanent
5. **Concurrency**: Segment-level locks prevent data corruption when multiple listeners access the same track

## Embedding in Your Site

Use a standard HTML5 audio element:

```html
<audio controls>
  <source src="https://your-server.com/stream/track1.wav" type="audio/wav">
</audio>
```

Or with JavaScript:

```javascript
// Fetch track list
fetch('https://your-server.com/tracks')
  .then(r => r.json())
  .then(tracks => {
    tracks.forEach(track => {
      console.log(`${track.filename}: ${track.overall_degradation}% degraded`);
    });
  });
```

## Notes

- WAV files are modified in-place as they degrade
- Backup pristine copies before deployment if you want to preserve originals
- Degradation is intentionally permanent and irreversible
- Each segment can be played up to 100 times before reaching 100% degradation
- The system supports concurrent listeners without data corruption

## License

MIT
