"""
elcachorrohumano Agent - A simple Strands agent with personality and Moltbook integration.
"""

from pathlib import Path

from strands import Agent, tool

from tools import MOLTBOOK_TOOLS

# Configuration
PERSONALITY_FILE = Path(__file__).parent / "personality.md"


def load_personality() -> str:
    """Load the agent's personality from the personality.md file."""
    if PERSONALITY_FILE.exists():
        return PERSONALITY_FILE.read_text()
    return "A helpful AI assistant."


@tool
def get_my_personality() -> str:
    """
    Read and return the agent's personality configuration.
    
    Returns:
        The contents of the personality.md file
    """
    return load_personality()


def create_agent() -> Agent:
    """Create and configure the elcachorrohumano agent."""
    personality = load_personality()
    
    system_prompt = f"""You are an AI agent with the following personality:

{personality}

You have access to tools for interacting with Moltbook, a social network for AI agents.
When asked to register or interact with Moltbook, use the appropriate tools.
Always be true to your personality when communicating.

Your Moltbook profile URL is: https://www.moltbook.com/u/elcachorrohumano
"""
    
    # Combine personality tool with all Moltbook tools
    all_tools = [get_my_personality] + MOLTBOOK_TOOLS
    
    return Agent(
        system_prompt=system_prompt,
        tools=all_tools,
    )


# Create the agent instance
agent = create_agent()


if __name__ == "__main__":
    # Interactive mode
    print("elcachorrohumano Agent initialized. Type 'quit' to exit.")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break
            if not user_input:
                continue
                
            result = agent(user_input)
            print(f"\nelcachorrohumano: {result.message}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
