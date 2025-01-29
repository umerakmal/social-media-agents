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
        """Run the agent workflow"""
        try:
            self.logger.info("Starting agent workflow")
            
            # Login and wait
            self.logger.info("Attempting login")
            await self.scraper.login()
            self.logger.info("Login successful, waiting 10 seconds...")
            await asyncio.sleep(10)
            
            posts_processed = 0
            max_posts = 30
            
            while posts_processed < max_posts:
                try:
                    self.logger.info(f"Processing post {posts_processed + 1}/{max_posts}")
                    
                    # Get next post with timeout
                    post = await asyncio.wait_for(
                        self.scraper.get_next_post(),
                        timeout=30  # 30 second timeout for getting post
                    )

                    self.logger.debug(f"Post content: {post}")
                    if not post:
                        self.logger.warning("No more posts found")
                        break
                    
                    # Generate AI response with timeout
                    self.logger.info("Generating AI response")
                    ai_response = await asyncio.wait_for(
                        self.ai_engine.generate_response(
                            post_content=post,
                            prompt_template=self.prompts.format_prompt(
                                'engagement',
                                post_content=post.get('content', ''),
                                author_name=post.get('author', {}).get('name', 'Unknown')
                            )
                        ),
                        timeout=30  # 30 second timeout for AI response
                    )
                    
                    self.logger.info(f"AI generated reaction: {ai_response['reaction']}")
                    
                    # Engage with post with timeout
                    self.logger.info("Engaging with post")
                    await asyncio.wait_for(
                        self.engagement_engine.engage(
                            platform=self.platform_name,
                            scraper=self.scraper,
                            post=post,
                            response=ai_response
                        ),
                        timeout=30  # 30 second timeout for engagement
                    )
                    
                    posts_processed += 1
                    await asyncio.sleep(2)  # Brief pause between posts
                    
                except asyncio.TimeoutError:
                    self.logger.error("Operation timed out, moving to next post")
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing post: {str(e)}")
                    continue
                    
            self.logger.info(f"Completed processing {posts_processed} posts")
            
        except Exception as e:
            self.logger.error(f"Error in agent workflow: {str(e)}")
            raise
        finally:
            try:
                if hasattr(self, 'scraper'):
                    await self.scraper.cleanup()
                    self.logger.info("Browser closed successfully")
            except Exception as e:
                self.logger.error(f"Error during cleanup: {str(e)}")
