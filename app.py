"""
Ephemeral Audio Decay System
A Flask server that streams WAV files while progressively degrading them through listener interaction.
"""

import os
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from metadata import MetadataManager
from lock_manager import SegmentLockManager
from streaming import AudioStreamingService
from streaming_readonly import stream_audio_readonly

# Initialize Flask application
app = Flask(__name__)

# Enable CORS for embedding in Eleventy site
cors_origin = os.environ.get('CORS_ORIGIN', '*')
CORS(app, origins=cors_origin)

# Configuration
app.config['AUDIO_DIR'] = os.environ.get('AUDIO_DIR', './audio')
app.config['METADATA_DIR'] = os.environ.get('METADATA_DIR', './metadata')
app.config['SEGMENT_DURATION'] = float(os.environ.get('SEGMENT_DURATION', '0.5'))
app.config['DEGRADATION_RATE'] = float(os.environ.get('DEGRADATION_RATE', '1.0'))

# Ensure directories exist
os.makedirs(app.config['AUDIO_DIR'], exist_ok=True)
os.makedirs(app.config['METADATA_DIR'], exist_ok=True)

# Initialize services
metadata_manager = MetadataManager(
    app.config['AUDIO_DIR'],
    app.config['METADATA_DIR'],
    app.config['SEGMENT_DURATION']
)

lock_manager = SegmentLockManager(timeout=5.0)

streaming_service = AudioStreamingService(
    app.config['AUDIO_DIR'],
    metadata_manager,
    lock_manager,
    app.config['SEGMENT_DURATION'],
    app.config['DEGRADATION_RATE']
)


def initialize_audio_system():
    """
    Initialize the audio system on startup.
    Scans audio directory and creates metadata for new files.
    """
    print("Initializing Ephemeral Audio Decay System...")
    print(f"Audio directory: {app.config['AUDIO_DIR']}")
    print(f"Metadata directory: {app.config['METADATA_DIR']}")
    
    try:
        # Scan audio directory and initialize metadata
        initialized = metadata_manager.scan_and_initialize()
        
        if initialized:
            print(f"Initialized metadata for {len(initialized)} new track(s):")
            for filename in initialized:
                print(f"  - {filename}")
        else:
            print("No new tracks to initialize")
        
        # Get all tracks
        tracks = metadata_manager.get_all_tracks()
        print(f"\nTotal tracks available: {len(tracks)}")
        
        for track in tracks:
            degradation = track.get('overall_degradation', 0)
            print(f"  - {track['filename']} ({degradation:.1f}% degraded)")
    
    except Exception as e:
        print(f"Error during initialization: {e}")
        print("System will continue, but some tracks may not be available")


# Run initialization when app starts
with app.app_context():
    initialize_audio_system()


@app.route('/')
def index():
    """Health check endpoint"""
    return {
        'status': 'running',
        'service': 'Ephemeral Audio Decay System',
        'audio_dir': app.config['AUDIO_DIR'],
        'metadata_dir': app.config['METADATA_DIR'],
        'degradation_rate': app.config['DEGRADATION_RATE']
    }


@app.route('/player')
def player():
    """Serve the Tone.js player"""
    from flask import send_file
    return send_file('examples/tone-player.html')


