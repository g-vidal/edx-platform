"""
Tests of various instructor dashboard features that include lists of students
"""
from unittest import skip
from django.conf import settings
from django.test.client import RequestFactory
from django.test.utils import override_settings
from markupsafe import escape

from courseware.tests.tests import TEST_DATA_MIXED_MODULESTORE
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from instructor.views import legacy


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestXss(ModuleStoreTestCase):
    def setUp(self):
        self._request_factory = RequestFactory()
        self._course = CourseFactory.create()
        self._evil_student = UserFactory.create(
            email="robot+evil@edx.org",
            username="evil-robot",
            profile__name='<span id="evil">Evil Robot</span>',
        )
        self._instructor = UserFactory.create(
            email="robot+instructor@edx.org",
            username="instructor",
            is_staff=True
        )
        CourseEnrollmentFactory.create(
            user=self._evil_student,
            course_id=self._course.id
        )

    def _test_action(self, action):
        """
        Test for XSS vulnerability in the given action

        Build a request with the given action, call the instructor dashboard
        view, and check that HTML code in a user's name is properly escaped.
        """
        req  = self._request_factory.post(
            "dummy_url",
            data={"action": action}
        )
        req.user = self._instructor
        req.session = {}
        resp = legacy.instructor_dashboard(req, self._course.id)
        respUnicode = resp.content.decode(settings.DEFAULT_CHARSET)
        self.assertNotIn(self._evil_student.profile.name, respUnicode)
        self.assertIn(escape(self._evil_student.profile.name), respUnicode)

    def test_list_enrolled(self):
        self._test_action("List enrolled students")

    def test_dump_list_of_enrolled(self):
        self._test_action("Dump list of enrolled students")

    @skip
    def test_dump_grades(self):
        # TODO: get this to work again.  It would require that grades
        # have been generated in order to have something to be dumped.
        self._test_action("Dump Grades for all students in this course")
