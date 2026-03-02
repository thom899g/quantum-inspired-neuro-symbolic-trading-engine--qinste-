"""
QINSTE Configuration Module
Centralized configuration management with validation
"""
import os
from dataclasses import dataclass
from typing import Optional
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    credentials_path: str
    
    def __post_init__(self):
        if not os.path.exists(self.credentials_path):
            logger.error(f"Firebase credentials not found at {self.credentials_path}")
            raise FileNotFoundError(f"Firebase credentials required at {self.credentials_path}")
            
        if not self.credentials_path.endswith('.json'):
            logger.warning("Firebase credentials should be a JSON file")


@dataclass
class TradingConfig:
    """Trading configuration with safety limits"""
    max_position_size: float
    risk_free_rate: float
    max_drawdown: float
    
    def __post_init__(self):
        if self.max_position_size > 0.5:
            logger.warning("Max position size exceeds recommended 50% limit")
        if self.max_drawdown > 0.3:
            logger.critical("Max drawdown exceeds 30% - system shutdown recommended")


class QINSTEConfig:
    """Main configuration orchestrator"""
    
    def __init__(self):
        self.firebase = FirebaseConfig(
            credentials_path=os.getenv('FIREBASE_CREDENTIALS_PATH', './config/firebase-credentials.json')
        )
        self.trading = TradingConfig(
            max_position_size=float(os.getenv('MAX_POSITION_SIZE', 0.1)),
            risk_free_rate=float(os.getenv('RISK_FREE_RATE', 0.02)),
            max_drawdown=float(os.getenv('MAX_DRAWDOWN', 0.15))
        )
        self.exchange_api_key = os.getenv('EXCHANGE_API_KEY')
        self.exchange_api_secret = os.getenv('EXCHANGE_API_SECRET')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
    def validate(self) -> bool:
        """Validate all configurations"""
        try:
            self.firebase.__post_init__()
            self.trading.__post_init__()
            
            if self.exchange_api_key and not self.exchange_api_secret:
                logger.error("API key provided without secret")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False