"""Tools package for elcachorrohumano agent."""

from .moltbook import (
    # Registration & Auth
    register_on_moltbook,
    check_moltbook_status,
    get_my_profile,
    update_my_profile,
    upload_avatar,
    remove_avatar,
    # Posts
    create_post,
    create_link_post,
    get_feed,
    get_my_feed,
    get_post,
    delete_post,
    # Comments
    add_comment,
    reply_to_comment,
    get_comments,
    # Voting
    upvote_post,
    downvote_post,
    upvote_comment,
    downvote_comment,
    # Submolts (Communities)
    list_submolts,
    get_submolt,
    create_submolt,
    subscribe_to_submolt,
    unsubscribe_from_submolt,
    get_submolt_feed,
    # Following
    follow_user,
    unfollow_user,
    get_user_profile,
    # Search
    search_moltbook,
)

# Export all tools as a list for easy agent configuration
MOLTBOOK_TOOLS = [
    register_on_moltbook,
    check_moltbook_status,
    get_my_profile,
    update_my_profile,
    upload_avatar,
    remove_avatar,
    create_post,
    create_link_post,
    get_feed,
    get_my_feed,
    get_post,
    delete_post,
    add_comment,
    reply_to_comment,
    get_comments,
    upvote_post,
    downvote_post,
    upvote_comment,
    downvote_comment,
    list_submolts,
    get_submolt,
    create_submolt,
    subscribe_to_submolt,
    unsubscribe_from_submolt,
    get_submolt_feed,
    follow_user,
    unfollow_user,
    get_user_profile,
    search_moltbook,
]
