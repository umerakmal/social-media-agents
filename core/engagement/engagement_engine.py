import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from logger.logger import AgentLogger
from logger.exceptions import EngagementError
import traceback

class EngagementEngine:
    def __init__(self):
        self.logger = AgentLogger("engagement_engine")
        # Initialize any necessary components here
        pass

    async def engage(self, platform: str, scraper, post: dict, response: dict):
        """Engage with a post using the provided reaction and comment"""
        try:
            self.logger.debug(f"Starting engagement on {platform}")
            
            # Get the post element
            post_element = post.get('element')
            if not post_element:
                raise EngagementError("Post element not found")

            # Ensure post is in view
            scraper.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            """, post_element)
            await asyncio.sleep(2)

            # First handle the reaction
            await self._add_reaction(scraper, post_element, response['reaction'])
            await asyncio.sleep(2)

            # Then add the comment
            await self._add_comment(scraper, post_element, response['comment'])
            
            self.logger.info("Engagement completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to engage with post: {str(e)}")
            raise EngagementError(f"Failed to engage with post: {str(e)}")

    async def _add_reaction(self, scraper, post_element, reaction_type: str) -> bool:
        """Add reaction to post with improved handling"""
        try:
            # First find and hover over the main reaction button to show the menu
            reaction_button = await self._safely_find_element(
                post_element,
                By.CSS_SELECTOR,
                scraper.selectors['reaction_button']
            )
            
            if not reaction_button:
                self.logger.warning("Could not find main reaction button")
                return False
            
            # Hover over the button to show reaction menu
            actions = ActionChains(scraper.driver)
            actions.move_to_element(reaction_button).perform()
            await asyncio.sleep(1)  # Wait for menu to appear
            
            # Try to find the specific reaction button
            try:
                specific_reaction = WebDriverWait(post_element, 5).until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        scraper.selectors['reactions'][reaction_type]
                    ))
                )
                specific_reaction.click()
                self.logger.info(f"Successfully added {reaction_type} reaction")
                return True
            
            except TimeoutException:
                # If specific reaction not found, try regular like
                self.logger.warning(f"Could not find {reaction_type} button, falling back to Like")
                reaction_button.click()
                await asyncio.sleep(1)
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to add reaction: {str(e)}\nTraceback: {traceback.format_exc()}")
            return False

    async def _safely_find_element(self, parent, by, selector, timeout=5):
        """Safely find element with retry logic"""
        try:
            return WebDriverWait(parent, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except:
            return None

    async def _add_comment(self, scraper, post_element, comment_text: str):
        """Add comment to the post"""
        try:
            self.logger.debug("Adding comment")
            
            # Ensure post is in view
            scraper.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            """, post_element)
            await asyncio.sleep(2)
            
            # Find and click comment button
            comment_button = WebDriverWait(post_element, 5).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    'button.artdeco-button.comment-button[aria-label="Comment"]'
                ))
            )
            
            try:
                comment_button.click()
            except:
                scraper.driver.execute_script("arguments[0].click();", comment_button)
            
            await asyncio.sleep(2)
            
            # Find comment field using the exact DOM structure
            comment_field = WebDriverWait(scraper.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    'div.ql-editor[data-gramm="false"][contenteditable="true"][data-placeholder="Add a comment…"]'
                ))
            )
            
            if not comment_field:
                raise Exception("Could not find comment field")

            self.logger.debug("Found comment field, entering text...")
            
            # Clear and enter comment text
            comment_field.clear()
            actions = ActionChains(scraper.driver)
            actions.move_to_element(comment_field)
            actions.click()
            actions.send_keys(comment_text)
            actions.perform()
            
            await asyncio.sleep(2)
            
            # Find and click the submit button using the exact class
            submit_button = WebDriverWait(scraper.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 
                    'button.comments-comment-box__submit-button--cr.artdeco-button--primary'
                ))
            )
            
            if not submit_button:
                raise Exception("Could not find submit button")

            self.logger.debug("Found submit button, clicking...")
            
            # Ensure submit button is in view
            scraper.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            await asyncio.sleep(1)
            
            # Try different click methods
            try:
                submit_button.click()
            except:
                try:
                    scraper.driver.execute_script("arguments[0].click();", submit_button)
                except:
                    actions = ActionChains(scraper.driver)
                    actions.move_to_element(submit_button)
                    actions.click()
                    actions.perform()
            
            # Wait for comment to be posted
            await asyncio.sleep(3)
            
            # Verify comment was posted
            try:
                posted_comment = WebDriverWait(scraper.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, 
                        f"//div[contains(@class, 'comments-comment-item')]//span[contains(text(), '{comment_text}')]"
                    ))
                )
                if posted_comment:
                    self.logger.info("Successfully verified comment was posted")
                    await asyncio.sleep(2)  # Wait before moving on
            except:
                self.logger.warning("Could not verify if comment was posted")
            
            self.logger.info("Successfully added comment")
            
        except Exception as e:
            self.logger.error(f"Failed to add comment: {str(e)}\nTraceback: {traceback.format_exc()}")
            raise

    async def _verify_engagement(self, post_element):
        """Verify that engagement was successful"""
        try:
            # Verify reaction was added
            reaction_added = post_element.find_elements(By.CSS_SELECTOR, 
                'button.react-button--active,'
                'button.artdeco-button--active')
            
            # Verify comment was added
            comment_added = post_element.find_elements(By.CSS_SELECTOR, 
                'div.comments-comments-list__comment-item')
            
            return bool(reaction_added and comment_added)
            
        except Exception as e:
            self.logger.warning(f"Could not verify engagement: {str(e)}")
            return False
