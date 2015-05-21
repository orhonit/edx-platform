"""
Setup script for the Open edX package.
"""

from setuptools import setup

setup(
    name="Open edX",
    version="0.3",
    install_requires=["distribute"],
    requires=[],
    # NOTE: These are not the names we should be installing.  This tree should
    # be reorganized to be a more conventional Python tree.
    packages=[
        "openedx.core.djangoapps.course_groups",
        "openedx.core.djangoapps.user_api",
        "lms",
        "cms",
    ],
    entry_points={
        "openedx.course_view_type": [
            "ccx = lms.djangoapps.ccx.plugins:CcxCourseViewType",
            "edxnotes = lms.djangoapps.edxnotes.plugins:EdxNotesCourseViewType",
            "instructor = lms.djangoapps.instructor.views.instructor_dashboard:InstructorDashboardViewType",
            'wiki = lms.djangoapps.course_wiki.tab:WikiCourseViewType',
            "courseware = openedx.core.djangoapps.course_views.course_views:CoursewareTab",
            "course_info = openedx.core.djangoapps.course_views.course_views:CourseInfoTab",
            'discussion = openedx.core.djangoapps.course_views.course_views:DiscussionTab',
            'external_discussion = openedx.core.djangoapps.course_views.course_views:ExternalDiscussionTab',
            'external_link = openedx.core.djangoapps.course_views.course_views:ExternalLinkTab',
            'textbooks = openedx.core.djangoapps.course_views.course_views:TextbookTabs',
            'pdf_textbooks = openedx.core.djangoapps.course_views.course_views:PDFTextbookTabs',
            'html_textbooks = openedx.core.djangoapps.course_views.course_views:HtmlTextbookTabs',
            'progress = openedx.core.djangoapps.course_views.course_views:ProgressTab',
            'static_tab = openedx.core.djangoapps.course_views.course_views:StaticTab',
            'peer_grading = lms.djangoapps.open_ended_grading.views:PeerGradingTab',
            'staff_grading = lms.djangoapps.open_ended_grading.views:StaffGradingTab',
            'open_ended = lms.djangoapps.open_ended_grading.views:OpenEndedGradingTab',
            'notes = lms.djangoapps.notes.views:NotesTab',
            'syllabus = openedx.core.djangoapps.course_views.course_views:SyllabusTab',
        ],
        "openedx.user_partition_scheme": [
            "random = openedx.core.djangoapps.user_api.partition_schemes:RandomUserPartitionScheme",
            "cohort = openedx.core.djangoapps.course_groups.partition_scheme:CohortPartitionScheme",
        ],
    }
)
