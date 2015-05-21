"""
Registers the "edX Notes" feature for the edX platform.
"""

from django.utils.translation import ugettext as _

from openedx.core.djangoapps.course_views.course_views import CourseViewType


class EdxNotesCourseViewType(CourseViewType):
    """
    The representation of the edX Notes course view type.
    """

    name = "edxnotes"
    title = _("Notes")
    view_name = "edxnotes"
    is_persistent = True

    @classmethod
    def is_enabled(cls, course, settings, user=None):  # pylint: disable=unused-argument
        """Returns true if the edX Notes feature is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            settings (dict): a dict of configuration settings
            user (User): the user interacting with the course
        """
        return course.edxnotes
