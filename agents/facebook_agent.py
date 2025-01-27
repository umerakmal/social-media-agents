from typing import Dict
from .base_agent import BaseAgent
from core.scraper.base_scraper import BaseScraper
from core.scraper.selectors.facebook_selectors import FACEBOOK_SELECTORS  # Ensure you have this selectors file

class FacebookAgent(BaseAgent):
    def __init__(self, config: Dict):
        super().__init__('facebook', config)

    def _initialize_scraper(self) -> BaseScraper:
        return BaseScraper(
            platform='facebook',
            credentials=self.config['platforms']['facebook']['credentials'],
            selectors=FACEBOOK_SELECTORS
        )
