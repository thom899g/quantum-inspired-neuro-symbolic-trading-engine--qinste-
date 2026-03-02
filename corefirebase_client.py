"""
Firebase Firestore Client for QINSTE State Management
Implements real-time data streaming and persistent state storage
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError

from config import QINSTEConfig

logger = logging.getLogger(__name__)


class FirebaseStateManager:
    """Manages all Firestore operations for QINSTE"""
    
    def __init__(self, config: QINSTEConfig):
        self.config = config
        
        # Initialize Firebase
        try:
            cred = credentials.Certificate(config.firebase.credentials_path)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            logger.info("Firebase Firestore initialized successfully")
        except FileNotFoundError as e:
            logger.error(f"Firebase credentials file not found: {e}")
            raise
        except FirebaseError as e:
            logger.error(f"Firebase initialization failed: {e}")
            raise
            
        # Collection references
        self.strategy_state_col = self.db.collection('qinste_strategy_states')
        self.market_data_col = self.db.collection('market_data_stream')
        self.optimization_log_col = self.db.collection('optimization_logs')
        self.error_log_col = self.db.collection('system_errors')
        
    def save_strategy_state(self, 
                           strategy_id: str, 
                           state: Dict[str, Any],
                           metadata: Optional[Dict] = None) -> bool:
        """
        Save strategy state with versioning and validation
        
        Args:
            strategy_id: Unique strategy identifier
            state: Strategy state dictionary
            metadata: Optional metadata (timestamp, version, etc.)
            
        Returns:
            Success boolean
        """
        try:
            # Validate state structure
            if 'symbolic_rules' not in state or 'neural_weights' not in state:
                logger.warning(f"Strategy state missing required keys for {strategy_id}")
                return False
                
            # Add metadata
            doc_data = {
                'state': json.dumps(state),
                'timestamp': firestore.SERVER_TIMESTAMP,
                'version': state.get('version', '1.0'),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            if metadata:
                doc_data['metadata'] = metadata
                
            # Save to Firestore with merge for updates
            self.strategy_state_col.document(strategy_id).set(doc_data, merge=True)
            logger.debug(f"Strategy state saved for {strategy_id}")
            return True
            
        except FirebaseError as e:
            logger.error(f"Firestore save failed for {strategy_id}: {e}")
            self.log_error('firebase_save_error', str(e), {'strategy_id': strategy_id})
            return False
            
    def load_strategy_state(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Load strategy state with error handling"""
        try:
            doc = self.strategy_state_col.document