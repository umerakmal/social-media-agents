from dataclasses import dataclass

@dataclass
class InstagramPrompts:
    engagement_prompt: str = """
    As an Instagram user, analyze the following post:
    {post_content}
    
    Author: {author_name}
    
    Generate:
    1. An appropriate reaction (LIKE, LOVE)
    2. An engaging comment that fits Instagram's style
    
    Consider:
    - Visual content context
    - Use of emojis
    - Hashtag relevance
    - Instagram culture
    """

    post_analysis_prompt: str = """
    Analyze this Instagram post for:
    - Visual elements
    - Caption style
    - Hashtag strategy
    - Engagement potential
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

instagram_prompts = InstagramPrompts() 