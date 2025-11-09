"""
Segment Lock Manager
Coordinates concurrent access to audio file segments.
"""

import threading
from typing import Dict, Tuple


class SegmentLockManager:
    """Manages locks for individual audio segments to prevent concurrent writes."""
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize segment lock manager.
        
        Args:
            timeout: Maximum time to wait for lock acquisition in seconds
        """
        self.timeout = timeout
        self._locks: Dict[Tuple[str, int], threading.Lock] = {}
        self._lock_creation_lock = threading.Lock()
    
    def _get_lock(self, filename: str, segment_index: int) -> threading.Lock:
        """
        Get or create a lock for a specific segment.
        
        Args:
            filename: Name of audio file
            segment_index: Index of segment
            
        Returns:
            Threading lock for the segment
        """
        key = (filename, segment_index)
        
        with self._lock_creation_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]
    
    def acquire_lock(self, filename: str, segment_index: int) -> bool:
        """
        Acquire exclusive lock for a specific segment.
        
        Args:
            filename: Name of audio file
            segment_index: Index of segment
            
        Returns:
            True if lock acquired, False on timeout
        """
        lock = self._get_lock(filename, segment_index)
        return lock.acquire(timeout=self.timeout)
    
    def release_lock(self, filename: str, segment_index: int):
        """
        Release lock for a specific segment.
        
        Args:
            filename: Name of audio file
            segment_index: Index of segment
        """
        lock = self._get_lock(filename, segment_index)
        try:
            lock.release()
        except RuntimeError:
            # Lock wasn't held by this thread, ignore
            pass
    
    def segment_lock(self, filename: str, segment_index: int):
        """
        Context manager for segment locking.
        
        Args:
            filename: Name of audio file
            segment_index: Index of segment
            
        Returns:
            SegmentLock context manager
        """
        return SegmentLock(self, filename, segment_index)


class SegmentLock:
    """Context manager for segment locking."""
    
    def __init__(self, manager: SegmentLockManager, filename: str, segment_index: int):
        """
        Initialize segment lock context manager.
        
        Args:
            manager: SegmentLockManager instance
            filename: Name of audio file
            segment_index: Index of segment
        """
        self.manager = manager
        self.filename = filename
        self.segment_index = segment_index
        self.acquired = False
    
    def __enter__(self):
        """Acquire lock when entering context."""
        self.acquired = self.manager.acquire_lock(self.filename, self.segment_index)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock when exiting context."""
        if self.acquired:
            self.manager.release_lock(self.filename, self.segment_index)
        return False
