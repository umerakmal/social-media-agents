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
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            self.logger.debug(f"Element found: {selector}")
            return element
        except TimeoutException:
            self.logger.error(f"Element not found: {selector}")
            raise ElementNotFoundError(
                f"Element '{selector}' not found after {timeout} seconds"
            )
        except Exception as e:
            self.logger.error(f"Error finding element '{selector}': {str(e)}")
            raise ScrapingError(f"Error finding element '{selector}': {str(e)}")

    def check_for_rate_limit(self) -> bool:
        """Check if rate limit page is shown"""
        # Implement platform-specific rate limit detection
        return False

    def check_for_login_errors(self) -> bool:
        """Check if login was unsuccessful"""
        # Implement platform-specific login error detection
        return False

    async def get_posts(self, count: int = 10) -> List[Dict]:
        """Get posts using platform-specific selectors"""
        try:
            self.logger.info(f"Fetching {count} posts")
            posts = []
            
            self.logger.debug("Waiting for post container")
            post_elements = self.wait_for_element(self.selectors['post_container'])
            
            self.logger.debug(f"Processing {len(post_elements[:count])} posts")
            for element in post_elements[:count]:
                try:
                    post_data = {
                        'id': self.extract_post_id(element),
                        'content': self.extract_post_content(element),
                        'author': self.extract_post_author(element)
                    }
                    posts.append(post_data)
                except Exception as e:
                    self.logger.warning(f"Failed to process post: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully fetched {len(posts)} posts")
            return posts
            
        except Exception as e:
            self.logger.error(f"Failed to fetch posts: {str(e)}")
            raise ScrapingError(f"Failed to fetch posts: {str(e)}")

    def extract_post_id(self, element) -> str:
        """Extract post ID using platform-specific selector"""
        try:
            return element.get_attribute(self.selectors['post_id_attribute'])
        except Exception as e:
            self.logger.error(f"Failed to extract post ID: {str(e)}")
            raise ScrapingError(f"Failed to extract post ID: {str(e)}")

    def extract_post_content(self, element) -> str:
        """Extract post content using platform-specific selector"""
        try:
            content_element = element.find_element(By.CSS_SELECTOR, self.selectors['post_content'])
            return content_element.text
        except Exception as e:
            self.logger.error(f"Failed to extract post content: {str(e)}")
            raise ScrapingError(f"Failed to extract post content: {str(e)}")

    def extract_post_author(self, element) -> Dict:
        """Extract post author using platform-specific selector"""
        try:
            author_element = element.find_element(By.CSS_SELECTOR, self.selectors['post_author'])
            return {
                'name': author_element.text,
                'profile_url': author_element.get_attribute('href')
            }
        except Exception as e:
            self.logger.error(f"Failed to extract post author: {str(e)}")
            raise ScrapingError(f"Failed to extract post author: {str(e)}")