@app.route('/tracks')
def get_tracks():
    """
    Get list of all available tracks with degradation stats.
    
    Returns:
        JSON array of track metadata
    """
    try:
        tracks = metadata_manager.get_all_tracks()
        
        # Format response
        response = []
        for track in tracks:
            # Calculate degradation with current rate
            degradation = metadata_manager.get_overall_degradation(
                track['filename'],
                app.config['DEGRADATION_RATE']
            )
            response.append({
                'filename': track['filename'],
                'title': track['title'],
                'duration': track['duration'],
                'overall_degradation': degradation,
                'total_streams': track.get('total_streams', 0)
            })
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stream/<filename>')
def stream_audio(filename):
    """
    Stream audio file with range request support for seeking.
    
    Args:
        filename: Name of WAV file to stream
        
    Returns:
        Audio stream with range support
    """
    try:
        file_path = os.path.join(app.config['AUDIO_DIR'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Audio file not found'}), 404
        
        # Increment total streams (only on first request, not range requests)
        if 'Range' not in request.headers:
            metadata_manager.increment_total_streams(filename)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Handle range requests for seeking
        range_header = request.headers.get('Range')
        if range_header:
            # Parse range header (e.g., "bytes=0-1023")
            byte_range = range_header.replace('bytes=', '').split('-')
            start = int(byte_range[0]) if byte_range[0] else 0
            end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
            
            length = end - start + 1
            
            def generate():
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk
            
            return Response(
                generate(),
                206,  # Partial Content
                mimetype='audio/wav',
                headers={
                    'Content-Range': f'bytes {start}-{end}/{file_size}',
                    'Accept-Ranges': 'bytes',
                    'Content-Length': str(length),
                    'Cache-Control': 'no-cache'
                }
            )
        else:
            # Full file request
            def generate():
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk
            
            return Response(
                generate(),
                mimetype='audio/wav',
                headers={
                    'Content-Length': str(file_size),
                    'Accept-Ranges': 'bytes',
                    'Cache-Control': 'no-cache'
                }
            )
    
    except Exception as e:
        return jsonify({'error': f'Streaming error: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Streaming error: {str(e)}'}), 500


@app.route('/degrade/<filename>', methods=['POST'])
def degrade_segment(filename):
    """
    Degrade a specific segment of a track.
    
    Args:
        filename: Name of WAV file
        
    JSON Body:
        segment_index: Index of segment to degrade
        
    Returns:
        Success message
    """
    try:
        data = request.get_json()
        segment_index = data.get('segment_index')
        
        if segment_index is None:
            return jsonify({'error': 'segment_index required'}), 400
        
        # Get track metadata
        metadata = metadata_manager.get_track_metadata(filename)
        if metadata is None:
            return jsonify({'error': 'Track not found'}), 404
        
        # Validate segment index
        if segment_index < 0 or segment_index >= metadata['total_segments']:
            return jsonify({'error': 'Invalid segment index'}), 400
        
        # Degrade the segment
        file_path = os.path.join(app.config['AUDIO_DIR'], filename)
        
        with lock_manager.segment_lock(filename, segment_index) as lock:
            if lock.acquired:
                # Get current play count
                play_count = metadata['segment_play_counts'][segment_index]
                
                # Read segment
                import wav_handler
                audio_data, _ = wav_handler.read_segment(
                    file_path,
                    segment_index,
                    app.config['SEGMENT_DURATION']
                )
                
                # Apply degradation
                import degradation
                degraded_audio = degradation.apply_dropout(
                    audio_data,
                    play_count,
                    app.config['DEGRADATION_RATE']
                )
                
                # Write back
                wav_handler.write_segment(
                    file_path,
                    segment_index,
                    app.config['SEGMENT_DURATION'],
                    degraded_audio
                )
                
                # Increment play count
                metadata_manager.increment_segment_play_count(filename, segment_index)
                
                return jsonify({
                    'success': True,
                    'segment_index': segment_index,
                    'play_count': play_count + 1
                })
            else:
                return jsonify({'error': 'Could not acquire lock'}), 503
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stats/<filename>')
def get_stats(filename):
    """
    Get detailed degradation statistics for a track.
    
    Args:
        filename: Name of WAV file
        
    Returns:
        JSON with detailed segment play counts and degradation data
    """
    try:
        metadata = metadata_manager.get_track_metadata(filename)
        
        if metadata is None:
            return jsonify({'error': 'Track not found'}), 404
        
        # Calculate overall degradation with current rate
        overall_degradation = metadata_manager.get_overall_degradation(
            filename,
            app.config['DEGRADATION_RATE']
        )
        
        # Return detailed stats
        return jsonify({
            'filename': metadata['filename'],
            'title': metadata['title'],
            'duration': metadata['duration'],
            'total_segments': metadata['total_segments'],
            'segment_duration': metadata['segment_duration'],
            'segment_play_counts': metadata['segment_play_counts'],
            'overall_degradation': overall_degradation,
            'total_streams': metadata.get('total_streams', 0),
            'created_at': metadata.get('created_at')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
