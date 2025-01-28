from abc import ABC, abstractmethod
import asyncio
from typing import Dict
from core.scraper.base_scraper import BaseScraper
from core.ai_engine.gemini_engine import GeminiEngine
from core.engagement.engagement_engine import EngagementEngine
from prompts import get_platform_prompts
from logger.logger import AgentLogger, log_execution_time
from logger.exceptions import (
    SocialMediaAgentException,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    AIGenerationError,
    EngagementError
)
import time

class BaseAgent(ABC):
    def __init__(self, platform_name: str, config):
        self.platform_name = platform_name
        self.config = config
        self.logger = AgentLogger("base_agent")
        
        try:
            # Initialize prompts
            self.logger.debug("Loading platform prompts")
            self.prompts = self._load_prompts()
            
            # Initialize core components
            self.logger.debug("Initializing core components")
            self.scraper = self._initialize_scraper()
            self.ai_engine = GeminiEngine(config.ai_settings.gemini_api_key)
            self.engagement_engine = EngagementEngine()
            
            self.logger.info(f"Initialized {platform_name} agent")
        except Exception as e:
            self.logger.error(f"Failed to initialize {platform_name} agent: {str(e)}")
            raise

    def _load_prompts(self):
        """Load platform-specific prompts"""
        try:
            self.logger.debug(f"Loading prompts for {self.platform_name}")
            prompts = get_platform_prompts(self.platform_name)
            if not prompts:
                self.logger.error(f"No prompts found for {self.platform_name}")
                raise ValueError(f"No prompts found for {self.platform_name}")
            return prompts
        except Exception as e:
            self.logger.error(f"Failed to load prompts: {str(e)}")
            raise

    @abstractmethod
    def _initialize_scraper(self) -> BaseScraper:
        """Initialize platform-specific scraper"""
        pass

    @log_execution_time
    async def run(self):
        """Main agent workflow"""
        try:
            self.logger.info("Starting agent workflow")
            
            # Login
            try:
                self.logger.info("Attempting login")
                await self.scraper.login()
                self.logger.info("Login successful")
                time.sleep(20)
            except AuthenticationError as e:
                self.logger.error(f"Authentication failed: {str(e)}")
                raise
            
            # Fetch posts
            try:
                self.logger.info("Fetching posts")
                posts = await self.scraper.get_posts()
                self.logger.info(f"Found {len(posts)} posts")
            except NetworkError as e:
                self.logger.error(f"Network error fetching posts: {str(e)}")
                raise
            
            # Process posts
            for index, post in enumerate(posts, 1):
                try:
                    self.logger.info(f"Processing post {index}/{len(posts)}")
                    
                    # Generate AI response
                    try:
                        response = await self.ai_engine.generate_response(
                            post_content=post,
                            prompt_template=self.prompts.format_prompt(
                                'engagement',
                                post_content=post.get('content', ''),
                                author_name=post.get('author', {}).get('name', 'Unknown')
                            )
                        )
                    except Exception as e:
                        raise AIGenerationError(f"AI generation failed: {str(e)}")
                    
                    # Engage with post
                    try:
                        await self.engagement_engine.engage(
                            platform=self.platform_name,
                            scraper=self.scraper,
                            post=post,
                            response=response
                        )
                    except Exception as e:
                        raise EngagementError(f"Engagement failed: {str(e)}")
                    
                    self.logger.info(f"Successfully processed post {index}")
                    
                except RateLimitError as e:
                    self.logger.warning(f"Rate limit hit, waiting: {str(e)}")
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue
                except (AIGenerationError, EngagementError) as e:
                    self.logger.error(f"Error processing post {index}: {str(e)}")
                    continue
                    
        except SocialMediaAgentException as e:
            self.logger.critical(f"Critical error in agent workflow: {str(e)}")
            raise
