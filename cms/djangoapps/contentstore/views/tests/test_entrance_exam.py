"""
Test module for Entrance Exams AJAX callback handler workflows
"""
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from contentstore.tests.utils import AjaxEnabledTestClient, CourseTestCase
from contentstore.utils import reverse_url
from contentstore.views.entrance_exam import create_entrance_exam
from models.settings.course_grading import CourseGradingModel
from models.settings.course_metadata import CourseMetadata
from opaque_keys.edx.keys import UsageKey
from student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore

if settings.FEATURES.get('MILESTONES_APP', False):
    from milestones import api as milestones_api
    from milestones.models import MilestoneRelationshipType
    from util.milestones_helpers import serialize_user


class EntranceExamHandlerTests(CourseTestCase):
    """
    Base test class for create, save, and delete
    """
    if settings.FEATURES.get('ENTRANCE_EXAMS', False):
        def setUp(self):
            """
            Shared scaffolding for individual test runs
            """
            super(EntranceExamHandlerTests, self).setUp()
            self.course_key = self.course.id
            self.usage_key = self.course.location
            self.course_url = '/course/{}'.format(unicode(self.course.id))
            self.exam_url = '/course/{}/entrance_exam/'.format(unicode(self.course.id))
            MilestoneRelationshipType.objects.create(name='requires', active=True)
            MilestoneRelationshipType.objects.create(name='fulfills', active=True)
            self.milestone_relationship_types = milestones_api.get_milestone_relationship_types()

        def test_contentstore_views_entrance_exam_post(self):
            """
            Unit Test: test_contentstore_views_entrance_exam_post
            """
            resp = self.client.post(self.exam_url, {}, http_accept='application/json')
            self.assertEqual(resp.status_code, 201)
            resp = self.client.get(self.exam_url)
            self.assertEqual(resp.status_code, 200)

            # Reload the test course now that the exam module has been added
            self.course = modulestore().get_course(self.course.id)
            metadata = CourseMetadata.fetch_all(self.course)
            self.assertTrue(metadata['entrance_exam_enabled'])
            self.assertIsNotNone(metadata['entrance_exam_minimum_score_pct'])
            self.assertIsNotNone(metadata['entrance_exam_id']['value'])
            self.assertTrue(len(milestones_api.get_course_milestones(unicode(self.course.id))))
            content_milestones = milestones_api.get_course_content_milestones(
                unicode(self.course.id),
                metadata['entrance_exam_id']['value'],
                self.milestone_relationship_types['FULFILLS']
            )
            self.assertTrue(len(content_milestones))

        def test_contentstore_views_entrance_exam_post_new_sequential_confirm_grader(self):
            """
            Unit Test: test_contentstore_views_entrance_exam_post
            """
            resp = self.client.post(self.exam_url, {}, http_accept='application/json')
            self.assertEqual(resp.status_code, 201)
            resp = self.client.get(self.exam_url)
            self.assertEqual(resp.status_code, 200)

            # Reload the test course now that the exam module has been added
            self.course = modulestore().get_course(self.course.id)

            # Add a new child sequential to the exam module
            # Confirm that the grader type is 'Entrance Exam'
            chapter_locator_string = json.loads(resp.content).get('locator')
            # chapter_locator = UsageKey.from_string(chapter_locator_string)
            seq_data = {
                'category': "sequential",
                'display_name': "Entrance Exam Subsection",
                'parent_locator': chapter_locator_string,
            }
            resp = self.client.ajax_post(reverse_url('xblock_handler'), seq_data)
            seq_locator_string = json.loads(resp.content).get('locator')
            seq_locator = UsageKey.from_string(seq_locator_string)
            section_grader_type = CourseGradingModel.get_section_grader_type(seq_locator)
            self.assertEqual('Entrance Exam', section_grader_type['graderType'])

        def test_contentstore_views_entrance_exam_get(self):
            """
            Unit Test: test_contentstore_views_entrance_exam_get
            """
            resp = self.client.post(
                self.exam_url,
                {'entrance_exam_minimum_score_pct': '50'},
                http_accept='application/json'
            )
            self.assertEqual(resp.status_code, 201)
            resp = self.client.get(self.exam_url)
            self.assertEqual(resp.status_code, 200)

        def test_contentstore_views_entrance_exam_delete(self):
            """
            Unit Test: test_contentstore_views_entrance_exam_delete
            """
            resp = self.client.post(self.exam_url, {}, http_accept='application/json')
            self.assertEqual(resp.status_code, 201)
            resp = self.client.get(self.exam_url)
            self.assertEqual(resp.status_code, 200)
            resp = self.client.delete(self.exam_url)
            self.assertEqual(resp.status_code, 204)
            resp = self.client.get(self.exam_url)
            self.assertEqual(resp.status_code, 404)

            user = User.objects.create(
                username='test_user',
                email='test_user@edx.org',
                is_active=True,
            )
            user.set_password('test')
            user.save()
            paths = milestones_api.get_course_milestones_fulfillment_paths(
                unicode(self.course_key),
                serialize_user(user)
            )
            print paths

            # What we have now is a course milestone requirement and no valid fulfillment
            # paths for the specified user.  The LMS is going to have to ignore this situation,
            # because we can't confidently prevent it from occuring at some point in the future.
            self.assertEqual(len(paths['milestone_1']), 0)

            # Re-adding an entrance exam to the course should fix the missing link
            # It wipes out any old entrance exam artifacts and inserts a new exam course chapter/module
            resp = self.client.post(self.exam_url, {}, http_accept='application/json')
            self.assertEqual(resp.status_code, 201)
            resp = self.client.get(self.exam_url)
            self.assertEqual(resp.status_code, 200)

        def test_contentstore_views_entrance_exam_delete_bogus_course(self):
            """
            Unit Test: test_contentstore_views_entrance_exam_delete_bogus_course
            """
            resp = self.client.delete('/course/bad/course/key/entrance_exam')
            self.assertEqual(resp.status_code, 400)

        def test_contentstore_views_entrance_exam_get_bogus_course(self):
            """
            Unit Test: test_contentstore_views_entrance_exam_get_bogus_course
            """
            resp = self.client.get('/course/bad/course/key/entrance_exam')
            self.assertEqual(resp.status_code, 400)

        def test_contentstore_views_entrance_exam_get_bogus_exam(self):
            """
            Unit Test: test_contentstore_views_entrance_exam_get_bogus_exam
            """
            resp = self.client.post(
                self.exam_url,
                {'entrance_exam_minimum_score_pct': '50'},
                http_accept='application/json'
            )
            self.assertEqual(resp.status_code, 201)
            resp = self.client.get(self.exam_url)
            self.assertEqual(resp.status_code, 200)
            self.course = modulestore().get_course(self.course.id)

            # Should raise an ItemNotFoundError and return a 404
            updated_metadata = {'entrance_exam_id': 'i4x://org.4/course_4/chapter/ed7c4c6a4d68409998e2c8554c4629d1'}
            CourseMetadata.update_from_dict(
                updated_metadata,
                self.course,
                self.user,
            )
            self.course = modulestore().get_course(self.course.id)
            resp = self.client.get(self.exam_url)
            self.assertEqual(resp.status_code, 404)

            # Should raise an InvalidKeyError and return a 404
            updated_metadata = {'entrance_exam_id': '123afsdfsad90f87'}
            CourseMetadata.update_from_dict(
                updated_metadata,
                self.course,
                self.user,
            )
            self.course = modulestore().get_course(self.course.id)
            resp = self.client.get(self.exam_url)
            self.assertEqual(resp.status_code, 404)

        def test_contentstore_views_entrance_exam_post_bogus_course(self):
            """
            Unit Test: test_contentstore_views_entrance_exam_post_bogus_course
            """
            resp = self.client.post(
                '/course/bad/course/key/entrance_exam',
                {},
                http_accept='application/json'
            )
            self.assertEqual(resp.status_code, 400)

        def test_contentstore_views_entrance_exam_post_invalid_http_accept(self):
            """
            Unit Test: test_contentstore_views_entrance_exam_post_invalid_http_accept
            """
            resp = self.client.post(
                '/course/bad/course/key/entrance_exam',
                {},
                http_accept='text/html'
            )
            self.assertEqual(resp.status_code, 400)

        def test_contentstore_views_entrance_exam_get_invalid_user(self):
            """
            Unit Test: test_contentstore_views_entrance_exam_get_invalid_user
            """
            user = User.objects.create(
                username='test_user',
                email='test_user@edx.org',
                is_active=True,
            )
            user.set_password('test')
            user.save()
            self.client = AjaxEnabledTestClient()
            self.client.login(username='test_user', password='test')
            resp = self.client.get(self.exam_url)
            self.assertEqual(resp.status_code, 403)

        def test_contentstore_views_entrance_exam_unsupported_method(self):
            """
            Unit Test: test_contentstore_views_entrance_exam_unsupported_method
            """
            resp = self.client.put(self.exam_url)
            self.assertEqual(resp.status_code, 405)

        def test_entrance_exam_view_direct_missing_score_setting(self):
            """
            Unit Test: test_entrance_exam_view_direct_missing_score_setting
            """
            user = UserFactory()
            user.is_staff = True
            request = RequestFactory()
            request.user = user

            resp = create_entrance_exam(request, self.course.id, None)
            self.assertEqual(resp.status_code, 201)
