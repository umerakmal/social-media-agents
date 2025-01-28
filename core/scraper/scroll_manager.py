import asyncio
from logger.logger import AgentLogger

class ScrollManager:
    def __init__(self, driver):
        self.driver = driver
        self.logger = AgentLogger("scroll_manager")
        self.scroll_step = 500  # Increased from 300 to 500 pixels per step
        self.scroll_delay = 0.05  # Decreased from 0.1 to 0.05 seconds
        self.smooth_scroll_script = """
            const startY = window.pageYOffset;
            const stopY = Math.min(startY + arguments[0], document.body.scrollHeight);
            const distance = stopY - startY;
            const steps = 10;
            const stepSize = distance / steps;
            
            for(let i = 0; i <= steps; i++) {
                const y = startY + (stepSize * i);
                window.scrollTo({
                    top: y,
                    behavior: 'auto'
                });
            }
            return stopY >= document.body.scrollHeight;
        """

    async def smooth_scroll(self, target_scroll: int = None):
        """Perform smooth scrolling using JavaScript"""
        try:
            # Use JavaScript for smoother scrolling
            reached_bottom = self.driver.execute_script(
                self.smooth_scroll_script, 
                target_scroll or 1000
            )
            await asyncio.sleep(0.2)  # Small delay after scroll
            return reached_bottom

        except Exception as e:
            self.logger.error(f"Error during scroll: {str(e)}")
            return False

    def scroll_element_into_view(self, element, offset: str = 'center'):
        """Scroll element into view with specified offset"""
        try:
            self.driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    behavior: 'auto',
                    block: arguments[1],
                    inline: 'nearest'
                });
                """, 
                element,
                offset
            )
            return True
        except Exception as e:
            self.logger.error(f"Error scrolling element into view: {str(e)}")
            return False 