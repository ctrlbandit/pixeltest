import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDataManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.profiles_collection = None
        self.blacklists_collection = None
        self.system_settings_collection = None
        self._cache = {
            'profiles': {},
            'blacklists': {'category': {}, 'channel': {}},
            'system_settings': {}
        }
        
    async def initialize(self):
        """Initialize MongoDB connection"""
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        database_name = os.getenv("MONGODB_DATABASE", "pixel_did_bot")
        
        try:
            self.client = AsyncIOMotorClient(mongodb_uri)
            # Test the connection
            await self.client.admin.command('ping')
            
            self.db = self.client[database_name]
            self.profiles_collection = self.db.user_profiles
            self.blacklists_collection = self.db.blacklists
            self.system_settings_collection = self.db.system_settings
            
            # Create indexes for better performance
            await self._create_indexes()
            
            # Load initial data into cache
            await self._load_cache()
            
            logger.info("MongoDB connection established successfully")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Fallback to in-memory storage if MongoDB is unavailable
            logger.warning("Falling back to in-memory storage")
            
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        if self.profiles_collection:
            await self.profiles_collection.create_index("user_id", unique=True)
        if self.blacklists_collection:
            await self.blacklists_collection.create_index([("type", 1), ("guild_id", 1)])
        if self.system_settings_collection:
            await self.system_settings_collection.create_index("guild_id", unique=True)
            
    async def _load_cache(self):
        """Load frequently accessed data into cache"""
        try:
            # Load user profiles
            if self.profiles_collection:
                async for profile in self.profiles_collection.find():
                    user_id = profile.get('user_id')
                    if user_id:
                        self._cache['profiles'][user_id] = profile
                        
            # Load blacklists
            if self.blacklists_collection:
                async for blacklist in self.blacklists_collection.find():
                    blacklist_type = blacklist.get('type')
                    guild_id = blacklist.get('guild_id')
                    if blacklist_type and guild_id:
                        if blacklist_type not in self._cache['blacklists']:
                            self._cache['blacklists'][blacklist_type] = {}
                        self._cache['blacklists'][blacklist_type][guild_id] = blacklist.get('data', {})
                        
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
    
    # User Profile Management
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile with system and alters data"""
        user_id = str(user_id)
        
        # Check cache first
        if user_id in self._cache['profiles']:
            return self._cache['profiles'][user_id]
            
        # Default profile structure optimized for DID/OSDD systems
        default_profile = {
            "user_id": user_id,
            "system": {
                "name": None,
                "description": None,
                "pronouns": None,
                "created_at": None,
                "front_history": [],
                "system_avatar": None,
                "system_banner": None,
                "privacy_settings": {
                    "show_front": True,
                    "show_member_count": True,
                    "allow_member_list": True
                }
            },
            "alters": {},
            "folders": {},
            "settings": {
                "default_proxy_mode": "webhook",
                "auto_delete_commands": True,
                "dm_proxy_enabled": False,
                "timezone": "UTC"
            }
        }
        
        if self.profiles_collection:
            try:
                profile = await self.profiles_collection.find_one({"user_id": user_id})
                if profile:
                    # Remove MongoDB _id field
                    profile.pop('_id', None)
                    self._cache['profiles'][user_id] = profile
                    return profile
            except Exception as e:
                logger.error(f"Error fetching profile for {user_id}: {e}")
        
        # Cache and return default profile
        self._cache['profiles'][user_id] = default_profile
        return default_profile
    
    async def save_user_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """Save user profile to database"""
        user_id = str(user_id)
        profile["user_id"] = user_id
        
        try:
            # Update cache
            self._cache['profiles'][user_id] = profile
            
            if self.profiles_collection:
                await self.profiles_collection.replace_one(
                    {"user_id": user_id},
                    profile,
                    upsert=True
                )
            return True
        except Exception as e:
            logger.error(f"Error saving profile for {user_id}: {e}")
            return False
    
    # Alter Management (DID/OSDD specific)
    async def create_alter(self, user_id: str, alter_name: str, alter_data: Dict[str, Any]) -> bool:
        """Create a new alter for a system"""
        profile = await self.get_user_profile(user_id)
        
        if alter_name in profile.get("alters", {}):
            return False  # Alter already exists
            
        # Default alter structure optimized for DID/OSDD
        default_alter = {
            "displayname": alter_name,
            "pronouns": "Not set",
            "description": "No description provided",
            "avatar": None,
            "proxy_avatar": None,
            "banner": None,
            "proxy": None,
            "aliases": [],
            "color": 0x8A2BE2,
            "use_embed": True,
            "created_at": None,
            "role": None,  # System role (protector, persecutor, etc.)
            "age": None,
            "birthday": None,
            "front_time": 0,  # Total time fronting in minutes
            "last_front": None,
            "privacy": {
                "show_in_list": True,
                "allow_proxy": True
            }
        }
        
        # Merge with provided data
        default_alter.update(alter_data)
        profile["alters"][alter_name] = default_alter
        
        return await self.save_user_profile(user_id, profile)
    
    # Blacklist Management
    async def get_blacklist(self, blacklist_type: str, guild_id: str = None) -> Dict[str, Any]:
        """Get blacklist data (channel or category)"""
        if blacklist_type in self._cache['blacklists']:
            if guild_id:
                return self._cache['blacklists'][blacklist_type].get(guild_id, {})
            return self._cache['blacklists'][blacklist_type]
    return {}
    
    async def save_blacklist(self, blacklist_type: str, guild_id: str, data: Dict[str, Any]) -> bool:
        """Save blacklist data"""
        try:
            # Update cache
            if blacklist_type not in self._cache['blacklists']:
                self._cache['blacklists'][blacklist_type] = {}
            self._cache['blacklists'][blacklist_type][guild_id] = data
            
            if self.blacklists_collection:
                await self.blacklists_collection.replace_one(
                    {"type": blacklist_type, "guild_id": guild_id},
                    {"type": blacklist_type, "guild_id": guild_id, "data": data},
                    upsert=True
                )
            return True
        except Exception as e:
            logger.error(f"Error saving {blacklist_type} blacklist for guild {guild_id}: {e}")
            return False
    
    async def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

# Initialize the data manager
data_manager = MongoDataManager()

# Backwards compatibility functions for existing code
async def get_global_profiles():
    """Get all user profiles (backwards compatibility)"""
    return data_manager._cache['profiles']

def save_profiles(profiles):
    """Save profiles (backwards compatibility) - now async"""
    async def _save():
        for user_id, profile in profiles.items():
            await data_manager.save_user_profile(user_id, profile)
    
    # Create a new event loop if one doesn't exist
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # If loop is running, create a task
        asyncio.create_task(_save())
    else:
        # If loop is not running, run until complete
        loop.run_until_complete(_save())

def load_category_blacklist():
    """Load category blacklist (backwards compatibility)"""
    return data_manager._cache['blacklists'].get('category', {})

def save_category_blacklist(blacklist):
    """Save category blacklist (backwards compatibility)"""
    # This will need to be updated in the calling code to be async
    pass

def load_blacklist():
    """Load channel blacklist (backwards compatibility)"""
    return data_manager._cache['blacklists'].get('channel', {})

def save_blacklist(blacklist):
    """Save channel blacklist (backwards compatibility)"""
    # This will need to be updated in the calling code to be async
    pass

# Legacy global variables for backwards compatibility
global_profiles = {}
category_blacklist = {}
channel_blacklist = {}
