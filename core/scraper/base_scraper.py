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
    async def get_posts(self, count: int = 30) -> List[Dict]:
        """Get posts one by one with smooth scrolling"""
        try:
            if not self._is_session_valid():
                self.logger.warning("Invalid session detected, attempting to recover")
                await self.login()
                await asyncio.sleep(10)  # Fixed 10 second delay after login
            
            self.logger.info(f"Starting to fetch {count} posts")
            posts = []
            processed_elements = set()
            
            # Initialize helpers
            post_extractor = PostExtractor(self.driver, self.selectors)
            scroll_manager = ScrollManager(self.driver)
            
            # Wait for initial feed load
            try:
                self.logger.debug("Waiting for feed to load")
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['post_container']))
                )
            except TimeoutException:
                raise ElementNotFoundError("Could not find any posts in feed")

            while len(posts) < count:
                # Find visible posts
                current_posts = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['post_container'])
                
                for post_element in current_posts:
                    if len(posts) >= count:
                        break
                        
                    try:
                        element_id = post_element.id
                        if element_id in processed_elements:
                            continue
                            
                        # Scroll post into view smoothly
                        self.logger.debug("Scrolling to next post")
                        await scroll_manager.scroll_element_into_view(post_element)
                        await asyncio.sleep(1)  # Wait for scroll to complete
                        
                        # Extract post data
                        self.logger.debug("Extracting post data")
                        post_data = await post_extractor.extract_post_data(post_element)
                        
                        if post_data.get('content'):
                            posts.append(post_data)
                            processed_elements.add(element_id)
                            self.logger.info(f"Processed post {len(posts)}/{count}")
                            
                            # Here you would add your engagement logic
                            # await self.engage_with_post(post_data)
                            
                            await asyncio.sleep(2)  # Wait before moving to next post
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to process post: {str(e)}")
                        continue
                
                # If we haven't found enough posts, scroll to load more
                if len(posts) < count:
                    self.logger.debug("Scrolling to load more posts")
                    scroll_result = await scroll_manager.natural_scroll()
                    if not scroll_result['scrolled']:
                        self.logger.warning("Failed to scroll further")
                        break
                    await asyncio.sleep(2)  # Wait for new content to load
            
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

    async def get_next_post(self) -> Dict:
        """Get the next unprocessed post with smooth scrolling"""
        try:
            # Initialize helpers if not already done
            if not hasattr(self, 'post_extractor'):
                self.post_extractor = PostExtractor(self.driver, self.selectors)
            if not hasattr(self, 'scroll_manager'):
                self.scroll_manager = ScrollManager(self.driver)
            if not hasattr(self, 'processed_posts'):
                self.processed_posts = set()
            
            max_scroll_attempts = 5
            scroll_attempt = 0
            
            while scroll_attempt < max_scroll_attempts:
                # Find all current posts
                current_posts = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['post_container'])
                self.logger.debug(f"Found {len(current_posts)} posts in current view")
                
                # Try to process unprocessed posts
                for post_element in current_posts:
                    try:
                        if not post_element.is_displayed():
                            continue
                            
                        element_id = post_element.id
                        if element_id in self.processed_posts:
                            continue
                        
                        # Scroll post into view smoothly
                        self.logger.debug(f"Scrolling to post {element_id}")
                        self.driver.execute_script("""
                            arguments[0].scrollIntoView({
                                behavior: 'smooth',
                                block: 'center'
                            });
                        """, post_element)
                        await asyncio.sleep(2)
                        
                        # Extract post data
                        post_data = await self.post_extractor.extract_post_data(post_element)
                        
                        if post_data and post_data.get('content'):
                            self.processed_posts.add(element_id)
                            return post_data
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to process post: {str(e)}")
                        continue
                
                # If we haven't found a valid post, scroll to load more
                self.logger.info("Scrolling to load more posts")
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # Scroll down smoothly
                self.driver.execute_script("""
                    window.scrollTo({
                        top: window.pageYOffset + 800,
                        behavior: 'smooth'
                    });
                """)
                await asyncio.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempt += 1
                else:
                    scroll_attempt = 0  # Reset counter if we successfully loaded new content
                
                await asyncio.sleep(1)
            
            self.logger.warning("Could not find more posts after multiple scroll attempts")
            return None
            
        except Exception as e:
            self.logger.error(f"Error in get_next_post: {str(e)}")
            return None

    async def _get_post_content(self, post_element) -> str:
        """Extract post content with better selectors"""
        content_selectors = [
            'div.feed-shared-update-v2__description-wrapper',
            'div.feed-shared-text-view',
            'div.feed-shared-update-v2__commentary',
            'span.break-words',
            'div.update-components-text'  # Added new selector
        ]
        
        for selector in content_selectors:
            try:
                content_element = WebDriverWait(post_element, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if content_element and content_element.text.strip():
                    return content_element.text.strip()
            except:
                continue
        return ""

    async def _get_reaction_button(self, post_element):
        """Find reaction button with better selectors"""
        reaction_selectors = [
            'button.react-button',
            'button[aria-label="React to this post"]',
            'button.artdeco-button--muted.reaction-button',
            'button[data-control-name="react_button"]'  # Added new selector
        ]
        
        for selector in reaction_selectors:
            try:
                button = WebDriverWait(post_element, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if button.is_displayed():
                    return button
            except:
                continue
        return None
