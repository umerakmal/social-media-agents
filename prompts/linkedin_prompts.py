from dataclasses import dataclass
from typing import Dict

@dataclass
class LinkedInPrompts:
    engagement_prompt: str = """
    As a LinkedIn professional, analyze the following post:
    {post_content}
    
    Author: {author_name}
    
    Generate:
    1. An appropriate reaction (LIKE, CELEBRATE, SUPPORT, FUNNY, LOVE, INSIGHTFUL)
    2. A thoughtful, professional comment that adds value to the discussion
    
    Consider:
    - Professional tone
    - Industry relevance
    - Network building
    - Thought leadership
    """

    post_analysis_prompt: str = """
    Analyze this LinkedIn post for:
    - Main topic
    - Industry relevance
    - Engagement potential
    - Key discussion points
    """

    def get_prompt(self, prompt_type: str) -> str:
        prompts = {
            'engagement': self.engagement_prompt,
            'analysis': self.post_analysis_prompt
        }
        return prompts.get(prompt_type, '')

    def format_prompt(self, prompt_type: str, **kwargs) -> str:
        prompt = self.get_prompt(prompt_type)
        return prompt.format(**kwargs)

linkedin_prompts = LinkedInPrompts() 