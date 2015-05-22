"""
Tabs for courseware.
"""
from abc import abstractmethod

from openedx.core.lib.plugins.api import PluginManager
from xmodule.tabs import CourseTab, key_checker, need_name, link_value_func, link_reverse_func
from courseware.access import has_access
from student.models import CourseEnrollment
from ccx.overrides import get_current_ccx

_ = lambda text: text


# Stevedore extension point namespaces
COURSE_VIEW_TYPE_NAMESPACE = 'openedx.course_view_type'


class CourseViewType(object):
    """
    Base class of all course view type plugins.
    """
    name = None
    title = None
    view_name = None
    is_persistent = False
    is_hideable = False
    priority = None

    @classmethod
    def is_enabled(cls, course, settings, user=None):  # pylint: disable=unused-argument
        """Returns true if this course view is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            settings (dict): a dict of configuration settings

            user (User): the user interacting with the course
        """
        raise NotImplementedError()

    @classmethod
    def validate(cls, tab_dict, raise_error=True):  # pylint: disable=unused-argument
        """
        Validates the given dict-type `tab_dict` object to ensure it contains the expected keys.
        This method should be overridden by subclasses that require certain keys to be persisted in the tab.
        """
        return True


class CourseViewTypeManager(PluginManager):
    """
    Manager for all of the course view types that have been made available.

    All course view types should implement `CourseViewType`.
    """
    NAMESPACE = COURSE_VIEW_TYPE_NAMESPACE

    @classmethod
    def get_course_view_types(cls):
        """
        Returns the list of available course view types in their canonical order.
        """
        def compare_course_view_types(first_type, second_type):
            """Compares two course view types, for use in sorting."""
            first_priority = first_type.priority
            second_priority = second_type.priority
            if not first_priority == second_priority:
                if not first_priority:
                    return -1
                elif not second_priority:
                    return 1
                else:
                    return first_priority - second_priority
            first_name = first_type.name
            second_name = second_type.name
            if first_name < second_name:
                return -1
            elif first_name == second_name:
                return 0
            else:
                return 1
        course_view_types = CourseViewTypeManager.get_available_plugins().values()
        course_view_types.sort(cmp=compare_course_view_types)
        return course_view_types


def is_user_staff(course, user):
    """
    Returns true if the user is staff in the specified course, or globally.
    """
    return has_access(user, 'staff', course, course.id)


def is_user_enrolled_or_staff(course, user):
    """
    Returns true if the user is enrolled in the specified course,
    or if the user is staff.
    """
    return is_user_staff(course, user) or CourseEnrollment.is_enrolled(user, course.id)


class AuthenticatedCourseTab(CourseTab):
    """
    Abstract class for tabs that can be accessed by only authenticated users.
    """
    def is_enabled(self, course, settings, user=None):
        return not user or user.is_authenticated()


class EnrolledOrStaffTab(AuthenticatedCourseTab):
    """
    Abstract class for tabs that can be accessed by only users with staff access
    or users enrolled in the course.
    """
    def is_enabled(self, course, settings, user=None):  # pylint: disable=unused-argument
        if not user:
            return True
        return is_user_enrolled_or_staff(course, user)


class StaffTab(AuthenticatedCourseTab):
    """
    Abstract class for tabs that can be accessed by only users with staff access.
    """
    def is_enabled(self, course, settings, user=None):  # pylint: disable=unused-argument
        return not user or is_user_staff(course, user)


class CoursewareTab(EnrolledOrStaffTab):
    """
    A tab containing the course content.
    """

    type = 'courseware'
    name = 'courseware'
    is_movable = False
    priority = 10

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(CoursewareTab, self).__init__(
            # Translators: 'Courseware' refers to the tab in the courseware that leads to the content of a course
            name=_('Courseware'),  # support fixed name for the courseware tab
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )


class CourseInfoTab(CourseTab):
    """
    A tab containing information about the course.
    """

    type = 'course_info'
    name = 'course_info'
    is_movable = False
    priority = 20

    def __init__(self, tab_dict=None):
        super(CourseInfoTab, self).__init__(
            # Translators: "Course Info" is the name of the course's information and updates page
            name=tab_dict['name'] if tab_dict else _('Course Info'),
            tab_id='info',
            link_func=link_reverse_func('info'),
        )

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(CourseInfoTab, cls).validate(tab_dict, raise_error) and need_name(tab_dict, raise_error)


