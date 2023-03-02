from unittest.mock import patch

from tests.backend.base import BaseTestCase
from tests.backend.helpers.test_helpers import (
    return_canned_user,
    generate_encoded_token,
    create_canned_interest,
)
from backend.services.messaging.smtp_service import SMTPService

TEST_EMAIL = "test@test.com"


class TestUsersActionsSetUsersAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_user = return_canned_user()
        self.test_user.create()
        self.url = "/api/v2/users/me/actions/set-user/"
        self.user_seesion_token = generate_encoded_token(self.test_user.id)

    def test_returns_401_if_no_token(self):
        """ Test that the API returns 401 if no token is provided """
        # Act
        response = self.client.patch(self.url)
        # Assert
        self.assertEqual(response.status_code, 401)

    def test_returns_401_if_other_user_requested(self):
        """ Test that the API returns 401 if another user is requested """
        # Act
        response = self.client.patch(
            self.url,
            headers={"Authorization": self.user_seesion_token},
            json={"id": 2},
        )
        # Assert
        self.assertEqual(response.status_code, 401)

    def test_returns_400_if_invalid_data(self):
        """ Test that the API returns 400 if invalid data is provided """
        # Act
        response = self.client.patch(
            self.url,
            headers={"Authorization": self.user_seesion_token},
            json={"id": self.test_user.id, "emailAddress": "invalid_email"},
        )
        # Assert
        self.assertEqual(response.status_code, 400)

    def test_returns_404_if_user_not_found(self):
        """ Test that the API returns 404 if user is not found """
        # Act
        response = self.client.patch(
            self.url,
            headers={"Authorization": generate_encoded_token(999)},
            json={"id": 999},
        )
        # Assert
        self.assertEqual(response.status_code, 404)

    def test_returns_200_if_user_updated(self):
        """ Test that the API returns 200 if user is updated """
        # Arrange
        sample_payload = {
            "id": self.test_user.id,
            "name": "ThinkWhere",
            "city": "test_city",
            "country": "AD",
            "twitterId": "test_twitter",
            "facebookId": "test_facebook",
            "linkedinId": "test_linkedin",
            "slackId": "test_slack",
            "gender": "MALE",
            "selfDescriptionGender": None,
        }
        # Act
        response = self.client.patch(
            self.url,
            headers={"Authorization": self.user_seesion_token},
            json=sample_payload,
        )
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["verificationEmailSent"], False)
        self.assertEqual(self.test_user.name, sample_payload["name"])
        self.assertEqual(self.test_user.city, sample_payload["city"])
        self.assertEqual(self.test_user.country, sample_payload["country"])
        self.assertEqual(self.test_user.twitter_id, sample_payload["twitterId"])
        self.assertEqual(self.test_user.facebook_id, sample_payload["facebookId"])
        self.assertEqual(self.test_user.linkedin_id, sample_payload["linkedinId"])
        self.assertEqual(self.test_user.slack_id, sample_payload["slackId"])

    @patch.object(SMTPService, "send_verification_email")
    def test_returns_200_if_user_updated_with_email(self, mock_send_verification_email):
        """ Test that the API returns 200 if user is updated """
        # Arrange
        mock_send_verification_email.return_value = True
        # Act
        response = self.client.patch(
            self.url,
            headers={"Authorization": self.user_seesion_token},
            json={"id": self.test_user.id, "emailAddress": TEST_EMAIL},
        )
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["verificationEmailSent"], True)


class TestUsersActionsRegisterEmailAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = "/api/v2/users/actions/register/"

    def test_returns_400_if_no_data(self):
        """ Test that the API returns 400 if no data is provided """
        # Act
        response = self.client.post(self.url)
        # Assert
        self.assertEqual(response.status_code, 400)

    def test_returns_200_if_email_registered(self):
        """ Test that the API returns 200 if email is registered """
        # Arrange
        sample_payload = {"email": TEST_EMAIL}
        # Act
        response = self.client.post(self.url, json=sample_payload)
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["email"], TEST_EMAIL)
        self.assertEqual(response.json["success"], True)


class TestUsersActionsSetInterestsAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_user = return_canned_user()
        self.test_user.create()
        self.url = "/api/v2/users/me/actions/set-interests/"
        self.user_seesion_token = generate_encoded_token(self.test_user.id)

    def test_returns_401_if_no_token(self):
        """ Test that the API returns 401 if no token is provided """
        # Act
        response = self.client.post(self.url)
        # Assert
        self.assertEqual(response.status_code, 401)

    def test_404_if_interests_not_found(self):
        """ Test that the API returns 404 if interests are not found """
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_seesion_token},
            json={"interests": [999]},
        )
        # Assert
        self.assertEqual(response.status_code, 404)

    def test_returns_400_if_invalid_data(self):
        """ Test that the API returns 400 if invalid data is provided """
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_seesion_token},
            json={"key": "invalid"},
        )
        # Assert
        self.assertEqual(response.status_code, 400)

    def test_returns_200_if_interests_set(self):
        """ Test that the API returns 200 if interests are set """
        # Arrange
        interest_1 = create_canned_interest("test_interest_1")
        interest_2 = create_canned_interest("test_interest_2")
        sample_payload = {"interests": [interest_1.id, interest_2.id]}
        # Act
        response = self.client.post(
            self.url,
            headers={"Authorization": self.user_seesion_token},
            json=sample_payload,
        )
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["interests"]), 2)
        self.assertEqual(response.json["interests"][0]["id"], interest_1.id)
        self.assertEqual(response.json["interests"][1]["id"], interest_2.id)
