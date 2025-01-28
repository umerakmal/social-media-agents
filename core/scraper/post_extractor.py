import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict
from logger.logger import AgentLogger
import time

class PostExtractor:
    def __init__(self, driver, selectors):
        self.driver = driver
        self.selectors = selectors
        self.logger = AgentLogger("post_extractor")

    async def extract_post_data(self, post_element) -> Dict:
        """Extract data from a post element with better error handling"""
        try:
            return {
                'id': post_element.get_attribute('data-id') or f"post_{time.time()}",
                'url': await self._safely_get_post_url(post_element),
                'content': await self._safely_get_post_content(post_element),
                'author': await self._safely_get_post_author(post_element),
                'element': post_element,
                'comment_button': await self._safely_find_comment_button(post_element),
                'processed': False
            }
        except Exception as e:
            self.logger.warning(f"Error extracting post data: {str(e)}")
            return {'content': '', 'processed': False}

    async def _safely_get_post_content(self, post_element) -> str:
        """Safely extract post content with retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                content_elements = post_element.find_elements(By.CSS_SELECTOR, self.selectors['post_content'])
                
                if not content_elements:
                    content_elements = WebDriverWait(post_element, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.selectors['post_content']))
                    )
                
                texts = []
                for elem in content_elements:
                    try:
                        text = elem.text.strip()
                        if not text:
                            text = self.driver.execute_script("return arguments[0].textContent", elem).strip()
                        if text:
                            texts.append(text)
                    except Exception as e:
                        self.logger.debug(f"Failed to get text from element: {str(e)}")
                        continue
                
                return ' '.join(texts) if texts else ''
                
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.warning(f"Failed to get post content: {str(e)}")
                    return ''
                await asyncio.sleep(1)

    async def _safely_get_post_author(self, post_element) -> Dict:
        """Safely extract author information with retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                author_name = ''
                profile_url = ''
                
                author_selectors = self.selectors['post_author'].split(',')
                for selector in author_selectors:
                    try:
                        author_element = post_element.find_element(By.CSS_SELECTOR, selector.strip())
                        author_name = author_element.text.strip()
                        if author_name:
                            break
                    except:
                        continue
                
                link_selectors = self.selectors['author_link'].split(',')
                for selector in link_selectors:
                    try:
                        link_element = post_element.find_element(By.CSS_SELECTOR, selector.strip())
                        profile_url = link_element.get_attribute('href')
                        if profile_url:
                            break
                    except:
                        continue
                
                return {
                    'name': author_name or 'Unknown',
                    'profile_url': profile_url or ''
                }
                
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.warning(f"Failed to get author info: {str(e)}")
                    return {'name': 'Unknown', 'profile_url': ''}
                await asyncio.sleep(1)

    async def _safely_get_post_url(self, post_element) -> str:
        """Safely extract post URL with retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = ''
                
                try:
                    url = post_element.get_attribute('data-permalink') or ''
                except:
                    pass
                
                if not url:
                    link_selectors = self.selectors['author_link'].split(',')
                    for selector in link_selectors:
                        try:
                            link_element = post_element.find_element(By.CSS_SELECTOR, selector.strip())
                            url = link_element.get_attribute('href')
                            if url:
                                break
                        except:
                            continue
                
                return url or ''
                
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.warning(f"Failed to get post URL: {str(e)}")
                    return ''
                await asyncio.sleep(1)

    async def _safely_find_comment_button(self, post_element):
        """Safely find comment button with retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return WebDriverWait(post_element, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['comment_button']))
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.warning(f"Failed to find comment button: {str(e)}")
                    return None
                await asyncio.sleep(1) 