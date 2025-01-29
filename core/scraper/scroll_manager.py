import asyncio
import random
from logger.logger import AgentLogger

class ScrollManager:
    def __init__(self, driver):
        self.driver = driver
        self.logger = AgentLogger("scroll_manager")
        # Smooth scroll script with visual feedback
        self.natural_scroll_script = """
            function smoothScroll(distance, duration) {
                const startPos = window.pageYOffset;
                const startTime = performance.now();
                
                function easeInOutQuad(t) {
                    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
                }
                
                function animate(currentTime) {
                    const timeElapsed = currentTime - startTime;
                    const progress = Math.min(timeElapsed / duration, 1);
                    
                    const ease = easeInOutQuad(progress);
                    const currentPosition = startPos + (distance * ease);
                    
                    window.scrollTo(0, currentPosition);
                    
                    if (progress < 1) {
                        requestAnimationFrame(animate);
                    }
                }
                
                requestAnimationFrame(animate);
            }
            
            const scrollAmount = arguments[0];
            const duration = arguments[1];
            
            smoothScroll(scrollAmount, duration);
            
            // Return scroll metrics
            return {
                startPosition: window.pageYOffset,
                documentHeight: document.documentElement.scrollHeight,
                viewportHeight: window.innerHeight,
                reachedBottom: (window.innerHeight + window.pageYOffset) >= document.documentElement.scrollHeight
            };
        """

    async def natural_scroll(self, min_distance=300, max_distance=600):
        """Perform smooth scrolling with visual feedback"""
        try:
            scroll_distance = random.randint(min_distance, max_distance)
            start_position = self.driver.execute_script("return window.pageYOffset;")
            
            # Execute smooth scroll
            self.driver.execute_script("""
                const distance = arguments[0];
                const duration = 1000;  // 1 second duration
                const start = window.pageYOffset;
                
                function step(timestamp) {
                    if (!start) start = timestamp;
                    const progress = timestamp - start;
                    const percentage = Math.min(progress / duration, 1);
                    
                    // Easing function for smooth acceleration/deceleration
                    const easing = t => t<.5 ? 2*t*t : -1+(4-2*t)*t;
                    
                    window.scrollTo(0, start + (distance * easing(percentage)));
                    
                    if (progress < duration) {
                        window.requestAnimationFrame(step);
                    }
                }
                
                window.requestAnimationFrame(step);
            """, scroll_distance)
            
            # Wait for scroll animation to complete
            await asyncio.sleep(1.2)
            
            # Get final position
            end_position = self.driver.execute_script("return window.pageYOffset;")
            
            return {
                "scrolled": end_position - start_position,
                "reachedBottom": self.driver.execute_script(
                    "return (window.innerHeight + window.pageYOffset) >= document.documentElement.scrollHeight;"
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error during scroll: {str(e)}")
            return {"scrolled": 0, "reachedBottom": False}

    async def scroll_element_into_view(self, element, offset: str = 'center'):
        """Smooth scroll element into view with visual feedback"""
        try:
            # First check if element is already in view
            in_view = self.driver.execute_script("""
                const elem = arguments[0];
                const rect = elem.getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.left >= 0 &&
                    rect.bottom <= window.innerHeight &&
                    rect.right <= window.innerWidth
                );
            """, element)
            
            if not in_view:
                # Smooth scroll to element
                self.driver.execute_script("""
                    const element = arguments[0];
                    const offset = arguments[1];
                    
                    function smoothScroll() {
                        const elementRect = element.getBoundingClientRect();
                        const absoluteElementTop = elementRect.top + window.pageYOffset;
                        const middle = absoluteElementTop - (window.innerHeight / 2);
                        const startPosition = window.pageYOffset;
                        const distance = middle - startPosition;
                        
                        let start = null;
                        const duration = 1000;  // 1 second duration
                        
                        function step(timestamp) {
                            if (!start) start = timestamp;
                            const progress = timestamp - start;
                            const percentage = Math.min(progress / duration, 1);
                            
                            // Easing function
                            const easing = t => t<.5 ? 2*t*t : -1+(4-2*t)*t;
                            
                            window.scrollTo(0, startPosition + (distance * easing(percentage)));
                            
                            if (progress < duration) {
                                window.requestAnimationFrame(step);
                            }
                        }
                        
                        window.requestAnimationFrame(step);
                    }
                    
                    smoothScroll();
                """, element, offset)
                
                # Wait for scroll animation to complete
                await asyncio.sleep(1.2)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error scrolling element into view: {str(e)}")
            return False 