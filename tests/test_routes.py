"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
import json
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)


    ######################################################################
    #  A C C O U N T   T E S T   C A S E S S U P P L E M E N T S
    ######################################################################

    def test_read_account(self):
        """it should return an element by its id """
        ac = AccountFactory()
        ac.create()
        ac_result = Account.find_by_name(ac.name)[0]
        response = self.client.get(f"{BASE_URL}/{ac_result.id}")
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        ac_final = response.get_json()
        self.assertEqual(ac_final["name"],ac.serialize()["name"])
        self.assertEqual(ac_final["email"],ac.serialize()["email"])
        self.assertEqual(ac_final["address"],ac.serialize()["address"])
        self.assertEqual(ac_final["phone_number"],ac.serialize()["phone_number"])
    
    def test_read_not_found(self):
        """it should return an error not found type"""
        response = self.client.get(f"{BASE_URL}/20")
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)
        ac_final = response.get_json()
        self.assertEqual("account not found",ac_final["error"])

    def test_read_list_accounts(self):
        """it should return accounts list"""
        ac_initials = list()
        for _ in range(3):
            a = AccountFactory()
            a.create()
            ac_initials.append(a)
        response = self.client.get(BASE_URL)
        ac_finals = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(ac_initials), len(ac_finals))
        for i in range(3):
            result = any(ac_finals[i] == item.serialize()  for item in ac_initials)
            self.assertTrue(result)

    def test_read_list_not_found(self):
        """it should return an error not found type for list check"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)
        ac_final = response.get_json()
        self.assertEqual("accounts not found",ac_final["error"])

    def test_update_account(self):
        """it should change value and return 200_OK"""
        ac = AccountFactory()
        ac.create()
        ac_id = Account.find_by_name(ac.name)[0].id
        ac.name = "benjamin"
        ac.email = "benjamin@gmail.com"
        response = self.client.put(f"{BASE_URL}/{ac_id}", json=ac.serialize())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        #check the item from database and verify modifications
        ac_result = Account.find(ac_id)
        self.assertEqual("benjamin", ac_result.name)
        self.assertEqual("benjamin@gmail.com", ac_result.email)

    def test_update_fail(self):
        """it should try to change empty or unauthaurized attribut value Or either invalid id"""
        response = self.client.put(f"{BASE_URL}/0", json = {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        ac = AccountFactory()
        response = self.client.put(f"{BASE_URL}/22", json = json.dumps(ac.serialize()))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        ac = AccountFactory()
        ac.create()
        ac_id = Account.find_by_name(ac.name)[0].id
        json_fail = '{"city":"goda"}'
        response = self.client.put(f"{BASE_URL}/{ac_id}", json = json_fail)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_delete_account(self):
        """it should delete an account by id"""
        ac = AccountFactory()
        ac.create()
        ac_id = Account.find_by_name(ac.name)[0].id
        response = self.client.delete(f"{BASE_URL}/{ac_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        #check the item from database and verify empty result
        self.assertIsNone(Account.find(ac_id))
    
    def test_delete_fail(self):
        """it should try to delete by false id"""
        response = self.client.delete(f"{BASE_URL}/22")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)