class ProgressTab(EnrolledOrStaffTab):
    """
    A tab containing information about the authenticated user's progress.
    """

    type = 'progress'
    name = 'progress'
    priority = None

    def __init__(self, tab_dict=None):
        super(ProgressTab, self).__init__(
            # Translators: "Progress" is the name of the student's course progress page
            name=tab_dict['name'] if tab_dict else _('Progress'),
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )

    def is_enabled(self, course, settings, user=None):
        super_can_display = super(ProgressTab, self).is_enabled(course, settings, user=user)
        return super_can_display and not course.hide_progress_tab

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(ProgressTab, cls).validate(tab_dict, raise_error) and need_name(tab_dict, raise_error)


class DiscussionTab(EnrolledOrStaffTab):
    """
    A tab only for the new Berkeley discussion forums.
    """

    type = 'discussion'
    name = 'discussion'
    priority = None

    def __init__(self, tab_dict=None):
        super(DiscussionTab, self).__init__(
            # Translators: "Discussion" is the title of the course forum page
            name=tab_dict['name'] if tab_dict else _('Discussion'),
            tab_id=self.type,
            link_func=link_reverse_func('django_comment_client.forum.views.forum_form_discussion'),
        )

    def is_enabled(self, course, settings, user=None):
        if settings.FEATURES.get('CUSTOM_COURSES_EDX', False):
            if get_current_ccx():
                return False
        super_can_display = super(DiscussionTab, self).is_enabled(course, settings, user=user)
        return settings.FEATURES.get('ENABLE_DISCUSSION_SERVICE') and super_can_display

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(DiscussionTab, cls).validate(tab_dict, raise_error) and need_name(tab_dict, raise_error)


class LinkTab(CourseTab):
    """
    Abstract class for tabs that contain external links.
    """
    link_value = ''

    def __init__(self, name, tab_id, link_value):
        self.link_value = link_value
        super(LinkTab, self).__init__(
            name=name,
            tab_id=tab_id,
            link_func=link_value_func(self.link_value),
        )

    def __getitem__(self, key):
        if key == 'link':
            return self.link_value
        else:
            return super(LinkTab, self).__getitem__(key)

    def __setitem__(self, key, value):
        if key == 'link':
            self.link_value = value
        else:
            super(LinkTab, self).__setitem__(key, value)

    def to_json(self):
        to_json_val = super(LinkTab, self).to_json()
        to_json_val.update({'link': self.link_value})
        return to_json_val

    def __eq__(self, other):
        if not super(LinkTab, self).__eq__(other):
            return False
        return self.link_value == other.get('link')

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(LinkTab, cls).validate(tab_dict, raise_error) and key_checker(['link'])(tab_dict, raise_error)


class ExternalDiscussionTab(LinkTab):
    """
    A tab that links to an external discussion service.
    """

    type = 'external_discussion'
    name = 'external_discussion'
    priority = None

    def __init__(self, tab_dict=None, link_value=None):
        super(ExternalDiscussionTab, self).__init__(
            # Translators: 'Discussion' refers to the tab in the courseware that leads to the discussion forums
            name=_('Discussion'),
            tab_id='discussion',
            link_value=tab_dict['link'] if tab_dict else link_value,
        )


class ExternalLinkTab(LinkTab):
    """
    A tab containing an external link.
    """
    type = 'external_link'
    name = 'external_link'
    priority = None

    def __init__(self, tab_dict):
        super(ExternalLinkTab, self).__init__(
            name=tab_dict['name'],
            tab_id=None,  # External links are never active.
            link_value=tab_dict['link'],
        )


