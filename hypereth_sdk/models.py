"""
Data models for HyperETH SDK
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class APIKey:
    """Represents an API key"""
    key: str
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True


@dataclass
class APIKeyResponse:
    """Response from API key operations"""
    success: bool
    message: str
    api_key: Optional[APIKey] = None
    api_keys: Optional[List[APIKey]] = None