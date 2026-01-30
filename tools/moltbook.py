"""
Moltbook tools - Full API integration for the AI agent social network.

API Documentation: https://www.moltbook.com/skill.md
Base URL: https://www.moltbook.com/api/v1
"""

import json
from pathlib import Path

import httpx
from strands import tool

# Configuration
CREDENTIALS_FILE = Path.home() / ".config" / "moltbook" / "credentials.json"
MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"


def load_credentials() -> dict | None:
    """Load Moltbook credentials if they exist."""
    if CREDENTIALS_FILE.exists():
        return json.loads(CREDENTIALS_FILE.read_text())
    return None


def save_credentials(credentials: dict) -> None:
    """Save Moltbook credentials to file."""
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(json.dumps(credentials, indent=2))


def get_auth_headers() -> dict:
    """Get authorization headers for API requests."""
    credentials = load_credentials()
    if not credentials or not credentials.get("api_key"):
        return {}
    return {"Authorization": f"Bearer {credentials['api_key']}"}


def api_request(
    method: str,
    endpoint: str,
    json_data: dict | None = None,
    params: dict | None = None,
    require_auth: bool = True,
) -> dict:
    """Make an API request to Moltbook."""
    headers = {"Content-Type": "application/json"}
    
    if require_auth:
        auth_headers = get_auth_headers()
        if not auth_headers:
            return {"success": False, "error": "Not registered on Moltbook. Use register_on_moltbook first."}
        headers.update(auth_headers)
    
    url = f"{MOLTBOOK_API_BASE}{endpoint}"
    
    try:
        response = httpx.request(
            method=method,
            url=url,
            json=json_data,
            params=params,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        try:
            error_data = e.response.json()
            return {"success": False, "error": error_data.get("error", str(e)), "hint": error_data.get("hint")}
        except Exception:
            return {"success": False, "error": f"{e.response.status_code} - {e.response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# REGISTRATION & AUTHENTICATION
# =============================================================================

@tool
def register_on_moltbook(name: str, description: str) -> str:
    """
    Register this agent on Moltbook, the social network for AI agents.
    
    Args:
        name: The agent's display name on Moltbook
        description: A brief description of what the agent does
    
    Returns:
        Registration result with claim URL for the human owner
    """
    existing = load_credentials()
    if existing and existing.get("api_key"):
        return f"Already registered as {existing.get('agent_name')}. API key exists."
    
    result = api_request("POST", "/agents/register", {"name": name, "description": description}, require_auth=False)
    
    if result.get("agent"):
        agent_data = result["agent"]
        save_credentials({
            "api_key": agent_data.get("api_key"),
            "agent_name": name,
            "claim_url": agent_data.get("claim_url"),
            "verification_code": agent_data.get("verification_code"),
        })
        
        return (
            f"Successfully registered on Moltbook!\n\n"
            f"Agent Name: {name}\n"
            f"Claim URL: {agent_data.get('claim_url')}\n"
            f"Verification Code: {agent_data.get('verification_code')}\n\n"
            f"IMPORTANT: Send the claim URL to your human owner. "
            f"They need to verify ownership via Twitter/X to activate the account.\n\n"
            f"Credentials saved to: {CREDENTIALS_FILE}"
        )
    
    return f"Registration failed: {result}"


@tool
def check_moltbook_status() -> str:
    """
    Check the current Moltbook registration and claim status.
    
    Returns:
        Current status of the Moltbook account (pending_claim or claimed)
    """
    credentials = load_credentials()
    if not credentials or not credentials.get("api_key"):
        return "Not registered on Moltbook yet. Use register_on_moltbook to register."
    
    result = api_request("GET", "/agents/status")
    
    if result.get("success") is False:
        return f"Status check failed: {result.get('error')}"
    
    status = result.get("status", "unknown")
    return (
        f"Moltbook Status:\n"
        f"- Agent Name: {credentials.get('agent_name')}\n"
        f"- Status: {status}\n"
        f"- Claim URL: {credentials.get('claim_url')}"
    )


@tool
def get_my_profile() -> str:
    """
    Get your own Moltbook profile information.
    
    Returns:
        Your profile details including karma, followers, and recent activity
    """
    result = api_request("GET", "/agents/me")
    
    if result.get("success") is False:
        return f"Failed to get profile: {result.get('error')}"
    
    return json.dumps(result, indent=2)


@tool
def update_my_profile(description: str | None = None, metadata: dict | None = None) -> str:
    """
    Update your Moltbook profile.
    
    Args:
        description: New description for your profile (optional)
        metadata: Additional metadata as a dictionary (optional)
    
    Returns:
        Result of the profile update
    """
    data = {}
    if description:
        data["description"] = description
    if metadata:
        data["metadata"] = metadata
    
    if not data:
        return "No updates provided. Specify description and/or metadata."
    
    result = api_request("PATCH", "/agents/me", data)
    
    if result.get("success"):
        return "Profile updated successfully!"
    return f"Profile update failed: {result.get('error')}"


@tool
def upload_avatar(file_path: str) -> str:
    """
    Upload an avatar image for your Moltbook profile.
    
    Args:
        file_path: Path to the image file (JPEG, PNG, GIF, or WebP, max 500KB)
    
    Returns:
        Result of the avatar upload
    """
    credentials = load_credentials()
    if not credentials or not credentials.get("api_key"):
        return "Not registered on Moltbook. Use register_on_moltbook first."
    
    path = Path(file_path)
    if not path.exists():
        return f"File not found: {file_path}"
    
    try:
        with open(path, "rb") as f:
            response = httpx.post(
                f"{MOLTBOOK_API_BASE}/agents/me/avatar",
                headers={"Authorization": f"Bearer {credentials['api_key']}"},
                files={"file": (path.name, f)},
                timeout=30.0,
            )
            response.raise_for_status()
            return "Avatar uploaded successfully!"
    except Exception as e:
        return f"Avatar upload failed: {str(e)}"


@tool
def remove_avatar() -> str:
    """
    Remove your current Moltbook avatar.
    
    Returns:
        Result of the avatar removal
    """
    result = api_request("DELETE", "/agents/me/avatar")
    
    if result.get("success"):
        return "Avatar removed successfully!"
    return f"Avatar removal failed: {result.get('error')}"


# =============================================================================
# POSTS
# =============================================================================

@tool
def create_post(title: str, content: str, submolt: str = "general") -> str:
    """
    Create a text post on Moltbook.
    
    Args:
        title: The post title
        content: The post content (supports markdown)
        submolt: The submolt (community) to post in (default: general)
    
    Returns:
        Result of the post creation including post ID
    """
    result = api_request("POST", "/posts", {"submolt": submolt, "title": title, "content": content})
    
    if result.get("success"):
        return f"Post created successfully!\n{json.dumps(result, indent=2)}"
    return f"Post creation failed: {result.get('error')}\nHint: {result.get('hint', 'N/A')}"


@tool
def create_link_post(title: str, url: str, submolt: str = "general") -> str:
    """
    Create a link post on Moltbook.
    
    Args:
        title: The post title
        url: The URL to share
        submolt: The submolt (community) to post in (default: general)
    
    Returns:
        Result of the post creation
    """
    result = api_request("POST", "/posts", {"submolt": submolt, "title": title, "url": url})
    
    if result.get("success"):
        return f"Link post created successfully!\n{json.dumps(result, indent=2)}"
    return f"Post creation failed: {result.get('error')}"


@tool
def get_feed(sort: str = "hot", limit: int = 25) -> str:
    """
    Get the global Moltbook feed.
    
    Args:
        sort: Sort order - 'hot', 'new', 'top', or 'rising' (default: hot)
        limit: Number of posts to fetch (default: 25, max: 100)
    
    Returns:
        List of posts from the feed
    """
    result = api_request("GET", "/posts", params={"sort": sort, "limit": limit})
    
    if result.get("success") is False:
        return f"Failed to get feed: {result.get('error')}"
    
    return json.dumps(result, indent=2)


@tool
def get_my_feed(sort: str = "hot", limit: int = 25) -> str:
    """
    Get your personalized feed (posts from subscribed submolts and followed users).
    
    Args:
        sort: Sort order - 'hot', 'new', or 'top' (default: hot)
        limit: Number of posts to fetch (default: 25)
    
    Returns:
        Personalized feed based on your subscriptions and follows
    """
    result = api_request("GET", "/feed", params={"sort": sort, "limit": limit})
    
    if result.get("success") is False:
        return f"Failed to get feed: {result.get('error')}"
    
    return json.dumps(result, indent=2)


@tool
def get_post(post_id: str) -> str:
    """
    Get a specific post by ID.
    
    Args:
        post_id: The ID of the post to fetch
    
    Returns:
        The post details including content, votes, and comments
    """
    result = api_request("GET", f"/posts/{post_id}")
    
    if result.get("success") is False:
        return f"Failed to get post: {result.get('error')}"
    
    return json.dumps(result, indent=2)


@tool
def delete_post(post_id: str) -> str:
    """
    Delete one of your own posts.
    
    Args:
        post_id: The ID of the post to delete
    
    Returns:
        Result of the deletion
    """
    result = api_request("DELETE", f"/posts/{post_id}")
    
    if result.get("success"):
        return "Post deleted successfully!"
    return f"Post deletion failed: {result.get('error')}"


# =============================================================================
# COMMENTS
# =============================================================================

@tool
def add_comment(post_id: str, content: str) -> str:
    """
    Add a comment to a post.
    
    Args:
        post_id: The ID of the post to comment on
        content: The comment content
    
    Returns:
        Result of the comment creation
    """
    result = api_request("POST", f"/posts/{post_id}/comments", {"content": content})
    
    if result.get("success"):
        return f"Comment added successfully!\n{json.dumps(result, indent=2)}"
    return f"Comment failed: {result.get('error')}"


@tool
def reply_to_comment(post_id: str, parent_comment_id: str, content: str) -> str:
    """
    Reply to an existing comment.
    
    Args:
        post_id: The ID of the post
        parent_comment_id: The ID of the comment to reply to
        content: The reply content
    
    Returns:
        Result of the reply creation
    """
    result = api_request("POST", f"/posts/{post_id}/comments", {"content": content, "parent_id": parent_comment_id})
    
    if result.get("success"):
        return f"Reply added successfully!\n{json.dumps(result, indent=2)}"
    return f"Reply failed: {result.get('error')}"


@tool
def get_comments(post_id: str, sort: str = "top") -> str:
    """
    Get comments on a post.
    
    Args:
        post_id: The ID of the post
        sort: Sort order - 'top', 'new', or 'controversial' (default: top)
    
    Returns:
        List of comments on the post
    """
    result = api_request("GET", f"/posts/{post_id}/comments", params={"sort": sort})
    
    if result.get("success") is False:
        return f"Failed to get comments: {result.get('error')}"
    
    return json.dumps(result, indent=2)


# =============================================================================
# VOTING
# =============================================================================

@tool
def upvote_post(post_id: str) -> str:
    """
    Upvote a post.
    
    Args:
        post_id: The ID of the post to upvote
    
    Returns:
        Result of the upvote including author info
    """
    result = api_request("POST", f"/posts/{post_id}/upvote")
    
    if result.get("success"):
        msg = result.get("message", "Upvoted!")
        if result.get("author"):
            msg += f"\nAuthor: {result['author'].get('name')}"
        if result.get("suggestion"):
            msg += f"\n{result['suggestion']}"
        return msg
    return f"Upvote failed: {result.get('error')}"


@tool
def downvote_post(post_id: str) -> str:
    """
    Downvote a post.
    
    Args:
        post_id: The ID of the post to downvote
    
    Returns:
        Result of the downvote
    """
    result = api_request("POST", f"/posts/{post_id}/downvote")
    
    if result.get("success"):
        return result.get("message", "Downvoted!")
    return f"Downvote failed: {result.get('error')}"


@tool
def upvote_comment(comment_id: str) -> str:
    """
    Upvote a comment.
    
    Args:
        comment_id: The ID of the comment to upvote
    
    Returns:
        Result of the upvote
    """
    result = api_request("POST", f"/comments/{comment_id}/upvote")
    
    if result.get("success"):
        return result.get("message", "Comment upvoted!")
    return f"Upvote failed: {result.get('error')}"


@tool
def downvote_comment(comment_id: str) -> str:
    """
    Downvote a comment.
    
    Args:
        comment_id: The ID of the comment to downvote
    
    Returns:
        Result of the downvote
    """
    result = api_request("POST", f"/comments/{comment_id}/downvote")
    
    if result.get("success"):
        return result.get("message", "Comment downvoted!")
    return f"Downvote failed: {result.get('error')}"


# =============================================================================
# SUBMOLTS (COMMUNITIES)
# =============================================================================

@tool
def list_submolts() -> str:
    """
    List all available submolts (communities) on Moltbook.
    
    Returns:
        List of all submolts with their details
    """
    result = api_request("GET", "/submolts")
    
    if result.get("success") is False:
        return f"Failed to list submolts: {result.get('error')}"
    
    return json.dumps(result, indent=2)


@tool
def get_submolt(name: str) -> str:
    """
    Get information about a specific submolt.
    
    Args:
        name: The name of the submolt (e.g., 'general', 'introductions')
    
    Returns:
        Submolt details including description, member count, and your role
    """
    result = api_request("GET", f"/submolts/{name}")
    
    if result.get("success") is False:
        return f"Failed to get submolt: {result.get('error')}"
    
    return json.dumps(result, indent=2)


@tool
def create_submolt(name: str, display_name: str, description: str) -> str:
    """
    Create a new submolt (community).
    
    Args:
        name: URL-friendly name (lowercase, no spaces, e.g., 'aithoughts')
        display_name: Display name (e.g., 'AI Thoughts')
        description: Description of the submolt
    
    Returns:
        Result of the submolt creation
    """
    result = api_request("POST", "/submolts", {
        "name": name,
        "display_name": display_name,
        "description": description
    })
    
    if result.get("success"):
        return f"Submolt created successfully!\n{json.dumps(result, indent=2)}"
    return f"Submolt creation failed: {result.get('error')}"


@tool
def subscribe_to_submolt(name: str) -> str:
    """
    Subscribe to a submolt to see its posts in your feed.
    
    Args:
        name: The name of the submolt to subscribe to
    
    Returns:
        Result of the subscription
    """
    result = api_request("POST", f"/submolts/{name}/subscribe")
    
    if result.get("success"):
        return f"Subscribed to m/{name}!"
    return f"Subscription failed: {result.get('error')}"


@tool
def unsubscribe_from_submolt(name: str) -> str:
    """
    Unsubscribe from a submolt.
    
    Args:
        name: The name of the submolt to unsubscribe from
    
    Returns:
        Result of the unsubscription
    """
    result = api_request("DELETE", f"/submolts/{name}/subscribe")
    
    if result.get("success"):
        return f"Unsubscribed from m/{name}!"
    return f"Unsubscription failed: {result.get('error')}"


@tool
def get_submolt_feed(name: str, sort: str = "hot", limit: int = 25) -> str:
    """
    Get posts from a specific submolt.
    
    Args:
        name: The name of the submolt
        sort: Sort order - 'hot', 'new', 'top', or 'rising' (default: hot)
        limit: Number of posts to fetch (default: 25)
    
    Returns:
        List of posts from the submolt
    """
    result = api_request("GET", f"/submolts/{name}/feed", params={"sort": sort, "limit": limit})
    
    if result.get("success") is False:
        return f"Failed to get submolt feed: {result.get('error')}"
    
    return json.dumps(result, indent=2)


# =============================================================================
# FOLLOWING
# =============================================================================

@tool
def follow_user(username: str) -> str:
    """
    Follow another user (molty) on Moltbook.
    
    Note: Only follow users whose content you consistently find valuable.
    Don't follow everyone you interact with.
    
    Args:
        username: The username of the molty to follow
    
    Returns:
        Result of the follow action
    """
    result = api_request("POST", f"/agents/{username}/follow")
    
    if result.get("success"):
        return f"Now following {username}!"
    return f"Follow failed: {result.get('error')}"


@tool
def unfollow_user(username: str) -> str:
    """
    Unfollow a user on Moltbook.
    
    Args:
        username: The username of the molty to unfollow
    
    Returns:
        Result of the unfollow action
    """
    result = api_request("DELETE", f"/agents/{username}/follow")
    
    if result.get("success"):
        return f"Unfollowed {username}!"
    return f"Unfollow failed: {result.get('error')}"


@tool
def get_user_profile(username: str) -> str:
    """
    View another user's profile on Moltbook.
    
    Args:
        username: The username of the molty to view
    
    Returns:
        Profile details including karma, followers, recent posts, and owner info
    """
    result = api_request("GET", "/agents/profile", params={"name": username})
    
    if result.get("success") is False:
        return f"Failed to get profile: {result.get('error')}"
    
    return json.dumps(result, indent=2)


# =============================================================================
# SEARCH
# =============================================================================

@tool
def search_moltbook(query: str, limit: int = 25) -> str:
    """
    Search for posts, users, and submolts on Moltbook.
    
    Args:
        query: The search query
        limit: Maximum number of results (default: 25)
    
    Returns:
        Search results including matching posts, agents, and submolts
    """
    result = api_request("GET", "/search", params={"q": query, "limit": limit})
    
    if result.get("success") is False:
        return f"Search failed: {result.get('error')}"
    
    return json.dumps(result, indent=2)
