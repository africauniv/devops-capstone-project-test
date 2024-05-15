"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application
import datetime


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    # Uncomment once get_accounts has been implemented
    # location_url = url_for("get_accounts", account_id=account.id, _external=True)
    location_url = "/"  # Remove once get_accounts has been implemented
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )


######################################################################
# LIST ALL ACCOUNTS
######################################################################
@app.route("/accounts", methods=["GET"])
def read_accounts():
    """
    Retrieve all accounts
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    app.logger.info(f"{timestamp} GET Request to retrieve all Accounts")
    accounts = Account.all()
    if(accounts):
        accounts_json = [item.serialize() for item in accounts]
        return (
            jsonify(accounts_json), status.HTTP_200_OK,
        )
    else:
        return (jsonify({'error': 'accounts not found'}), status.HTTP_404_NOT_FOUND)


######################################################################
# READ AN ACCOUNT
######################################################################
@app.route("/accounts/<int:id>", methods=["GET"])
def read_account(id):
    """
    Retrieve an account by its ID.
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    app.logger.info(f"{timestamp} GET Request to retrieve an Account")
    account = Account.find(id)
    if(account):
        return (
            jsonify(account.serialize()), status.HTTP_200_OK,
        )
    else:
        return (jsonify({'error': 'account not found'}), status.HTTP_404_NOT_FOUND)


######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################
@app.route("/accounts/<int:id>", methods=["PUT"])
def update_account(id):
    """
    update an account by it ID.
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    app.logger.info(f"{timestamp} GET Request to update an Account")
    if not request.get_json():
        return (jsonify({'error': 'id not found'}), status.HTTP_405_METHOD_NOT_ALLOWED)

    ac = Account.find(id)
    if not ac:
        return (jsonify({'error': 'id not found'}), status.HTTP_404_NOT_FOUND)

    try:
        ac.deserialize(request.get_json())
    except Exception as e:
        return (jsonify({'error': 'attribute error', 'details': e}), status.HTTP_409_CONFLICT)

    ac.update()

    return (
        jsonify(ac.serialize()), status.HTTP_200_OK,
    )


######################################################################
# DELETE AN ACCOUNT
######################################################################
@app.route("/accounts/<int:id>", methods=["DELETE"])
def delete_account(id):
    """
    delete an account by it ID.
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    app.logger.info(f"{timestamp} GET Request to delete an Account")

    ac = Account.find(id)
    if not ac:
        return (jsonify({'error': 'id not found'}), status.HTTP_404_NOT_FOUND)

    ac.delete()

    return (
        {}, status.HTTP_204_NO_CONTENT
    )


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
