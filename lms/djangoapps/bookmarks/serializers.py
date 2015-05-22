"""
Serializers for Bookmarks.
"""
from rest_framework import serializers

from .models import Bookmark


class BookmarkSerializer(serializers.ModelSerializer):
    """
    Class that serializes the Bookmark model.
    """
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        try:
            fields = kwargs['context'].pop('fields', [])
        except KeyError:
            from .views import DEFAULT_FIELDS
            fields = DEFAULT_FIELDS
        # Instantiate the superclass normally
        super(BookmarkSerializer, self).__init__(*args, **kwargs)

        if fields:
            # Drop any fields that are not specified in the `fields` argument.
            required_fields = set(fields)
            all_fields = set(self.fields.keys())
            for field_name in all_fields - required_fields:
                self.fields.pop(field_name)

    id = serializers.SerializerMethodField('resource_id')  # pylint: disable=invalid-name
    course_id = serializers.Field(source='course_key')
    usage_id = serializers.Field(source='usage_key')
    path = serializers.Field(source='path')

    class Meta(object):  # pylint: disable=missing-docstring
        """ Serializer metadata """
        model = Bookmark
        fields = ("id", "course_id", "usage_id", "display_name", "path", "created")

    def resource_id(self, bookmark):
        """
        Return the REST resource id: {username, usage_id}.
        """
        return "{0},{1}".format(bookmark.user.username, bookmark.usage_key)
