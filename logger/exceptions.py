class SocialMediaAgentException(Exception):
    """Base exception class for all social media agent exceptions"""
    def __init__(self, message: str = None, *args, **kwargs):
        super().__init__(message or self.__doc__, *args)

class AuthenticationError(SocialMediaAgentException):
    """Failed to authenticate with the social media platform"""

class ScrapingError(SocialMediaAgentException):
    """Error occurred during web scraping operations"""

class NetworkError(SocialMediaAgentException):
    """Network connection or request failed"""

class AIGenerationError(SocialMediaAgentException):
    """Error occurred during AI content generation"""

class EngagementError(SocialMediaAgentException):
    """Failed to perform engagement action (react/comment)"""

class RateLimitError(SocialMediaAgentException):
    """Platform rate limit exceeded"""

class ElementNotFoundError(ScrapingError):
    """Required HTML element not found on the page"""

class InvalidConfigurationError(SocialMediaAgentException):
    """Invalid or missing configuration settings"""

class PlatformNotSupportedError(SocialMediaAgentException):
    """Attempted to use an unsupported social media platform"""

class ContentValidationError(SocialMediaAgentException):
    """Content validation failed (length, format, etc.)"""

# Platform-specific exceptions
class LinkedInException(SocialMediaAgentException):
    """Base exception for LinkedIn-specific errors"""

class FacebookException(SocialMediaAgentException):
    """Base exception for Facebook-specific errors"""

class InstagramException(SocialMediaAgentException):
    """Base exception for Instagram-specific errors"""

# Usage example in a docstring:
"""
Example usage:

try:
    # Attempt login
    platform.login()
except AuthenticationError as e:
    logger.error(f"Authentication failed: {str(e)}")
except RateLimitError as e:
    logger.warning(f"Rate limit hit: {str(e)}")
    time.sleep(300)  # Wait 5 minutes
except NetworkError as e:
    logger.error(f"Network error: {str(e)}")
except SocialMediaAgentException as e:
    logger.error(f"General agent error: {str(e)}")
"""
