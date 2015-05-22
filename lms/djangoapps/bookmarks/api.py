"""
This File contains bookmark api method(s).
"""

from bookmarks.serializers import BookmarkSerializer
from bookmarks.models import Bookmark


def get_bookmark(user, usage_key, fields=None, serialized=False):
    """
    Return bookmark model or data.

    Args:
        user (User): The user requesting the bookmark.
        fields_to_add (list): List of fields to return for a bookmark.
        usage_key (UsageKey): The usage id of an Xblock.
        serialized (Bool): Decides to return object or json.

    Returns:
         A dict or object containing bookmark data.

    Raises:
         ObjectDoesNotExit: If Bookmark object does not exist.
    """
    bookmark = Bookmark.objects.get(usage_key=usage_key, user=user)

    return BookmarkSerializer(bookmark, context={"fields": fields}).data if serialized else bookmark
