import asyncio
from typing import Dict, Type, List
from agents.base_agent import BaseAgent
from agents.linkedin_agent import LinkedInAgent
# from agents.facebook_agent import FacebookAgent
# from agents.instagram_agent import InstagramAgent
from config.config import Config
from logger.logger import AgentLogger
from logger.exceptions import (
    SocialMediaAgentException,
    PlatformNotSupportedError,
    InvalidConfigurationError
)

class AgentFactory:
    _agents: Dict[str, Type[BaseAgent]] = {
        'linkedin': LinkedInAgent,
        # 'facebook': FacebookAgent,
        # 'instagram': InstagramAgent
    }
    
    logger = AgentLogger("agent_factory")

    @classmethod
    def get_available_agents(cls) -> List[str]:
        """Get list of available social media platforms"""
        return list(cls._agents.keys())

    @classmethod
    def create_agent(cls, platform: str, config: Config) -> BaseAgent:
        """Create and return an agent instance for the specified platform"""
        try:
            cls.logger.info(f"Creating agent for platform: {platform}")
            
            if platform not in cls._agents:
                cls.logger.error(f"Unsupported platform requested: {platform}")
                raise PlatformNotSupportedError(f"Platform '{platform}' is not supported")
            
            cls.logger.debug(f"Initializing {platform} agent with config")
            agent = cls._agents[platform](config)
            cls.logger.info(f"Successfully created {platform} agent")
            return agent
            
        except Exception as e:
            cls.logger.error(f"Failed to create agent for {platform}: {str(e)}")
            raise

async def main():
    logger = AgentLogger("main")
    
    try:
        logger.info("Starting social media engagement bot")
        
        # Load configuration
        try:
            logger.debug("Loading configuration")
            config = Config()
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.critical(f"Failed to load configuration: {str(e)}")
            raise InvalidConfigurationError(f"Configuration error: {str(e)}")
        
        # Validate Gemini API key
        if not config.ai_settings.gemini_api_key:
            logger.critical("Gemini API key not found in configuration")
            raise InvalidConfigurationError("Gemini API key is required")
        
        # Get available agents
        available_agents = AgentFactory.get_available_agents()
        logger.info(f"Available social media agents: {', '.join(available_agents)}")
        
        # Filter out platforms with missing credentials
        active_agents = []
        for platform in available_agents:
            platform_config = config.get_platform_config(platform)
            if not platform_config:
                logger.warning(f"No configuration found for {platform}")
                continue
                
            if (platform_config.credentials.username and 
                platform_config.credentials.password):
                active_agents.append(platform)
                logger.info(f"Found valid credentials for {platform}")
                print(f"{len(active_agents)}. {platform.title()}")
            else:
                logger.warning(f"Skipping {platform} - missing credentials")

        if not active_agents:
            logger.critical("No platforms configured with valid credentials")
            raise InvalidConfigurationError("No platforms have valid credentials configured")

        # Get user choice
        selected_platform = None
        while True:
            try:
                choice = int(input("\nSelect an agent (enter number): ")) - 1
                if 0 <= choice < len(active_agents):
                    selected_platform = active_agents[choice]
                    logger.info(f"User selected platform: {selected_platform}")
                    break
                logger.warning(f"Invalid choice entered: {choice + 1}")
                print("Invalid choice. Please try again.")
            except ValueError:
                logger.warning("Invalid input received")
                print("Please enter a valid number.")
            except KeyboardInterrupt:
                logger.info("User cancelled platform selection")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during platform selection: {str(e)}")
                print("An error occurred. Please try again.")

        # Initialize and run selected agent
        try:
            logger.info(f"Initializing {selected_platform} agent")
            agent = AgentFactory.create_agent(selected_platform, config)
            
            # Configure browser settings
            logger.debug("Configuring browser settings")
            agent.scraper.headless = config.browser_settings.headless
            agent.scraper.timeout = config.browser_settings.timeout
            
            # Run the agent
            logger.info("Starting agent execution")
            await agent.run()
            logger.info("Agent completed successfully")
            
        except SocialMediaAgentException as e:
            logger.error(f"Agent execution failed: {str(e)}")
            print(f"Error: {str(e)}")
            raise
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\nOperation cancelled by user")
    except InvalidConfigurationError as e:
        logger.critical(f"Configuration error: {str(e)}")
        print(f"Configuration error: {str(e)}")
    except Exception as e:
        logger.critical(f"Critical error in main execution: {str(e)}")
        print(f"Fatal error: {str(e)}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
