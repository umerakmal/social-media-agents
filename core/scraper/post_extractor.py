import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict
from logger.logger import AgentLogger
import time
import json
import traceback

class PostExtractor:
    def __init__(self, driver, selectors):
        self.driver = driver
        self.selectors = selectors
        self.logger = AgentLogger("post_extractor")

    async def extract_post_data(self, post_element):
        """Extract all data from a post"""
        try:
            # Extract all data
            content = await self._get_post_content(post_element)
            author = await self._get_post_author(post_element)
            
            # Store post data
            post_data = {
                'element': post_element,
                'content': content,
                'author': author,
                'url': await self._get_post_url(post_element),
                'timestamp': await self._get_post_timestamp(post_element),
                'metadata': {
                    'post_id': post_element.get_attribute('data-urn'),
                    'is_sponsored': await self._is_sponsored_post(post_element),
                }
            }

            # Log complete post data (excluding WebElement)
            log_data = post_data.copy()
            log_data.pop('element')  # Remove WebElement as it's not JSON serializable
            self.logger.info("Extracted post data:")
            self.logger.info(json.dumps(log_data, indent=2))

            return post_data

        except Exception as e:
            self.logger.error(f"Failed to extract post data: {str(e)}")
            raise

    async def _get_post_content(self, post_element):
        """Extract post content"""
        try:
            # Try multiple selectors
            for selector in self.selectors['post_content'].split(','):
                try:
                    content_element = post_element.find_element(By.CSS_SELECTOR, selector.strip())
                    if content_element and content_element.text.strip():
                        return content_element.text.strip()
                except:
                    continue
            return ""
        except Exception as e:
            self.logger.warning(f"Could not extract post content: {str(e)}")
            return ""

    async def _get_post_author(self, post_element):
        """Extract post author information"""
        try:
            # First find the author container
            container_selectors = [
                'div.update-components-actor__container',
                'div.feed-shared-actor__container',
                'div.update-components-actor'
            ]
            
            author_container = None
            for selector in container_selectors:
                try:
                    author_container = post_element.find_element(By.CSS_SELECTOR, selector)
                    if author_container:
                        break
                except:
                    continue

            if not author_container:
                self.logger.warning("Could not find author container")
                return {'name': 'Unknown', 'profile_url': None, 'title': None}

            # Extract author name from the title span
            name_selectors = [
                'span.update-components-actor__title span[dir="ltr"]',
                'span.update-components-actor__name',
                'span.feed-shared-actor__name',
                'span.hoverable-link-text'
            ]
            
            author_name = None
            for selector in name_selectors:
                try:
                    name_element = author_container.find_element(By.CSS_SELECTOR, selector)
                    if name_element and name_element.text.strip():
                        author_name = name_element.text.strip()
                        break
                except:
                    continue

            # Extract profile URL from the meta link
            try:
                profile_link = author_container.find_element(By.CSS_SELECTOR, 
                    'a.update-components-actor__meta-link,' +
                    'a.feed-shared-actor__container-link')
                profile_url = profile_link.get_attribute('href')
            except:
                profile_url = None

            # Extract title/description
            try:
                title_element = author_container.find_element(By.CSS_SELECTOR,
                    'span.update-components-actor__description,' +
                    'span.feed-shared-actor__description')
                title = title_element.text.strip()
            except:
                title = None

            # Extract timestamp
            try:
                time_element = author_container.find_element(By.CSS_SELECTOR,
                    'span.update-components-actor__sub-description,' +
                    'span.feed-shared-actor__sub-description')
                timestamp = time_element.text.strip()
            except:
                timestamp = None

            author_data = {
                'name': author_name or 'Unknown',
                'profile_url': profile_url,
                'title': title,
                'timestamp': timestamp
            }

            self.logger.debug(f"Extracted author data: {json.dumps(author_data, ensure_ascii=False)}")
            return author_data

        except Exception as e:
            self.logger.warning(f"Could not extract author: {str(e)}\nTraceback: {traceback.format_exc()}")
            return {'name': 'Unknown', 'profile_url': None, 'title': None}

    async def _get_post_url(self, post_element):
        """Extract post URL"""
        try:
            url_element = post_element.find_element(By.CSS_SELECTOR, 
                'a.feed-shared-update-v2__permalink,'
                'a[data-control-name="update_permalink"]')
            return url_element.get_attribute('href')
        except:
            return None

    async def _get_post_timestamp(self, post_element):
        """Extract post timestamp"""
        try:
            time_element = post_element.find_element(By.CSS_SELECTOR, 
                'span.feed-shared-actor__sub-description,'
                'span.update-components-actor__sub-description')
            return time_element.text.strip()
        except:
            return None

    async def _is_sponsored_post(self, post_element):
        """Check if post is sponsored"""
        try:
            sponsored_element = post_element.find_element(By.CSS_SELECTOR, 
                'span.feed-shared-actor__sub-description:contains("Promoted")')
            return bool(sponsored_element)
        except:
            return False

    def _is_element_visible(self, element):
        """Check if element is visible"""
        try:
            return element.is_displayed() and element.is_enabled()
        except:
            return False

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

    async def _get_reaction_button(self, post_element):
        """Find reaction button"""
        try:
            # Try multiple selectors for reaction button
            button_selectors = [
                'button.reactions-react-button',
                'button[aria-label="React to this post"]',
                'button.artdeco-button--muted.reaction-button',
                'button.react-button',
                'span.reactions-react-button'
            ]
            
            for selector in button_selectors:
                try:
                    buttons = post_element.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.logger.debug(f"Found reaction button with selector: {selector}")
                            return button
                except:
                    continue

            self.logger.warning("Could not find reaction button")
            return None

        except Exception as e:
            self.logger.warning(f"Error finding reaction button: {str(e)}")
            return None 