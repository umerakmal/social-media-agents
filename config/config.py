from typing import Dict, Optional
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from logger.logger import AgentLogger
from logger.exceptions import InvalidConfigurationError

# Initialize logger
logger = AgentLogger("config")

# Load environment variables from .env file
try:
    logger.debug("Loading environment variables from .env file")
    load_dotenv()
    logger.info("Environment variables loaded successfully")
except Exception as e:
    logger.error(f"Failed to load .env file: {str(e)}")
    raise InvalidConfigurationError(f"Error loading .env file: {str(e)}")

@dataclass
class PlatformCredentials:
    username: str
    password: str

@dataclass
class PlatformSettings:
    posts_per_session: int
    engagement_delay: int

@dataclass
class PlatformConfig:
    credentials: PlatformCredentials
    settings: PlatformSettings

@dataclass
class AISettings:
    gemini_api_key: str
    temperature: float
    max_tokens: int

@dataclass
class BrowserSettings:
    headless: bool
    timeout: int

class Config:
    def __init__(self):
        logger.debug("Initializing configuration")
        try:
            # Initialize platforms configuration
            logger.debug("Setting up platform configurations")
            self.platforms = {
                'linkedin': self._setup_linkedin_config(),
                'facebook': self._setup_facebook_config(),
                'instagram': self._setup_instagram_config()
            }
            logger.info("Platform configurations initialized successfully")

            # Initialize AI settings
            logger.debug("Setting up AI configuration")
            self.ai_settings = self._setup_ai_config()
            logger.info("AI configuration initialized successfully")

            # Initialize browser settings
            logger.debug("Setting up browser configuration")
            self.browser_settings = self._setup_browser_config()
            logger.info("Browser configuration initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize configuration: {str(e)}")
            raise InvalidConfigurationError(f"Configuration initialization failed: {str(e)}")

    def _setup_linkedin_config(self) -> PlatformConfig:
        """Setup LinkedIn-specific configuration"""
        try:
            logger.debug("Setting up LinkedIn configuration")
            username = os.getenv('LINKEDIN_USERNAME')
            password = os.getenv('LINKEDIN_PASSWORD')
            
            if not username or not password:
                logger.warning("LinkedIn credentials not found in environment variables")
            
            return PlatformConfig(
                credentials=PlatformCredentials(
                    username=username,
                    password=password
                ),
                settings=PlatformSettings(
                    posts_per_session=int(os.getenv('LINKEDIN_POSTS_PER_SESSION', 10)),
                    engagement_delay=int(os.getenv('LINKEDIN_ENGAGEMENT_DELAY', 30))
                )
            )
        except Exception as e:
            logger.error(f"Error setting up LinkedIn configuration: {str(e)}")
            return None

    def _setup_facebook_config(self) -> PlatformConfig:
        """Setup Facebook-specific configuration"""
        try:
            logger.debug("Setting up Facebook configuration")
            username = os.getenv('FACEBOOK_USERNAME')
            password = os.getenv('FACEBOOK_PASSWORD')
            
            if not username or not password:
                logger.warning("Facebook credentials not found in environment variables")
            
            return PlatformConfig(
                credentials=PlatformCredentials(
                    username=username,
                    password=password
                ),
                settings=PlatformSettings(
                    posts_per_session=int(os.getenv('FACEBOOK_POSTS_PER_SESSION', 8)),
                    engagement_delay=int(os.getenv('FACEBOOK_ENGAGEMENT_DELAY', 45))
                )
            )
        except Exception as e:
            logger.error(f"Error setting up Facebook configuration: {str(e)}")
            return None

    def _setup_instagram_config(self) -> PlatformConfig:
        """Setup Instagram-specific configuration"""
        try:
            logger.debug("Setting up Instagram configuration")
            username = os.getenv('INSTAGRAM_USERNAME')
            password = os.getenv('INSTAGRAM_PASSWORD')
            
            if not username or not password:
                logger.warning("Instagram credentials not found in environment variables")
            
            return PlatformConfig(
                credentials=PlatformCredentials(
                    username=username,
                    password=password
                ),
                settings=PlatformSettings(
                    posts_per_session=int(os.getenv('INSTAGRAM_POSTS_PER_SESSION', 5)),
                    engagement_delay=int(os.getenv('INSTAGRAM_ENGAGEMENT_DELAY', 60))
                )
            )
        except Exception as e:
            logger.error(f"Error setting up Instagram configuration: {str(e)}")
            return None

    def _setup_ai_config(self) -> AISettings:
        """Setup AI-specific configuration"""
        try:
            logger.debug("Setting up AI configuration")
            api_key = os.getenv('GEMINI_API_KEY')
            
            if not api_key:
                logger.error("Gemini API key not found in environment variables")
                raise InvalidConfigurationError("Gemini API key is required")
            
            return AISettings(
                gemini_api_key=api_key,
                temperature=float(os.getenv('AI_TEMPERATURE', 0.7)),
                max_tokens=int(os.getenv('AI_MAX_TOKENS', 150))
            )
        except Exception as e:
            logger.error(f"Error setting up AI configuration: {str(e)}")
            raise

    def _setup_browser_config(self) -> BrowserSettings:
        """Setup browser-specific configuration"""
        try:
            logger.debug("Setting up browser configuration")
            return BrowserSettings(
                headless=os.getenv('HEADLESS', 'False').lower() == 'true',
                timeout=int(os.getenv('BROWSER_TIMEOUT', 30))
            )
        except Exception as e:
            logger.error(f"Error setting up browser configuration: {str(e)}")
            raise InvalidConfigurationError(f"Browser configuration error: {str(e)}")

    def get_platform_config(self, platform: str) -> Optional[PlatformConfig]:
        """Get configuration for specific platform with error handling"""
        try:
            logger.debug(f"Retrieving configuration for platform: {platform}")
            config = self.platforms.get(platform)
            if config:
                logger.debug(f"Configuration found for {platform}")
                return config
            else:
                logger.warning(f"No configuration found for platform: {platform}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving configuration for {platform}: {str(e)}")
            return None

# Initialize global config instance
try:
    logger.debug("Initializing global config instance")
    config = Config()
    logger.info("Global config instance initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize global config: {str(e)}")
    raise