from unittest.mock import patch
from backend.models.postgis.statuses import (
    TaskStatus,
    MappingNotAllowed,
    ProjectStatus,
    ValidatingNotAllowed,
)

from backend.services.project_admin_service import ProjectAdminService
from backend.services.project_service import ProjectService
from backend.services.users.user_service import UserService
from tests.backend.base import BaseTestCase
from tests.backend.helpers.test_helpers import (
    create_canned_project,
    return_canned_user,
    generate_encoded_token,
    create_canned_license,
)
from backend.models.postgis.task import Task, TaskAction


class TasksActionsMapAllAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_project, _ = create_canned_project()
        self.url = f"/api/v2/projects/{self.test_project.id}/tasks/actions/map-all/"
        self.test_user = return_canned_user(username="Test User", id=11111)
        self.test_user.create()
        self.user_session_token = generate_encoded_token(self.test_user.id)

    def test_map_all_tasks_returns_401_for_unauthorized_request(self):
        """Test returns 401 on request without session token."""

        # Act
        response = self.client.post(self.url)
        # Assert
        self.assertEqual(response.status_code, 401)

    @patch.object(ProjectAdminService, "is_user_action_permitted_on_project")
    def test_map_all_tasks_returns_403_for_non_PM_role_request(self, mock_pm_role):
        """Test returns 403 on request by user without PM role"""

        # Arrange
        mock_pm_role.return_value = False
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "UserPermissionError")

    @patch.object(ProjectAdminService, "is_user_action_permitted_on_project")
    def test_map_all_tasks_is_allowed_for_user_with_pm_role(self, mock_pm_role):
        """Test returns 200 on request by user with PM role and all tasks are mapped"""
        # Arrange
        init_ready_tasks = Task.get_tasks_by_status(
            self.test_project.id, TaskStatus.READY.name
        )
        mock_pm_role.return_value = True
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        self.assertEqual(response.status_code, 200)
        for task in init_ready_tasks:
            self.assertEqual(task.task_status, TaskStatus.MAPPED.value)
        self.assertEqual(
            self.test_project.tasks_mapped,
            (
                self.test_project.total_tasks
                - self.test_project.tasks_bad_imagery
                - self.test_project.tasks_validated
            ),
        )


class TasksActionsValidateAllAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_project, _ = create_canned_project()
        self.url = (
            f"/api/v2/projects/{self.test_project.id}/tasks/actions/validate-all/"
        )
        self.test_user = return_canned_user(username="Test User", id=11111)
        self.test_user.create()
        self.user_session_token = generate_encoded_token(self.test_user.id)

    def test_validate_all_tasks_returns_401_for_unauthorized_request(self):
        """Test returns 401 on request without session token."""
        # Act
        response = self.client.post(self.url)
        # Assert
        self.assertEqual(response.status_code, 401)

    @patch.object(ProjectAdminService, "is_user_action_permitted_on_project")
    def test_validate_all_tasks_returns_403_for_non_PM_role_request(self, mock_pm_role):
        """Test returns 403 on request by user without PM role"""

        # Arrange
        mock_pm_role.return_value = False
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "UserPermissionError")

    @patch.object(ProjectAdminService, "is_user_action_permitted_on_project")
    def test_validate_all_tasks_is_allowed_for_user_with_pm_role(self, mock_pm_role):
        """Test returns 200 on request by user with PM role and all tasks are validated"""
        # Arrange
        init_mapped_tasks = Task.get_tasks_by_status(
            self.test_project.id, TaskStatus.MAPPED.name
        )
        mock_pm_role.return_value = True
        init_tasks_validated = self.test_project.tasks_validated
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        self.assertEqual(response.status_code, 200)
        for task in init_mapped_tasks:
            self.assertEqual(task.task_status, TaskStatus.VALIDATED.value)
        self.assertEqual(
            self.test_project.tasks_validated,
            init_tasks_validated + len(init_mapped_tasks),
        )


class TasksActionsInvalidateAllAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_project, _ = create_canned_project()
        self.url = (
            f"/api/v2/projects/{self.test_project.id}/tasks/actions/invalidate-all/"
        )
        self.test_user = return_canned_user(username="Test User", id=11111)
        self.test_user.create()
        self.user_session_token = generate_encoded_token(self.test_user.id)

    def test_invalidate_all_tasks_returns_401_for_unauthorized_request(self):
        """Test returns 401 on request without session token."""
        # Act
        response = self.client.post(self.url)
        # Assert
        self.assertEqual(response.status_code, 401)

    @patch.object(ProjectAdminService, "is_user_action_permitted_on_project")
    def test_invalidate_all_tasks_returns_403_for_non_PM_role_request(
        self, mock_pm_role
    ):
        """Test returns 403 on request by user without PM role"""

        # Arrange
        mock_pm_role.return_value = False
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "UserPermissionError")

    @patch.object(ProjectAdminService, "is_user_action_permitted_on_project")
    def test_invalidate_all_tasks_is_allowed_for_user_with_pm_role(self, mock_pm_role):
        """Test that all tasks with status of validated are invalidated"""
        # Arrange
        validated_tasks = Task.get_tasks_by_status(
            self.test_project.id, TaskStatus.VALIDATED.name
        )
        mock_pm_role.return_value = True
        init_tasks_validated = self.test_project.tasks_validated
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check status of all tasks that had status of validated before validated
        for task in validated_tasks:
            self.assertEqual(task.task_status, TaskStatus.INVALIDATED.value)
        # Check if counters are set correctly
        self.assertEqual(self.test_project.tasks_validated, 0)

        after_tasks_invalidated = len(
            Task.get_tasks_by_status(self.test_project.id, TaskStatus.INVALIDATED.name)
        )
        self.assertEqual(after_tasks_invalidated, init_tasks_validated)


class TasksActionsResetBadImageryAllAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_project, _ = create_canned_project()
        self.url = f"/api/v2/projects/{self.test_project.id}/tasks/actions/reset-all-badimagery/"
        self.test_user = return_canned_user(username="Test User", id=11111)
        self.test_user.create()
        self.user_session_token = generate_encoded_token(self.test_user.id)

    def test_reset_all_badimagery_tasks_returns_401_for_unauthorized_request(self):
        """Test returns 401 on request without session token."""
        # Act
        response = self.client.post(self.url)
        # Assert
        self.assertEqual(response.status_code, 401)

    @patch.object(ProjectAdminService, "is_user_action_permitted_on_project")
    def test_reset_all_badimagery_tasks_returns_403_for_non_PM_role_request(
        self, mock_pm_role
    ):
        """Test returns 403 on request by user without PM role"""

        # Arrange
        mock_pm_role.return_value = False
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "UserPermissionError")

    @patch.object(ProjectAdminService, "is_user_action_permitted_on_project")
    def test_reset_all_badimagery_tasks_is_allowed_for_user_with_pm_role(
        self, mock_pm_role
    ):
        """Test returns 200 on request by user with PM role and resets all bad imagery tasks to ready"""
        # Arrange
        init_bad_imagery_tasks = Task.get_tasks_by_status(
            self.test_project.id, TaskStatus.BADIMAGERY.name
        )
        mock_pm_role.return_value = True
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check status of all tasks that had status of validated before validated
        for task in init_bad_imagery_tasks:
            self.assertEqual(task.task_status, TaskStatus.READY.value)
        # Check if counters are set correctly
        self.assertEqual(self.test_project.tasks_bad_imagery, 0)


class TasksActionsResetAllAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_project, _ = create_canned_project()
        self.url = f"/api/v2/projects/{self.test_project.id}/tasks/actions/reset-all/"
        self.test_user = return_canned_user(username="Test User", id=11111)
        self.test_user.create()
        self.user_session_token = generate_encoded_token(self.test_user.id)

    def test_reset_all_tasks_returns_401_for_unauthorized_request(self):
        """Test returns 401 on request without session token."""
        # Act
        response = self.client.post(self.url)
        # Assert
        self.assertEqual(response.status_code, 401)

    @patch.object(ProjectAdminService, "is_user_action_permitted_on_project")
    def test_reset_all_tasks_returns_403_for_non_PM_role_request(self, mock_pm_role):
        "Test returns 403 on request by user without PM role"

        # Arrange
        mock_pm_role.return_value = False
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "UserPermissionError")

    @patch.object(ProjectAdminService, "is_user_action_permitted_on_project")
    def test_reset_all_tasks_is_allowed_for_user_with_pm_role(self, mock_pm_role):
        """ Test returns 200 on request by user with PM role and resets all tasks to ready """
        # Arrange
        init_non_ready_tasks = []
        for status in [
            TaskStatus.MAPPED.name,
            TaskStatus.VALIDATED.name,
            TaskStatus.INVALIDATED.name,
            TaskStatus.BADIMAGERY.name,
        ]:
            init_non_ready_tasks.extend(
                Task.get_tasks_by_status(self.test_project.id, status)
            )

        mock_pm_role.return_value = True
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check status of all tasks that had status of validated before validated
        for task in init_non_ready_tasks:
            self.assertEqual(task.task_status, TaskStatus.READY.value)
        # Check if counters are set correctly
        ready_tasks = len(
            Task.get_tasks_by_status(self.test_project.id, TaskStatus.READY.name)
        )
        self.assertEqual(ready_tasks, self.test_project.total_tasks)
        self.assertEqual(self.test_project.tasks_mapped, 0)
        self.assertEqual(self.test_project.tasks_validated, 0)
        self.assertEqual(self.test_project.tasks_bad_imagery, 0)


class TestTasksActionsMappingLockAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_project, _ = create_canned_project()
        self.url = (
            f"/api/v2/projects/{self.test_project.id}/tasks/actions/lock-for-mapping/1/"
        )
        self.test_user = return_canned_user(username="Test User", id=11111)
        self.test_user.create()
        self.user_session_token = generate_encoded_token(self.test_user.id)

    def test_mapping_lock_returns_401_for_unauthorized_request(self):
        """Test returns 401 on request without session token."""
        # Act
        response = self.client.post(self.url)
        # Assert
        self.assertEqual(response.status_code, 401)

    def test_mapping_lock_returns_404_for_invalid_project_id(self):
        """Test returns 404 on request with invalid project id."""
        # Act
        response = self.client.post(
            "/api/v2/projects/999999/tasks/actions/lock-for-mapping/1/",
            headers={"Authorization": self.user_session_token},
        )
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["SubCode"], "NotFound")

    def test_mapping_lock_returns_404_for_invalid_task_id(self):
        """Test returns 404 on request with invalid task id."""
        # Act
        response = self.client.post(
            f"/api/v2/projects/{self.test_project.id}/tasks/actions/lock-for-mapping/999999/",
            headers={"Authorization": self.user_session_token},
        )
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["SubCode"], "NotFound")

    @patch.object(ProjectService, "is_user_permitted_to_map")
    def test_mapping_lock_returns_403_for_if_user_not_allowed_to_map(
        self, mock_permitted
    ):
        """Test returns 403 on request by user who doesn't have required permission to map."""
        # Arrange
        mock_permitted.return_value = False, MappingNotAllowed.PROJECT_NOT_PUBLISHED
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.READY.value
        task.update()
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "ProjectNotPublished")

    @patch.object(ProjectAdminService, "is_user_action_permitted_on_project")
    def test_mapping_lock_returns_403_if_task_in_invalid_state_for_mapping(
        self, mock_pm_role
    ):
        """ Test returns 403 if task is in invalid state for mapping. i.e. not in READY or INVALIDATED state. """
        # Arrange
        mock_pm_role.return_value = True
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        # As Task 1 is in MAPPED state, it should not be allowed to be locked for mapping.
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "InvalidTaskState")

        # Arrange
        # Change task state to VALIDATED
        self.test_project.tasks[0].task_status = TaskStatus.VALIDATED.value
        self.test_project.tasks[0].update()
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        # As Task 1 is in VALIDATED state, it should not be allowed to be locked for mapping.
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "InvalidTaskState")

    @patch.object(UserService, "has_user_accepted_license")
    def test_mapping_lock_returns_403_if_project_licence_not_accepted(
        self, mock_accepted
    ):
        """ Test returns 403 if project licence is not accepted. """
        # Arrange
        mock_accepted.return_value = False
        self.test_project.status = ProjectStatus.PUBLISHED.value
        self.test_project.license_id = create_canned_license()
        self.test_project.save()
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.READY.value
        task.update()
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json["SubCode"], "UserLicenseError")

    @patch.object(ProjectService, "is_user_permitted_to_map")
    def test_mapping_lock_is_allowed_for_user_with_mapping_permission(
        self, mock_permitted
    ):
        """ Test returns 200 if user has mapping permission. """
        # Arrange
        mock_permitted.return_value = True, "User allowed to map"
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.READY.value
        task.update()
        # Act
        response = self.client.post(
            self.url, headers={"Authorization": self.user_session_token}
        )
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["taskId"], 1)
        self.assertEqual(response.json["projectId"], self.test_project.id)
        self.assertEqual(
            response.json["taskStatus"], TaskStatus.LOCKED_FOR_MAPPING.name
        )
        self.assertEqual(response.json["lockHolder"], self.test_user.username)


class TestTasksActionsMappingUnlockAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_project, self.test_author = create_canned_project()
        self.test_user = return_canned_user("Test User", 1111111)
        self.test_user.create()
        self.user_session_token = generate_encoded_token(self.test_user.id)
        self.url = f"/api/v2/projects/{self.test_project.id}/tasks/actions/unlock-after-mapping/1/"

    def test_mapping_unlock_returns_401_for_unauthenticated_user(self):
        """Test returns 401 on request from unauthenticated user."""
        # Act
        response = self.client.post(self.url)
        # Assert
        self.assertEqual(response.status_code, 401)

    def test_mapping_unlock_returns_400_if_invalid_data(self):
        """Test returns 404 on request with invalid data."""
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={
                "status": "test"
            },  # Since valid status are MAPPED, INVALIDATED, BADIMAGERY
        )
        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["SubCode"], "InvalidData")

    def test_mapping_unlock_returns_404_for_invalid_project_id(self):
        """Test returns 404 on request with invalid project id."""
        # Act
        response = self.client.post(
            "/api/v2/projects/999999/tasks/actions/unlock-after-mapping/1/",
            headers={"Authorization": self.user_session_token},
            json={"status": "MAPPED"},
        )
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["SubCode"], "NotFound")

    def test_mapping_unlock_returns_404_for_invalid_task_id(self):
        """Test returns 404 on request with invalid task id."""
        # Act
        response = self.client.post(
            f"/api/v2/projects/{self.test_project.id}/tasks/actions/unlock-after-mapping/999999/",
            headers={"Authorization": self.user_session_token},
            json={"status": "MAPPED"},
        )
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["SubCode"], "NotFound")

    def test_mapping_unlock_returns_403_if_task_not_locked_for_mapping(self):
        """Test returns 403 if task is not locked for mapping."""
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"status": "MAPPED"},
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "LockBeforeUnlocking")

    def test_mapping_unlock_returns_403_if_task_locked_by_other_user(self):
        """Test returns 403 if task is locked by other user."""
        # Arrange
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.LOCKED_FOR_MAPPING.value
        task.locked_by = self.test_author.id
        task.update()
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"status": "MAPPED"},
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "TaskNotOwned")

    def test_returns_403_if_invalid_new_state_passed(self):
        """Test returns 403 if invalid new state passed as new task state should be READY, MAPPED or BADIMAGERY."""
        # Arrange
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.LOCKED_FOR_MAPPING.value
        task.locked_by = self.test_user.id
        task.update()
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"status": "INVALIDATED"},
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "InvalidUnlockState")

    def test_mapping_unlock_returns_200_on_success(self):
        """Test returns 200 on success."""
        # Arrange
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.LOCKED_FOR_MAPPING.value
        task.locked_by = self.test_user.id
        task.update()
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"status": "MAPPED"},
        )
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["taskId"], 1)
        self.assertEqual(response.json["projectId"], self.test_project.id)
        self.assertEqual(response.json["taskStatus"], TaskStatus.MAPPED.name)
        last_task_history = response.json["taskHistory"][0]
        self.assertEqual(last_task_history["action"], TaskAction.STATE_CHANGE.name)
        self.assertEqual(last_task_history["actionText"], TaskStatus.MAPPED.name)
        self.assertEqual(last_task_history["actionBy"], self.test_user.username)

    def test_mapping_unlock_returns_200_on_success_with_comment(self):
        """Test returns 200 on success."""
        # Arrange
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.LOCKED_FOR_MAPPING.value
        task.locked_by = self.test_user.id
        task.update()
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={
                "status": "BADIMAGERY",  # Lets test with BADIMAGERY this time
                "comment": "cannot map",
            },
        )
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["taskId"], 1)
        self.assertEqual(response.json["projectId"], self.test_project.id)
        self.assertEqual(response.json["taskStatus"], TaskStatus.BADIMAGERY.name)

        last_task_history = response.json["taskHistory"][0]
        self.assertEqual(last_task_history["action"], TaskAction.STATE_CHANGE.name)
        self.assertEqual(last_task_history["actionText"], TaskStatus.BADIMAGERY.name)
        self.assertEqual(last_task_history["actionBy"], self.test_user.username)

        last_comment_history = response.json["taskHistory"][1]
        self.assertEqual(last_comment_history["action"], TaskAction.COMMENT.name)
        self.assertEqual(last_comment_history["actionText"], "cannot map")
        self.assertEqual(last_comment_history["actionBy"], self.test_user.username)


class TestTasksActionsMappingStopAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_project, self.test_author = create_canned_project()
        self.test_user = return_canned_user("Test User", 11111111)
        self.test_user.create()
        self.user_session_token = generate_encoded_token(self.test_user.id)
        self.url = (
            f"/api/v2/projects/{self.test_project.id}/tasks/actions/stop-mapping/1/"
        )

    def test_returns_401_if_user_not_authorized(self):
        """Test returns 401 if user not authorized."""
        # Act
        response = self.client.post(self.url)
        # Assert
        self.assertEqual(response.status_code, 401)

    def test_mapping_stop_returns_404_for_invalid_project_id(self):
        """Test returns 404 on request with invalid project id."""
        # Act
        response = self.client.post(
            "/api/v2/projects/999999/tasks/actions/stop-mapping/1/",
            headers={"Authorization": self.user_session_token},
        )
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["SubCode"], "NotFound")

    def test_mapping_stop_returns_404_for_invalid_task_id(self):
        """Test returns 404 on request with invalid task id."""
        # Act
        response = self.client.post(
            f"/api/v2/projects/{self.test_project.id}/tasks/actions/stop-mapping/999999/",
            headers={"Authorization": self.user_session_token},
        )
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["SubCode"], "NotFound")

    def test_mapping_stop_returns_403_if_task_not_locked_for_mapping(self):
        """Test returns 403 if task not locked for mapping."""
        # Since we are not locking the task, it should return 403
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "LockBeforeUnlocking")

    def test_mapping_stop_returns_403_if_task_locked_by_other_user(self):
        """Test returns 403 if task locked by other user."""
        # Arrange
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.LOCKED_FOR_MAPPING.value
        task.locked_by = self.test_author.id
        task.update()
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "TaskNotOwned")

    def test_mapping_stop_returns_200_on_success(self):
        """Test returns 200 on success."""
        # Arrange
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.LOCKED_FOR_MAPPING.value
        task.locked_by = self.test_user.id
        task.update()
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
        )
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["taskId"], 1)
        self.assertEqual(response.json["projectId"], self.test_project.id)
        self.assertEqual(response.json["taskStatus"], TaskStatus.READY.name)

    def test_mapping_stop_returns_200_on_success_with_comment(self):
        """Test returns 200 on success."""
        # Arrange
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.LOCKED_FOR_MAPPING.value
        task.locked_by = self.test_user.id
        task.update()
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={
                "comment": "cannot map",
            },
        )
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["taskId"], 1)
        self.assertEqual(response.json["projectId"], self.test_project.id)
        self.assertEqual(response.json["taskStatus"], TaskStatus.READY.name)

        last_comment_history = response.json["taskHistory"][0]
        self.assertEqual(last_comment_history["action"], TaskAction.COMMENT.name)
        self.assertEqual(last_comment_history["actionText"], "cannot map")
        self.assertEqual(last_comment_history["actionBy"], self.test_user.username)


class TestTasksActionsValidationLockAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_project, self.test_author = create_canned_project()
        self.test_user = return_canned_user("Test User", 11111111)
        self.test_user.create()
        self.user_session_token = generate_encoded_token(self.test_user.id)
        self.url = f"/api/v2/projects/{self.test_project.id}/tasks/actions/lock-for-validation/"

    def test_returns_401_if_user_not_authorized(self):
        """Test returns 401 if user not authorized."""
        # Act
        response = self.client.post(self.url)
        # Assert
        self.assertEqual(response.status_code, 401)

    def test_validation_lock_returns_400_if_invalid_json(self):
        """Test returns 400 if invalid json."""
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"taskIds": "abcd"},
        )
        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["SubCode"], "InvalidData")

    def test_validation_lock_returns_404_for_invalid_project_id(self):
        """Test returns 404 on request with invalid project id."""
        # Act
        response = self.client.post(
            "/api/v2/projects/999999/tasks/actions/lock-for-validation/",
            headers={"Authorization": self.user_session_token},
            json={"taskIds": [1, 2]},
        )
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["SubCode"], "NotFound")

    def test_validation_lock_returns_404_for_invalid_task_id(self):
        """Test returns 404 on request with invalid task id."""
        # Act
        response = self.client.post(
            f"/api/v2/projects/{self.test_project.id}/tasks/actions/lock-for-validation/",
            headers={"Authorization": self.user_session_token},
            json={"taskIds": [999999]},
        )
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["SubCode"], "NotFound")

    def test_validation_lock_returns_403_if_task_not_ready_for_validation(self):
        """Test returns 403 if task not ready for validation."""
        # Arrange
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.READY.value  # not ready for validation
        task.locked_by = self.test_user.id
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"taskIds": [1]},
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "NotReadyForValidation")

    def test_validation_lock_returns_403_if_mapped_by_same_user_and_user_not_admin(
        self,
    ):
        """Test returns 403 if mapped by same user."""
        # Arrange
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.MAPPED.value
        task.mapped_by = self.test_user.id
        task.update()
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"taskIds": [1]},
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "CannotValidateMappedTask")

    def test_validation_lock_returns_403_if_user_not_permitted_to_validate(self):
        """Test returns 403 if user not permitted to validate."""
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"taskIds": [1]},
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "ProjectNotPublished")

    def test_validation_lock_returns_409_if_user_hasnt_accepted_license(self):
        """Test returns 409 if user hasn't accepted license."""
        # Arrange
        self.test_project.license_id = create_canned_license()
        self.test_project.status = ProjectStatus.PUBLISHED.value
        self.test_project.save()
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.MAPPED.value
        task.mapped_by = self.test_author.id
        task.update()
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"taskIds": [1]},
        )
        # Assert
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json["SubCode"], "UserLicenseError")

    @patch.object(ProjectService, "is_user_permitted_to_validate")
    def test_validation_lock_returns_403_if_user_not_on_allowed_list(
        self, mock_validate_permitted
    ):
        """Test returns 403 if user not on allowed list."""
        # Arrange
        mock_validate_permitted.return_value = (
            False,
            ValidatingNotAllowed.USER_NOT_ON_ALLOWED_LIST,
        )
        task = Task.get(1, self.test_project.id)
        task.task_status = TaskStatus.MAPPED.value
        task.mapped_by = self.test_author.id
        task.update()
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"taskIds": [1]},
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "UserNotAllowed")

    def test_validation_lock_returns_403_if_user_has_already_locked_other_task(self):
        """Test returns 403 if user has already locked other task."""
        # Arrange
        self.test_project.status = ProjectStatus.PUBLISHED.value
        self.test_project.save()
        task = Task.get(2, self.test_project.id)
        task.task_status = TaskStatus.LOCKED_FOR_MAPPING.value
        task.locked_by = self.test_user.id
        task.update()
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"taskIds": [1]},
        )
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["SubCode"], "UserAlreadyHasTaskLocked")

    @patch.object(ProjectService, "is_user_permitted_to_validate")
    def validation_lock_returns_200_if_user_permitted_to_validate(
        self, mock_validate_permitted
    ):
        """Test returns 200 if user permitted to validate."""
        # Arrange
        mock_validate_permitted.return_value = (
            True,
            ValidatingNotAllowed.USER_NOT_ON_ALLOWED_LIST,
        )
        # Since task 1 is already mapped, we need to change the status of task 2 to invalidated
        # As ivalidated tasks should also be allowed to be locked for validation
        task = Task.get(2, self.test_project.id)
        task.task_status = TaskStatus.INVALIDATED.value
        task.update()

        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_session_token},
            json={"taskIds": [1, 2]},
        )
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["tasks"][0]["taskId"], 1)
        self.assertEqual(
            response.json["tasks"][0]["taskStatus"],
            TaskStatus.LOCKED_FOR_VALIDATION.name,
        )
        self.assertEqual(response.json["tasks"][1]["taskId"], 2)
        self.assertEqual(
            response.json["tasks"][1]["taskStatus"],
            TaskStatus.LOCKED_FOR_VALIDATION.name,
        )
