import google.generativeai as genai
import asyncio
from logger.logger import AgentLogger
from logger.exceptions import AIGenerationError
from typing import Dict, Tuple

class GeminiEngine:
    def __init__(self, api_key: str):
        self.logger = AgentLogger("gemini_engine")
        try:
            # Configure Gemini
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.logger.info("Gemini AI engine initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini AI: {str(e)}")
            raise AIGenerationError(f"Gemini AI initialization failed: {str(e)}")

    async def generate_response(self, post_content: dict, prompt_template: str) -> Dict:
        """Generate a reaction and comment based on the post content"""
        try:
            self.logger.debug("Generating AI response")
            
            # Format the content for the prompt
            content = post_content.get('content', '')
            author = post_content.get('author', {}).get('name', 'Unknown')
            
            # Generate response using Gemini
            response = await self._generate_safely(prompt_template.format(
                post_content=content,
                author_name=author
            ))
            
            # Parse the response to extract reaction and comment
            reaction, comment = self._parse_response(response)
            
            self.logger.info("Successfully generated response")
            return {
                'reaction': reaction,
                'comment': comment,
                'raw_response': response
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate response: {str(e)}")
            raise AIGenerationError(f"Failed to generate response: {str(e)}")

    async def _generate_safely(self, prompt: str, max_retries: int = 3) -> str:
        """Generate response with retry mechanism"""
        for attempt in range(max_retries):
            try:
                # Run Gemini generation in a separate thread to not block
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.model.generate_content(prompt).text
                )
                return response
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.warning(f"Retry {attempt + 1}/{max_retries} after error: {str(e)}")
                await asyncio.sleep(1)

    def _parse_response(self, response: str) -> Tuple[str, str]:
        """Parse Gemini response to extract reaction and comment"""
        try:
            # Default values
            reaction = "LIKE"
            comment = ""
            
            # Split response into lines
            lines = response.strip().split('\n')
            
            # Look for reaction and comment
            for line in lines:
                line = line.strip()
                
                # Extract reaction
                if any(r in line.upper() for r in ["LIKE", "CELEBRATE", "SUPPORT", "FUNNY", "LOVE", "INSIGHTFUL"]):
                    for r in ["LIKE", "CELEBRATE", "SUPPORT", "FUNNY", "LOVE", "INSIGHTFUL"]:
                        if r in line.upper():
                            reaction = r
                            break
                
                # Extract comment
                elif len(line) > 10 and not line.startswith(('1.', '2.', '-', 'Generate:', 'Consider:')):
                    comment = line
            
            # If no comment found, use the longest line as comment
            if not comment:
                comment = max([l for l in lines if len(l) > 10], key=len, default="Great insights!")
            
            self.logger.debug(f"Parsed reaction: {reaction}, Comment length: {len(comment)}")
            return reaction, comment
            
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {str(e)}")
            return "LIKE", "Interesting perspective! Thanks for sharing."
