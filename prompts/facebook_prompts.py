from dataclasses import dataclass

@dataclass
class FacebookPrompts:
    engagement_prompt: str = """
    As a Facebook user, analyze the following post:
    {post_content}
    
    Author: {author_name}
    
    Generate:
    1. An appropriate reaction (LIKE, LOVE, CARE, HAHA, WOW, SAD, ANGRY)
    2. A friendly and engaging comment that contributes to the conversation
    
    Consider:
    - Casual, friendly tone
    - Social context
    - Personal connection
    - Engagement potential
    """

    post_analysis_prompt: str = """
    Analyze this Facebook post for:
    - Content type (personal, shared, event, etc.)
    - Emotional tone
    - Social context
    - Engagement opportunities
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

facebook_prompts = FacebookPrompts() 