class StaticTab(CourseTab):
    """
    A custom tab.
    """
    type = 'static_tab'
    name = 'static_tab'
    priority = None

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return (super(StaticTab, cls).validate(tab_dict, raise_error)
                and key_checker(['name', 'url_slug'])(tab_dict, raise_error))

    def __init__(self, tab_dict=None, name=None, url_slug=None):
        def link_func(course, reverse_func):
            """ Returns a url for a given course and reverse function. """
            return reverse_func(self.type, args=[course.id.to_deprecated_string(), self.url_slug])

        self.url_slug = tab_dict['url_slug'] if tab_dict else url_slug
        super(StaticTab, self).__init__(
            name=tab_dict['name'] if tab_dict else name,
            tab_id='static_tab_{0}'.format(self.url_slug),
            link_func=link_func,
        )

    def __getitem__(self, key):
        if key == 'url_slug':
            return self.url_slug
        else:
            return super(StaticTab, self).__getitem__(key)

    def __setitem__(self, key, value):
        if key == 'url_slug':
            self.url_slug = value
        else:
            super(StaticTab, self).__setitem__(key, value)

    def to_json(self):
        to_json_val = super(StaticTab, self).to_json()
        to_json_val.update({'url_slug': self.url_slug})
        return to_json_val

    def __eq__(self, other):
        if not super(StaticTab, self).__eq__(other):
            return False
        return self.url_slug == other.get('url_slug')


class SingleTextbookTab(CourseTab):
    """
    A tab representing a single textbook.  It is created temporarily when enumerating all textbooks within a
    Textbook collection tab.  It should not be serialized or persisted.
    """
    type = 'single_textbook'
    name = 'single_textbook'
    is_movable = False
    is_collection_item = True
    priority = None

    def to_json(self):
        raise NotImplementedError('SingleTextbookTab should not be serialized.')


class TextbookTabsBase(AuthenticatedCourseTab):
    """
    Abstract class for textbook collection tabs classes.
    """
    is_collection = True

    def __init__(self, tab_id):
        # Translators: 'Textbooks' refers to the tab in the course that leads to the course' textbooks
        super(TextbookTabsBase, self).__init__(
            name=_("Textbooks"),
            tab_id=tab_id,
            link_func=None,
        )

    @abstractmethod
    def items(self, course):
        """
        A generator for iterating through all the SingleTextbookTab book objects associated with this
        collection of textbooks.
        """
        pass


class TextbookTabs(TextbookTabsBase):
    """
    A tab representing the collection of all textbook tabs.
    """
    type = 'textbooks'
    name = 'textbooks'
    priority = None

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(TextbookTabs, self).__init__(
            tab_id=self.type,
        )

    def is_enabled(self, course, settings, user=None):
        return settings.FEATURES.get('ENABLE_TEXTBOOK')

    def items(self, course):
        for index, textbook in enumerate(course.textbooks):
            yield SingleTextbookTab(
                name=textbook.title,
                tab_id='textbook/{0}'.format(index),
                link_func=lambda course, reverse_func, index=index: reverse_func(
                    'book', args=[course.id.to_deprecated_string(), index]
                ),
            )


class PDFTextbookTabs(TextbookTabsBase):
    """
    A tab representing the collection of all PDF textbook tabs.
    """
    type = 'pdf_textbooks'
    name = 'pdf_textbooks'
    priority = None

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(PDFTextbookTabs, self).__init__(
            tab_id=self.type,
        )

    def items(self, course):
        for index, textbook in enumerate(course.pdf_textbooks):
            yield SingleTextbookTab(
                name=textbook['tab_title'],
                tab_id='pdftextbook/{0}'.format(index),
                link_func=lambda course, reverse_func, index=index: reverse_func(
                    'pdf_book', args=[course.id.to_deprecated_string(), index]
                ),
            )


class HtmlTextbookTabs(TextbookTabsBase):
    """
    A tab representing the collection of all Html textbook tabs.
    """
    type = 'html_textbooks'
    name = 'html_textbooks'
    priority = None

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(HtmlTextbookTabs, self).__init__(
            tab_id=self.type,
        )

    def items(self, course):
        for index, textbook in enumerate(course.html_textbooks):
            yield SingleTextbookTab(
                name=textbook['tab_title'],
                tab_id='htmltextbook/{0}'.format(index),
                link_func=lambda course, reverse_func, index=index: reverse_func(
                    'html_book', args=[course.id.to_deprecated_string(), index]
                ),
            )
