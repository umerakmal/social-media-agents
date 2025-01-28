import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict, List
from logger.exceptions import (
    AuthenticationError,
    ElementNotFoundError,
    NetworkError,
    RateLimitError,
    ScrapingError
)
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException
)
from logger.logger import AgentLogger, log_execution_time
from .post_extractor import PostExtractor
from .scroll_manager import ScrollManager
import random
import time

class BaseScraper:
    def __init__(self, platform: str, credentials: Dict, selectors: Dict):
        self.platform = platform
        self.credentials = credentials
        self.selectors = selectors
        self.driver = None
        self.logger = AgentLogger(f"{platform}_scraper")
        self.headless = False  # Default value
        self.timeout = 30      # Default value

    def initialize_driver(self):
        """Initialize webdriver with platform-specific options"""
        try:
            self.logger.debug("Setting up Chrome options")
            options = webdriver.ChromeOptions()
            if self.headless:
                self.logger.debug("Configuring headless mode")
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
            
            self.logger.info("Initializing Chrome driver")
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(self.timeout)
            self.logger.info("Chrome driver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize web driver: {str(e)}")
            raise ScrapingError(f"Driver initialization failed: {str(e)}")

    @log_execution_time
    async def login(self):
        """Generic login using platform-specific selectors"""
        try:
            self.logger.info("Starting login process")
            
            if not self.driver:
                self.logger.debug("Driver not initialized, initializing now")
                self.initialize_driver()
            
            self.logger.info(f"Navigating to {self.selectors['login_url']}")
            self.driver.get(self.selectors['login_url'])
            
            try:
                self.logger.debug("Waiting for login form elements")
                username_field = self.wait_for_element(self.selectors['username_field'])
                password_field = self.wait_for_element(self.selectors['password_field'])
                login_button = self.wait_for_element(self.selectors['login_button'])
            except TimeoutException as e:
                raise ElementNotFoundError(f"Login form elements not found: {str(e)}")

            self.logger.debug("Entering credentials")
            username_field.send_keys(self.credentials['username'])
            password_field.send_keys(self.credentials['password'])
            
            self.logger.debug("Submitting login form")
            login_button.click()

            # Check for login errors
            if self.check_for_rate_limit():
                raise RateLimitError("Login rate limit detected")
            
            if self.check_for_login_errors():
                raise AuthenticationError("Invalid credentials or login failed")
            
            self.logger.info("Login successful")
            
        except WebDriverException as e:
            self.logger.error(f"Browser/network error during login: {str(e)}")
            raise NetworkError(f"Browser/network error: {str(e)}")
        except Exception as e:
            if "rate limit" in str(e).lower():
                raise RateLimitError(str(e))
            self.logger.error(f"Login failed: {str(e)}")
            raise ScrapingError(f"Login failed: {str(e)}")

    def wait_for_element(self, selector: str, timeout: int = None):
        """Wait for element with better error handling"""
        try:
            timeout = timeout or self.timeout
            self.logger.debug(f"Waiting for element: {selector}")
            # Add wait for element to be both present AND visible
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector)) and
                EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
            )
            # Add a small delay after finding element
            time.sleep(1)
            return element
        except TimeoutException:
            self.logger.error(f"Element not found: {selector}")
            return None  # Return None instead of raising exception

    def check_for_rate_limit(self) -> bool:
        """Check if rate limit page is shown"""
        # Implement platform-specific rate limit detection
        return False

    def check_for_login_errors(self) -> bool:
        """Check if login was unsuccessful"""
        # Implement platform-specific login error detection
        return False

    @log_execution_time
    async def get_posts(self, count: int = 10) -> List[Dict]:
        """Get posts using platform-specific selectors"""
        try:
            if not self._is_session_valid():
                self.logger.warning("Invalid session detected, attempting to recover")
                await self.login()
                await asyncio.sleep(5)
            
            self.logger.info(f"Fetching {count} posts")
            posts = []
            
            # Initialize helpers
            post_extractor = PostExtractor(self.driver, self.selectors)
            scroll_manager = ScrollManager(self.driver)
            
            # Initial wait for feed
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['post_container']))
                )
                await asyncio.sleep(3)
            except TimeoutException:
                raise ElementNotFoundError("Could not find any posts in feed")
            
            # Scroll and collect posts
            max_scrolls = 10
            scroll_count = 0
            
            while len(posts) < count and scroll_count < max_scrolls:
                if not self._is_session_valid():
                    self.logger.warning("Session became invalid during scrolling, re-establishing...")
                    await self.login()
                    await asyncio.sleep(5)
                
                await asyncio.sleep(random.uniform(2, 5))
                
                try:
                    current_posts = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['post_container'])
                    self.logger.debug(f"Found {len(current_posts)} posts before scroll")
                    
                    for post_element in current_posts[len(posts):]:
                        try:
                            self.driver.execute_script(
                                "arguments[0].setAttribute('data-processed', 'true');", 
                                post_element
                            )
                            
                            scroll_manager.scroll_element_into_view(post_element)
                            await asyncio.sleep(1)
                            
                            post_data = await post_extractor.extract_post_data(post_element)
                            
                            if post_data.get('content'):
                                posts.append(post_data)
                                self.logger.debug(f"Added post {len(posts)}/{count}")
                                
                                if len(posts) >= count:
                                    return posts[:count]
                                    
                        except WebDriverException as e:
                            if "invalid session id" in str(e).lower():
                                raise
                            self.logger.warning(f"Failed to process post: {str(e)}")
                            continue
                    
                    reached_bottom = await scroll_manager.smooth_scroll()
                    if reached_bottom:
                        self.logger.debug("Reached end of feed")
                        break
                    
                    scroll_count += 1
                    
                except WebDriverException as e:
                    if "invalid session id" in str(e).lower():
                        continue
                    raise
            
            self.logger.info(f"Successfully fetched {len(posts)} posts")
            return posts[:count]
            
        except Exception as e:
            self.logger.error(f"Failed to fetch posts: {str(e)}")
            raise ScrapingError(f"Failed to fetch posts: {str(e)}")

    def _is_session_valid(self) -> bool:
        try:
            self.driver.find_element(By.TAG_NAME, 'body')
            return True
        except:
            return False
