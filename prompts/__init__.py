from .linkedin_prompts import LinkedInPrompts

def get_platform_prompts(platform_name: str):
    """Get prompts for the specified platform"""
    if platform_name.lower() == 'linkedin':
        return LinkedInPrompts()
    # Add other platform conditions here as needed
    return None
