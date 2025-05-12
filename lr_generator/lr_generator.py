"""LR ID generator module."""
from datetime import datetime
from typing import Dict

class LRGenerator:
    def __init__(self, id_pattern: str, branch_code: str = ""):
        self.id_pattern = id_pattern
        self.branch_code = branch_code
        self._sequence = 0

    def generate_lr_id(self, record: Dict) -> str:
        """Generate a unique LR ID based on the pattern."""
        now = datetime.now()
        self._sequence += 1
        
        return self.id_pattern.format(
            branch_code=self.branch_code,
            YYMMDD=now.strftime("%y%m%d"),
            sequence=self._sequence
        )

    def reset_sequence(self):
        """Reset the sequence counter."""
        self._sequence = 0
