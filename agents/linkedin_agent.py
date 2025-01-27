from typing import Dict
from .base_agent import BaseAgent
from core.scraper.base_scraper import BaseScraper
from core.scraper.selectors.linkedin_selectors import LINKEDIN_SELECTORS
from logger.logger import AgentLogger
from config.config import Config

class LinkedInAgent(BaseAgent):
    def __init__(self, config: Config):
        super().__init__('linkedin', config)
        self.logger = AgentLogger('linkedin_agent')

    def _initialize_scraper(self) -> BaseScraper:
        """Initialize LinkedIn-specific scraper with proper error handling"""
        try:
            self.logger.debug("Initializing LinkedIn scraper")
            
            # Get LinkedIn-specific configuration
            platform_config = self.config.get_platform_config('linkedin')
            if not platform_config:
                raise ValueError("LinkedIn configuration not found")

            scraper = BaseScraper(
                platform='linkedin',
                credentials={
                    'username': platform_config.credentials.username,
                    'password': platform_config.credentials.password
                },
                selectors=LINKEDIN_SELECTORS
            )
            self.logger.info("LinkedIn scraper initialized successfully")
            return scraper
        except Exception as e:
            self.logger.error(f"Failed to initialize LinkedIn scraper: {str(e)}")
            raise
