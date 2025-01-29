from dataclasses import dataclass
from typing import Dict

@dataclass
class LinkedInPrompts:
    engagement_prompt: str = """
    As a LinkedIn professional, analyze the following post:
    {post_content}
    
    Author: {author_name}
    
    First, determine the post type:
    1. If it contains job openings, hiring announcements, or recruitment -> HIRING
    2. If it's about someone starting a new job or role -> NEW_JOB
    3. If it's any other type of post -> GENERAL
    
    Then, generate:
    1. An appropriate reaction based on post type:
       - HIRING -> INSIGHTFUL
       - NEW_JOB -> CELEBRATE
       - GENERAL -> Choose from (LIKE, SUPPORT, LOVE, INSIGHTFUL) based on content
       
    2. A contextual comment:
       - For HIRING posts -> ONLY return "cfbr 🎯" or "following 🎯" (randomly choose one)
       - For NEW_JOB posts -> ONLY return "Congratulations 🎉 All the best in your new role"
       - For GENERAL posts -> A comment that:
         * Is between 50-80 characters
         * Is professional and adds value
         * Can include relevant emojis
         * Is a single line of text
         * Has no extra spaces
         * Is not promotional
         * Is not overly enthusiastic
    
    STRICT RULES:
    1. NEVER add any prefixes or labels
    2. NEVER add any markdown formatting
    3. NEVER add special characters (except emojis)
    4. NEVER add multiple lines or paragraphs
    5. For HIRING posts, ONLY return "cfbr 🎯" or "following 🎯"
    6. NEVER add extra context or explanations
    7. NEVER add hashtags
    8. NEVER add URLs or mentions
    9. NEVER add bullet points or numbering
    10. Return EXACTLY what should be posted - no additional text
    11. NEVER add "Comment:" or "Reaction:" prefixes
    12. NEVER add quotes or brackets
    13. NEVER add any text formatting
    14. Keep emojis relevant and professional
    15. Maximum 1-2 emojis per comment
    """

    post_analysis_prompt: str = """
    Analyze this LinkedIn post for:
    - Post type (HIRING, NEW_JOB, GENERAL)
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