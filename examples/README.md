# Frontend Integration Examples

This directory contains example HTML files demonstrating how to integrate the Ephemeral Audio Decay System into your website.

## Examples

### 1. Basic Player (`basic-player.html`)

A simple, minimal example using native HTML5 audio elements.

**Features:**
- Track list with degradation indicators
- Native browser audio controls
- Auto-refreshing degradation stats
- Minimal dependencies (no external libraries)

**Best for:**
- Quick prototyping
- Simple integrations
- Maximum browser compatibility

### 2. Howler.js Player (`howler-player.html`)

An enhanced player using Howler.js for better audio control.

**Features:**
- Custom playback controls
- Seek/scrub functionality
- Real-time progress tracking
- Visual degradation display
- Detailed statistics
- Modern dark UI

**Best for:**
- Production websites
- Enhanced user experience
- Custom player designs

## Usage

1. **Update the API URL:**

   In each example file, update the `API_BASE_URL` constant:
   ```javascript
   const API_BASE_URL = 'https://your-backend-url.com';
   ```

2. **Serve the files:**

   You can open these files directly in a browser for local testing, or serve them with a web server:
   ```bash
   python -m http.server 8000
   ```
   
   Then visit `http://localhost:8000/examples/basic-player.html`

3. **Ensure CORS is configured:**

   Make sure your backend has CORS enabled for your frontend domain. Set the `CORS_ORIGIN` environment variable:
   ```bash
   export CORS_ORIGIN=https://your-frontend-domain.com
   ```

## Embedding in Your Eleventy Site

### Simple Embed

Add to any Eleventy template:

```html
<div class="audio-player">
  <h2>Ephemeral Audio</h2>
  <audio controls>
    <source src="https://your-backend.com/stream/track.wav" type="audio/wav">
  </audio>
</div>
```

### Dynamic Track List

```html
<div id="track-list"></div>

<script>
  fetch('https://your-backend.com/tracks')
    .then(r => r.json())
    .then(tracks => {
      const html = tracks.map(track => `
        <div class="track">
          <h3>${track.title}</h3>
          <p>Degradation: ${track.overall_degradation.toFixed(1)}%</p>
          <audio controls>
            <source src="https://your-backend.com/stream/${track.filename}" type="audio/wav">
          </audio>
        </div>
      `).join('');
      document.getElementById('track-list').innerHTML = html;
    });
</script>
```

### With Degradation Visualization

```html
<div class="track-stats" id="stats"></div>

<script>
  async function updateStats(filename) {
    const response = await fetch(`https://your-backend.com/stats/${filename}`);
    const stats = await response.json();
    
    // Create visualization of segment degradation
    const canvas = document.createElement('canvas');
    canvas.width = stats.total_segments;
    canvas.height = 50;
    const ctx = canvas.getContext('2d');
    
    stats.segment_play_counts.forEach((count, i) => {
      const intensity = Math.min(count / 100, 1);
      ctx.fillStyle = `rgb(${255 * intensity}, ${100 * (1-intensity)}, ${100 * (1-intensity)})`;
      ctx.fillRect(i, 0, 1, 50);
    });
    
    document.getElementById('stats').appendChild(canvas);
  }
  
  updateStats('your-track.wav');
</script>
```

## Customization

### Styling

Both examples include inline CSS that you can easily customize to match your site's design.

### Functionality

You can extend the examples with:
- Volume controls
- Playback speed adjustment
- Download buttons (for current degraded state)
- Social sharing
- Playlist functionality
- Visualization of degradation patterns

## Browser Compatibility

- **Basic Player**: Works in all modern browsers with HTML5 audio support
- **Howler.js Player**: Requires modern browsers (Chrome, Firefox, Safari, Edge)

## Notes

- The audio degrades on the server side, so the degradation is permanent and shared across all listeners
- Each play increments the play count for the segments that were actually played
- Seeking to different parts of the track will degrade those specific segments
- The degradation is cumulative - each play adds to the existing degradation

## Support

For issues or questions, refer to the main README.md in the project root.
