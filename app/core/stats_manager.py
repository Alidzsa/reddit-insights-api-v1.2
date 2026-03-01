import threading
from datetime import datetime
from collections import deque

class StatsManager:
    """
    In-memory stats manager for tracking scraper health and proxy performance.
    """
    def __init__(self, history_size=100):
        self.history_size = history_size
        self.stats = {
            "json_success": 0,
            "json_failure": 0,
            "browser_success": 0,
            "browser_failure": 0,
            "proxy_errors": 0,
            "reddit_blocks": 0
        }
        self.history = deque(maxlen=history_size)
        self.lock = threading.Lock()

    def record_event(self, event_type: str, success: bool, metadata: dict = None):
        with self.lock:
            key = f"{event_type}_{'success' if success else 'failure'}"
            if key in self.stats:
                self.stats[key] += 1
            
            if metadata and "error_type" in metadata:
                err_key = metadata["error_type"]
                if err_key in self.stats:
                    self.stats[err_key] += 1
            
            self.history.append({
                "timestamp": datetime.now(),
                "event": event_type,
                "success": success,
                "metadata": metadata
            })

    def get_summary(self):
        with self.lock:
            return {
                "totals": self.stats.copy(),
                "success_rate": self._calculate_success_rate(),
                "recent_history_count": len(self.history)
            }

    def _calculate_success_rate(self):
        total = self.stats["json_success"] + self.stats["json_failure"] + \
                self.stats["browser_success"] + self.stats["browser_failure"]
        if total == 0:
            return 100.0
        success = self.stats["json_success"] + self.stats["browser_success"]
        return round((success / total) * 100, 2)

stats_manager = StatsManager()
